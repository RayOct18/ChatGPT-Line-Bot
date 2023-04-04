FROM python:3.9-alpine

RUN apk update
RUN apk add --no-cache ffmpeg build-base gfortran cmake openblas-dev linux-headers

RUN pip3 install --upgrade pip
ADD requirements.txt requirements.txt
RUN pip3 install -v -r requirements.txt

COPY ./ /ChatGPT-Line-Bot
WORKDIR /ChatGPT-Line-Bot

CMD ["python3", "main.py"]