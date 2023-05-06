import json
from linebot.models import TextSendMessage, FlexSendMessage
from main import OpenAI, openai_model, ElevenLabs, el_model
from src.flex import help


def register_openai(user_id, text):
    api_key = text[9:].strip()
    openai_model.add_api_key(user_id, api_key)
    model = OpenAI(api_key=openai_model.get_api_key(user_id))
    is_successful, _, _ = model.check_token_valid()
    if not is_successful:
        raise PermissionError("Invalid API token")
    msg = TextSendMessage(text="Token 有效，註冊成功")
    return msg


def register_elevenlabs(user_id, text):
    api_key = text[13:].strip()
    el_model.add_api_key(user_id, api_key)
    el_api = ElevenLabs(api_key=el_model.get_api_key(user_id))
    el_api.voice_list()
    msg = TextSendMessage(text="Token 有效，註冊成功")
    return msg


def switch_text_to_speech(user_id, text):
    enable_text_to_speech = el_model.get_tts(user_id)
    if enable_text_to_speech:
        el_model.disable_tts(user_id)
        msg = TextSendMessage(text="文字轉語音已關閉")
    else:
        el_model.enable_tts(user_id)
        msg = TextSendMessage(text="文字轉語音已開啟")
    return msg


def get_token(user_id, text):
    text = ""
    api_key = openai_model.get_api_key(user_id)
    if api_key:
        text += f"目前使用的 OpenAI Token:\n{api_key}\n"
    else:
        text += "尚未註冊 OpenAI Token\n"

    api_key = el_model.get_api_key(user_id)
    if api_key:
        text += f"目前使用的 ElevenLabs Token:\n{api_key}\n"
    else:
        text += "尚未註冊 ElevenLabs Token\n"
    msg = TextSendMessage(text=text)
    return msg


def get_message_count(user_id, text):
    memory_message_count = openai_model.get_memory_message_count(user_id)
    msg = TextSendMessage(text=f"目前會記憶前 {memory_message_count} 則訊息")
    return msg


def set_message_count(user_id, text):
    memory_message_count = int(text[7:].strip())
    openai_model.change_memory_message_count(user_id, memory_message_count)
    msg = TextSendMessage(text=f"設定成功，目前會記憶前 {memory_message_count} 則訊息")
    return msg


def get_message(user_id, text):
    memory_message = openai_model.get_storage(user_id)
    msg = TextSendMessage(text=f"目前記憶訊息：{memory_message}")
    return msg


def set_system_message(user_id, text):
    system_message = text[7:].strip()
    openai_model.change_system_message(user_id, system_message)
    msg = TextSendMessage(text=f"系統訊息已設定為：{system_message}")
    return msg


def get_system_message(user_id, text):
    system_message = openai_model.get_system_message(user_id)
    msg = TextSendMessage(text=f"目前系統訊息：{system_message}")
    return msg


def clean_chat_history(user_id, text):
    openai_model.clean_storage(user_id)
    msg = TextSendMessage(text="歷史訊息清除成功")
    return msg


def get_shortcut_keyword(user_id, text):
    shortcut_keywords = openai_model.get_shortcut_keywords(user_id)
    msg = TextSendMessage(text=f"目前快捷關鍵字：{dict(shortcut_keywords)}")
    return msg


def add_shortcut_keyword(user_id, text):
    shortcut_pairs = text[6:].strip().split()
    if len(shortcut_pairs) < 2:
        msg = "請輸入 /新增關鍵字 key value"
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
    return msg


def delete_shortcut_keyword(user_id, text):
    shortcut_keyword = text[16:].strip().lower()
    shortcut_keywords = openai_model.get_shortcut_keywords(user_id)
    if shortcut_keyword in shortcut_keywords:
        shortcut_keywords.pop(shortcut_keyword)
        openai_model.change_shortcut_keywords(user_id, shortcut_keywords)
        msg = TextSendMessage(text=f'刪除快捷關鍵字 "{shortcut_keyword}" 成功')
    else:
        msg = TextSendMessage(text=f'快捷關鍵字 "{shortcut_keyword}" 不存在')
    return msg


def clean_all_shortcut_keyword(user_id, text):
    openai_model.change_shortcut_keywords(user_id, {})
    msg = TextSendMessage(text=f"已刪除所有快捷關鍵字")
    return msg


def get_voice(user_id, text):
    voice = el_model.get_voice(user_id)
    el_api = ElevenLabs(api_key=el_model.get_api_key(user_id))
    voice_list = el_api.voice_list()
    text = f"目前語音：{voice}\n如果要更換語音，請輸入\n/設定語音 語音\n{voice_list}（從中選擇一個語音）"
    msg = TextSendMessage(text=text)
    return msg


def set_voice(user_id, text):
    voice = text[5:].strip()
    el_api = ElevenLabs(api_key=el_model.get_api_key(user_id))
    voice_list = el_api.voice_list()
    if voice not in voice_list:
        msg = TextSendMessage(text=f"語音 {voice} 不存在，請輸入以下其中一個語音：\n{voice_list}")
        return msg
    el_model.change_voice(user_id, voice)
    msg = TextSendMessage(text=f"語音已設定為：{voice}")
    return msg


def commands(user_id, text):
    text = "指令："
    for k, v in menu.items():
        if k == "/所有指令說明" or k == "/help":
            continue
        text += f"\n{v['description']}\n"
    msg = TextSendMessage(text=text)
    return msg


def flex_help(user_id, text):
    flex = help()
    msg = FlexSendMessage(alt_text="快捷指令", contents=flex)
    return msg


menu = {}

menu["/註冊OpenAI"] = {
    "function": register_openai,
    "description": "/註冊OpenAI + API Token\n👉 API Token 請先到 https://platform.openai.com/ 註冊登入後取得",
}

menu["/註冊ElevenLabs"] = {
    "function": register_elevenlabs,
    "description": "/註冊ElevenLabs + API Token\n👉 API Token 請先到 https://beta.elevenlabs.io/ 註冊登入後取得",
}

menu["/文字轉語音"] = {
    "function": switch_text_to_speech,
    "description": "/文字轉語音\n👉 開啟或關閉文字轉語音",
}

menu["/目前使用金鑰"] = {"function": get_token, "description": "/目前使用金鑰\n👉 查看目前使用的 API Token"}

menu["/目前記憶聊天筆數"] = {
    "function": get_message_count,
    "description": "/目前記憶聊天筆數\n👉 查看目前記憶聊天筆數",
}

menu["/設定記憶數量"] = {
    "function": set_message_count,
    "description": "/設定記憶數量 + 數字\n👉 設定記憶數量",
}

menu["/目前聊天紀錄"] = {"function": get_message, "description": "/目前聊天紀錄\n👉 查看目前聊天紀錄"}

menu["/設定系統訊息"] = {
    "function": set_system_message,
    "description": "/設定系統訊息 + Prompt\n👉 Prompt 可以命令機器人扮演某個角色，例如：請你扮演擅長做總結的人",
}

menu["/目前系統訊息"] = {"function": get_system_message, "description": "/目前系統訊息\n👉 查看目前系統訊息"}

menu["/清除所有聊天記錄"] = {
    "function": clean_chat_history,
    "description": "/清除所有聊天記錄\n👉 清除所有聊天記錄",
}

menu["/目前快捷關鍵字"] = {
    "function": get_shortcut_keyword,
    "description": "/目前快捷關鍵字\n👉 查看目前快捷關鍵字",
}

menu["/新增關鍵字"] = {
    "function": add_shortcut_keyword,
    "description": "/新增關鍵字 key value\n👉 新增快捷關鍵字，使用方法 !key 輸入內容",
}

menu["/刪除關鍵字"] = {
    "function": delete_shortcut_keyword,
    "description": "/刪除關鍵字 key\n👉 刪除快捷關鍵字",
}

menu["/清除所有快捷關鍵字"] = {
    "function": clean_all_shortcut_keyword,
    "description": "/清除所有快捷關鍵字\n👉 清除所有快捷關鍵字",
}

menu["/目前語音"] = {"function": get_voice, "description": "/目前語音\n👉 查看目前語音"}

menu["/設定語音"] = {"function": set_voice, "description": "/設定語音 + 語音名稱\n👉 設定語音"}

menu["/所有指令說明"] = menu["/help"] = {"function": commands, "description": "查看所有指令說明"}

menu["H"] = {"function": flex_help, "description": "H\n👉指令介面"}
