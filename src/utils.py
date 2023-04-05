import os
import opencc
import requests

s2t_converter = opencc.OpenCC("s2t")
t2s_converter = opencc.OpenCC("t2s")


def get_role_and_content(response: str):
    role = response["choices"][0]["message"]["role"]
    content = response["choices"][0]["message"]["content"].strip()
    content = s2t_converter.convert(content)
    return role, content


def verify_file_preparation_status(messageId):
    """
    Check if the file is ready to be downloaded.
    https://developers.line.biz/en/reference/messaging-api/#verify-video-or-audio-preparation-status
    """
    url = f"https://api-data.line.me/v2/bot/message/{messageId}/content/transcoding"
    headers = {"Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    if r.status_code != 200 or r.json()["status"] == "failed":
        raise Exception(f"File preparation failed. {r.json()}")
    status = r.json()["status"]
    return True if status == "succeeded" else False
