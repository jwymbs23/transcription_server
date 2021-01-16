FROM python:3.7


RUN apt-get -y update
RUN apt-get -y install libssl1.1 libssl-dev
RUN apt-get -y install ffmpeg

ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD python app.py