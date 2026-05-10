FROM python:3.13 AS builder
WORKDIR /home/app
COPY pyproject.toml .
COPY poetry.lock .

RUN apt-get update && apt-get -y install git
RUN pip install -U pip poetry
RUN poetry self add poetry-plugin-export
RUN poetry export --without-hashes -f requirements.txt --output requirements.txt --with web --with disney && \
     pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

FROM python:3.13-slim
WORKDIR /home/app

COPY --from=builder /wheels /wheels
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*


COPY ./series_info /home/app/series_info

WORKDIR /home/app
CMD ["gunicorn", "-w","4","-b","0.0.0.0:80", "series_info.app:app"]

EXPOSE 80