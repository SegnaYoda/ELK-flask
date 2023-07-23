# Dockerfile for Flask app

# Указываем базовый образ для Python
FROM python:3.10

# Устанавливаем зависимости для работы с PostgreSQL
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y libpq-dev gcc musl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка poetry
RUN pip install poetry

# Создание директории приложения внутри контейнера
WORKDIR /app/

# Копирование файлов с зависимостями в контейнер
COPY pyproject.toml poetry.lock . /app/

# Установка зависимостей из poetry.lock
RUN poetry config virtualenvs.create false \
    && poetry install --no-root

# Копирование исходного кода приложения в контейнер
COPY /app /app

# Открытие порта 5000 в контейнере
EXPOSE 5000

# Запуск приложения Flask
ENTRYPOINT ["python3","-m","flask","run", "--host=0.0.0.0", "--port=5000"]
