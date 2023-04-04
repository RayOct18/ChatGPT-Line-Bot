FROM python:3.9

RUN apt update
RUN apt install ffmpeg -y

RUN pip3 install --upgrade pip
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./ /ChatGPT-Line-Bot
WORKDIR /ChatGPT-Line-Bot

CMD ["gunicorn", "-b", "0.0.0.0:8080", "--worker-class", "gevent" "-w", "2", "-t", "8", "main:app"]