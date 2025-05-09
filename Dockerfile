FROM python:3.10-slim

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копирование и запуск бота
CMD ["python", ".venv/bot.py"]