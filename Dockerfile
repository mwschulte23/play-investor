FROM python:3.8

ADD requirements.txt requirements.txt
ADD . .

RUN pip install -r requirements.txt

EXPOSE 8501