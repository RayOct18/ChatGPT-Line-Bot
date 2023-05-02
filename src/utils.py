import os
import opencc
import pydub
import noisereduce as nr
from scipy.io import wavfile

s2t_converter = opencc.OpenCC("s2t")
t2s_converter = opencc.OpenCC("t2s")


def get_role_and_content(response: str):
    role = response["choices"][0]["message"]["role"]
    content = response["choices"][0]["message"]["content"].strip()
    content = s2t_converter.convert(content)
    return role, content


def reduce_audio_noise(input_audio_path: str):
    # perform noise reduction
    wav_file = pydub.AudioSegment.from_file_using_temporary_files(input_audio_path)
    filename = os.path.splitext(input_audio_path)[0]
    wav_path = f"{filename}.wav"
    # Convert to WAV format
    wav_file.export(wav_path, format="wav")
    rate, data = wavfile.read(wav_path)
    reduced_noise = nr.reduce_noise(y=data, sr=rate, stationary=True)
    wavfile.write(wav_path, rate, reduced_noise)
    return wav_path
