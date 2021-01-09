FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /tmp/
RUN pip install --progress-bar pretty --no-cache-dir --upgrade -r /tmp/requirements.txt
ADD . /code/
RUN echo "bla" > secretkey.txt