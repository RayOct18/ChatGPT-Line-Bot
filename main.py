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
        response = el_api.generate(response, "Adam", f"static/{str(uuid.uuid4())}.mp3")
        msg.append(
            AudioSendMessage(
                original_content_url=f"https://{os.getenv('DOMAIN_NAME')}/files/{response['filename']}",
                duration=response["duration"],
            )
        )
    return msg


def process_text_message(user_id, message):
    text = message.text.strip()
    logger.info(f"{user_id}: {text}")
    if text.startswith("/註冊OpenAI"):
        api_key = text[9:].strip()
        openai_model.add_api_key(user_id, api_key)
        model = OpenAI(api_key=openai_model.get_api_key(user_id))
        is_successful, _, _ = model.check_token_valid()
        if not is_successful:
            raise PermissionError("Invalid API token")
        msg = TextSendMessage(text="Token 有效，註冊成功")

    elif text.startswith("/註冊ElevenLabs"):
        api_key = text[13:].strip()
        el_model.add_api_key(user_id, api_key)
        el_api = ElevenLabs(api_key=el_model.get_api_key(user_id))
        el_api.voice_list()
        msg = TextSendMessage(text="Token 有效，註冊成功")

    elif text.startswith("/文字轉語音"):
        enable_text_to_speech = el_model.get_tts(user_id)
        if enable_text_to_speech:
            el_model.disable_tts(user_id)
            msg = TextSendMessage(text="文字轉語音已關閉")
        else:
            el_model.enable_tts(user_id)
            msg = TextSendMessage(text="文字轉語音已開啟")

    elif text.startswith("/目前金鑰"):
        api_key = openai_model.get_api_key(user_id)
        if api_key:
            msg = TextSendMessage(text=f"目前使用 Token {api_key}")
        else:
            msg = TextSendMessage(text="尚未註冊")

    elif text.startswith("/目前記憶數量"):
        memory_message_count = openai_model.get_memory_message_count(user_id)
        msg = TextSendMessage(text=f"目前會記憶前 {memory_message_count} 則訊息")

    elif text.startswith("/設定記憶數量"):
        count = int(text.strip().split()[-1])
        openai_model.change_memory_message_count(user_id, count)
        msg = TextSendMessage(text=f"設定成功，目前會記憶前 {count} 則訊息")

    elif text.startswith("/指令說明") or text.startswith("/help"):
        msg = TextSendMessage(
            text="指令：\n/註冊 + API Token\n👉 API Token 請先到 https://platform.openai.com/ 註冊登入後取得\n"
            + "\n/目前金鑰\n👉 顯示目前註冊的 API Token\n"
            + "\n/系統訊息 + Prompt\n👉 Prompt 可以命令機器人扮演某個角色，例如：請你扮演擅長做總結的人\n"
            + "\n/目前系統訊息 \n👉 顯示目前機器人扮演的角色\n"
            + "\n/清除\n👉 當前每一次都會紀錄最後兩筆歷史紀錄，這個指令能夠清除歷史訊息\n"
            + "\n/圖像 + Prompt\n👉 會調用 DALL∙E 2 Model，以文字生成圖像\n"
            + "\n語音輸入\n👉 會調用 Whisper 模型，先將語音轉換成文字，再調用 ChatGPT 以文字回覆\n"
            + "\n其他文字輸入\n👉 調用 ChatGPT 以文字回覆\n"
            + "\n/get_keyword\n👉 取得所有快捷關鍵字內容\n"
            + "\n/add_keyword + key content\n👉 新增快捷關鍵字內容，之後內容開頭如果是關鍵字，則自動帶入對應的內容\n"
            + "\n/remove_keyword + key\n👉 刪除快捷關鍵字\n"
            + "\n/目前記憶數量\n👉 顯示目前會記憶前幾則訊息\n"
            + "\n/設定記憶數量 + 數字\n👉 設定目前會記憶前幾則訊息\n"
        )

    elif text.startswith("/系統訊息"):
        openai_model.change_system_message(user_id, text[5:].strip())
        msg = TextSendMessage(text="輸入成功")

    elif text.startswith("/目前系統訊息"):
        system_message = openai_model.get_system_message(user_id)
        msg = TextMessage(text=f"目前系統訊息：{system_message}")

    elif text.startswith("/清除"):
        openai_model.clean_storage(user_id)
        msg = TextSendMessage(text="歷史訊息清除成功")

    elif text.startswith("/get_keyword"):
        shortcut_keywords = openai_model.get_shortcut_keywords(user_id)
        msg = TextSendMessage(text=f"目前快捷關鍵字：{dict(shortcut_keywords)}")

    elif text.startswith("/add_keyword"):
        shortcut_pairs = text[12:].strip().split()
        if len(shortcut_pairs) < 2:
            msg = "請輸入 /add_keyword key value"
        else:
            shortcut_keywords = openai_model.get_shortcut_keywords(user_id)
            shortcut_keyword = shortcut_pairs[0].lower()
            shortcut_value = " ".join(shortcut_pairs[1:])

            shortcut_keywords[shortcut_keyword] = shortcut_value
            openai_model.change_shortcut_keywords(user_id, shortcut_keywords)
            msg = TextSendMessage(
                text=f'新增快捷關鍵字 "{shortcut_keyword}": "{shortcut_value}" 成功，'
                + f'之後輸入文字 "!{shortcut_keyword}" 就會自動帶入 "{shortcut_value}"，'
                + "如果是使用語音輸入，則在開頭說出關鍵字"
            )

    elif text.startswith("/remove_keyword"):
        shortcut_keyword = text[16:].strip().lower()
        shortcut_keywords = mongodb.find_one(user_id, "shortcut_keywords") or {}
        if shortcut_keyword in shortcut_keywords:
            shortcut_keywords.pop(shortcut_keyword)
            openai_model.change_shortcut_keywords(user_id, shortcut_keywords)
            msg = TextSendMessage(text=f'刪除快捷關鍵字 "{shortcut_keyword}" 成功')
        else:
            msg = TextSendMessage(text=f'快捷關鍵字 "{shortcut_keyword}" 不存在')

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
                response, "Adam", f"static/{str(uuid.uuid4())}.mp3"
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
        "歡迎使用，請輸入 \n/註冊 [OpenAI API key]，來註冊你的 API key\n或輸入 /help 來查看其他指令\n"
        + "\n注意！如果群組有其他人，會共用同一個 OpenAI key，意味著所有在此群組的發言都會產生費用，此費用為註冊金鑰者需要支付！"
    )
    msg = TextSendMessage(text=text)
    line_bot_api.reply_message(reply_token, msg)


@app.route("/", methods=["GET"])
def home():
    return "Hello World"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
