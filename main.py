from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    AudioSendMessage,
    AudioMessage,
    JoinEvent,
)
import os
import uuid
import time

from src.api import OpenAI, ElevenLabs
from src.model import OpenAIModel, ElevenLabsModel
from src.logger import logger
from src.utils import get_role_and_content, reduce_audio_noise
from src.mongodb import mongodb
from src.event_middleware import event_middleware
from src.readme import README

load_dotenv(".env")

app = Flask(
    __name__, static_url_path="/files", static_folder=os.getenv("STATIC_FOLDER")
)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
mongodb.connect_to_database()


openai_model = OpenAIModel(mongodb)
el_model = ElevenLabsModel(mongodb)


class MessageEventHandler:
    def __init__(self, process_message):
        self.process_message = process_message

    def handle_message(self, reply_token, user_id, message):
        if user_id is None:
            msg = TextMessage(text=message)
        else:
            try:
                msg = self.process_message(user_id, message)
            except PermissionError:
                msg = TextSendMessage(text="Token 無效，請重新註冊，格式為 /註冊OpenAI sk-xxxxx")
            except Exception as e:
                openai_model.clean_storage(user_id)
                if str(e).startswith("Incorrect API key provided"):
                    msg = TextSendMessage(text="OpenAI API Token 有誤，請重新註冊。")
                elif str(e).startswith(
                    "That model is currently overloaded with other requests."
                ):
                    msg = TextSendMessage(text="已超過負荷，請稍後再試")
                else:
                    msg = TextSendMessage(text=str(e))
        line_bot_api.reply_message(reply_token, msg)


def process_audio_message(user_id, message, ext=".m4a"):
    openai_api = OpenAI(api_key=openai_model.get_api_key(user_id))

    input_audio_path = f"{str(uuid.uuid4())}{ext}"

    retry = 0
    # retry if file is not ready
    while (
        not (
            os.path.exists(input_audio_path) and os.path.getsize(input_audio_path) != 0
        )
        and retry < 5
    ):
        audio_content = line_bot_api.get_message_content(message.id)
        with open(input_audio_path, "wb") as fd:
            for chunk in audio_content.iter_content():
                fd.write(chunk)
        time.sleep(3)
        retry += 1
    if os.path.getsize(input_audio_path) == 0:
        raise RuntimeError(
            "File preparation failed. Please reduce the file size and try again."
        )

    wav_path = reduce_audio_noise(input_audio_path)
    is_successful, response, error_message = openai_api.audio_transcriptions(
        wav_path, "whisper-1"
    )
    if not is_successful:
        raise Exception(error_message)
    speech_to_text_content = response["text"]

    text_split = speech_to_text_content.split()
    shortcut_keyword = text_split[0].lower().replace(",", "").replace(".", "")
    shortcut_keywords = openai_model.get_shortcut_keywords(user_id)
    if shortcut_keyword in shortcut_keywords:
        speech_to_text_content = (
            shortcut_keywords[shortcut_keyword] + "\n" + " ".join(text_split[1:])
        )

    openai_model.append_storage(user_id, "user", speech_to_text_content)
    is_successful, response, error_message = openai_api.chat_completions(
        openai_model.get_storage(user_id), "gpt-3.5-turbo"
    )
    if not is_successful:
        raise Exception(error_message)
    role, response = get_role_and_content(response)
    openai_model.append_storage(user_id, role, response)
    msg = [TextSendMessage(text=f"you:\n{speech_to_text_content}")]
    msg.append(TextSendMessage(text=f"response:\n{response}"))
    os.remove(input_audio_path)
    os.remove(wav_path)

    if el_model.get_tts(user_id):
        el_api = ElevenLabs(api_key=el_model.get_api_key(user_id))
        response = el_api.generate(
            response, "Adam", f"{os.getenv('STATIC_FOLDER')}/{str(uuid.uuid4())}.mp3"
        )
        msg.append(
            AudioSendMessage(
                original_content_url=f"https://{os.getenv('DOMAIN_NAME')}/files/{response['filename']}",
                duration=response["duration"],
            )
        )
    return msg


def process_text_message(user_id, message):
    from src.menu import menu

    text = message.text.strip()
    logger.info(f"{user_id}: {text}")
    if text == "/首次使用":
        msg = TextSendMessage(text=README)
    elif text == "H":
        msg = menu["H"]["function"](user_id, text)
    elif text.startswith("/") and text.split()[0] not in menu:
        msg = TextSendMessage(text="指令錯誤，請輸入 /help 查看指令")
    elif text.startswith("/"):
        text_split = text.split()
        if len(text_split) == 2 and text_split[1] == "help":
            msg = TextSendMessage(menu[text.split()[0]]["description"])
        else:
            msg = menu[text.split()[0]]["function"](user_id, text)
    else:
        if text.startswith(f"!"):
            text_split = text.split()
            shortcut_keyword = text_split[0][1:].lower()
            if shortcut_keyword in openai_model.shortcut_keywords[user_id]:
                text = (
                    openai_model.shortcut_keywords[user_id][shortcut_keyword]
                    + " "
                    + " ".join(text_split[1:])
                )
        openai_model.append_storage(user_id, "user", text)
        model = OpenAI(api_key=openai_model.get_api_key(user_id))
        is_successful, response, error_message = model.chat_completions(
            openai_model.get_storage(user_id), os.getenv("OPENAI_MODEL_ENGINE")
        )
        if not is_successful:
            raise Exception(error_message)
        role, response = get_role_and_content(response)
        msg = [TextSendMessage(text=response)]
        openai_model.append_storage(user_id, role, response)

        if el_model.get_tts(user_id):
            el_api = ElevenLabs(api_key=el_model.get_api_key(user_id))
            response = el_api.generate(
                response,
                "Adam",
                f"{os.getenv('STATIC_FOLDER')}/{str(uuid.uuid4())}.mp3",
            )
            msg.append(
                AudioSendMessage(
                    original_content_url=f"https://{os.getenv('DOMAIN_NAME')}/files/{response['filename']}",
                    duration=response["duration"],
                )
            )
    return msg


textHandler = MessageEventHandler(process_message=process_text_message)
audioHandler = MessageEventHandler(process_message=process_audio_message)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
@event_middleware
def handle_text_message(reply_token, user_id, message):
    textHandler.handle_message(reply_token, user_id, message)


@handler.add(MessageEvent, message=AudioMessage)
@event_middleware
def handle_audio_message(reply_token, user_id, message):
    audioHandler.handle_message(reply_token, user_id, message)


@handler.add(JoinEvent)
@event_middleware
def handle_join_event(reply_token):
    text = (
        "歡迎使用，請註冊你的 API key\n，輸入 H 會跳出操作介面\n"
        + "\n注意！如果群組有其他人，會共用同一個 OpenAI key，意味著所有在此群組的發言都會產生費用，此費用為註冊金鑰者需要支付！"
    )
    msg = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, msg)


@app.route("/", methods=["GET"])
def home():
    return "Hello World"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
