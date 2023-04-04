from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ImageSendMessage,
    AudioMessage,
    JoinEvent,
    FileMessage,
)
import os
import uuid
import noisereduce as nr
import pydub
from scipy.io import wavfile

from src.models import OpenAIModel
from src.memory import Memory
from src.logger import logger
from src.utils import get_role_and_content
from src.service.youtube import Youtube, YoutubeTranscriptReader
from src.service.website import Website, WebsiteReader
from src.mongodb import mongodb
from src.event_middleware import event_middleware

load_dotenv(".env")

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
youtube = Youtube(step=4)
website = Website()
mongodb.connect_to_database()


memory = Memory(mongodb)


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
                msg = TextSendMessage(text="Token 無效，請重新註冊，格式為 /註冊 sk-xxxxx")
            except KeyError:
                msg = TextSendMessage(text="請先註冊 Token，格式為 /註冊 sk-xxxxx")
            except Exception as e:
                memory.clean_storage(user_id)
                if str(e).startswith("Incorrect API key provided"):
                    msg = TextSendMessage(text="OpenAI API Token 有誤，請重新註冊。")
                elif str(e).startswith(
                    "That model is currently overloaded with other requests."
                ):
                    msg = TextSendMessage(text="已超過負荷，請稍後再試")
                else:
                    msg = TextSendMessage(text=str(e))
        line_bot_api.reply_message(reply_token, msg)


def process_audio_message(user_id, message):
    model = OpenAIModel(api_key=memory.get_api_key(user_id))
    audio_content = line_bot_api.get_message_content(message.id)
    input_audio_path = f"{str(uuid.uuid4())}.m4a"
    with open(input_audio_path, "wb") as fd:
        for chunk in audio_content.iter_content():
            fd.write(chunk)

    # perform noise reduction
    wav_file = pydub.AudioSegment.from_file(input_audio_path)
    wav_path = f"{str(uuid.uuid4())}.wav"
    # Convert to WAV format
    wav_file.export(wav_path, format="wav")
    rate, data = wavfile.read(wav_path)
    reduced_noise = nr.reduce_noise(y=data, sr=rate, stationary=True)
    wavfile.write(wav_path, rate, reduced_noise)

    is_successful, response, error_message = model.audio_transcriptions(
        wav_path, "whisper-1"
    )
    if not is_successful:
        raise Exception(error_message)
    speech_to_text_content = response["text"]
    text_split = speech_to_text_content.split()
    shortcut_keyword = text_split[0].lower().replace(",", "").replace(".", "")
    shortcut_keywords = memory.get_shortcut_keywords(user_id)
    if shortcut_keyword in shortcut_keywords:
        speech_to_text_content = (
            shortcut_keywords[shortcut_keyword] + "\n" + " ".join(text_split[1:])
        )
    memory.append_storage(user_id, "user", speech_to_text_content)
    is_successful, response, error_message = model.chat_completions(
        memory.get_storage(user_id), "gpt-3.5-turbo"
    )
    if not is_successful:
        raise Exception(error_message)
    role, response = get_role_and_content(response)
    memory.append_storage(user_id, role, response)
    msg = TextSendMessage(
        text=f"you:\n{speech_to_text_content}\n===\nresponse:\n{response}"
    )
    os.remove(input_audio_path)
    os.remove(wav_path)
    return msg


def process_text_message(user_id, message):
    text = message.text.strip()
    logger.info(f"{user_id}: {text}")
    model = OpenAIModel(api_key=memory.get_api_key(user_id))
    if text.startswith("/註冊"):
        api_key = text[3:].strip()
        memory.add_api_key(user_id, api_key)
        model = OpenAIModel(api_key=memory.get_api_key(user_id))
        is_successful, _, _ = model.check_token_valid()
        if not is_successful:
            raise PermissionError("Invalid API token")
        msg = TextSendMessage(text="Token 有效，註冊成功")

    elif text.startswith("/目前金鑰"):
        api_key = memory.get_api_key(user_id)
        if api_key:
            msg = TextSendMessage(text=f"目前使用 Token {api_key}")
        else:
            msg = TextSendMessage(text="尚未註冊")

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
        )

    elif text.startswith("/系統訊息"):
        memory.change_system_message(user_id, text[5:].strip())
        msg = TextSendMessage(text="輸入成功")

    elif text.startswith("/目前系統訊息"):
        system_message = memory.get_system_message(user_id)
        msg = TextMessage(text=f"目前系統訊息：{system_message}")

    elif text.startswith("/清除"):
        memory.clean_storage(user_id)
        msg = TextSendMessage(text="歷史訊息清除成功")

    elif text.startswith("/get_keyword"):
        shortcut_keywords = memory.get_shortcut_keywords(user_id)
        msg = TextSendMessage(text=f"目前快捷關鍵字：{dict(shortcut_keywords)}")

    elif text.startswith("/add_keyword"):
        shortcut_pairs = text[12:].strip().split()
        if len(shortcut_pairs) < 2:
            msg = "請輸入 /add_keyword key value"
        else:
            shortcut_keywords = memory.get_shortcut_keywords(user_id)
            shortcut_keyword = shortcut_pairs[0].lower()
            shortcut_value = " ".join(shortcut_pairs[1:])

            shortcut_keywords[shortcut_keyword] = shortcut_value
            memory.change_shortcut_keywords(user_id, shortcut_keywords)
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
            memory.change_shortcut_keywords(user_id, shortcut_keywords)
            msg = TextSendMessage(text=f'刪除快捷關鍵字 "{shortcut_keyword}" 成功')
        else:
            msg = TextSendMessage(text=f'快捷關鍵字 "{shortcut_keyword}" 不存在')

    elif text.startswith("/圖像"):
        prompt = text[3:].strip()
        memory.append_storage(user_id, "user", prompt)
        is_successful, response, error_message = model.image_generations(prompt)
        if not is_successful:
            raise Exception(error_message)
        url = response["data"][0]["url"]
        msg = ImageSendMessage(original_content_url=url, preview_image_url=url)
        memory.append_storage(user_id, "assistant", url)

    else:
        if text.startswith(f"!"):
            text_split = text.split()
            shortcut_keyword = text_split[0][1:].lower()
            if shortcut_keyword in memory.shortcut_keywords[user_id]:
                text = (
                    memory.shortcut_keywords[user_id][shortcut_keyword]
                    + " "
                    + " ".join(text_split[1:])
                )
        memory.append_storage(user_id, "user", text)
        url = website.get_url_from_text(text)
        if url:
            if youtube.retrieve_video_id(text):
                (
                    is_successful,
                    chunks,
                    error_message,
                ) = youtube.get_transcript_chunks(youtube.retrieve_video_id(text))
                if not is_successful:
                    raise Exception(error_message)
                youtube_transcript_reader = YoutubeTranscriptReader(
                    model, os.getenv("OPENAI_MODEL_ENGINE")
                )
                (
                    is_successful,
                    response,
                    error_message,
                ) = youtube_transcript_reader.summarize(chunks)
                if not is_successful:
                    raise Exception(error_message)
                role, response = get_role_and_content(response)
                msg = TextSendMessage(text=response)
            else:
                chunks = website.get_content_from_url(url)
                if len(chunks) == 0:
                    raise Exception("無法撈取此網站文字")
                website_reader = WebsiteReader(model, os.getenv("OPENAI_MODEL_ENGINE"))
                is_successful, response, error_message = website_reader.summarize(
                    chunks
                )
                if not is_successful:
                    raise Exception(error_message)
                role, response = get_role_and_content(response)
                msg = TextSendMessage(text=response)
        else:
            is_successful, response, error_message = model.chat_completions(
                memory.get_storage(user_id), os.getenv("OPENAI_MODEL_ENGINE")
            )
            if not is_successful:
                raise Exception(error_message)
            role, response = get_role_and_content(response)
            msg = TextSendMessage(text=response)
        memory.append_storage(user_id, role, response)
    return msg


def process_file_message(user_id, message):
    audio_types = (".mp4", ".mpeg", ".mp3", ".wav", ".m4a", ".wma")
    file_name = message.file_name
    file_size = message.file_size
    if os.path.splitext(file_name)[-1] in audio_types:
        msg = process_audio_message(user_id, message)
    elif file_size > 25000000:  # lager than 25MB
        msg = TextSendMessage(text="檔案太大，目前僅支援 25MB 以下的檔案")
    else:
        msg = TextSendMessage(text=f"目前僅支援 {audio_types} 檔案")
    return msg


textHandler = MessageEventHandler(process_message=process_text_message)
audioHandler = MessageEventHandler(process_message=process_audio_message)
fileHandler = MessageEventHandler(process_message=process_file_message)


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


@handler.add(MessageEvent, message=FileMessage)
@event_middleware
def handle_file_message(reply_token, user_id, message):
    fileHandler.handle_message(reply_token, user_id, message)


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
