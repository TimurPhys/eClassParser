# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем необходимые пакеты для работы Selenium с Chrome
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    chromium-driver \
    chromium \
    && apt-get clean

# Установка переменных среды для запуска headless Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="${PATH}:/usr/bin"

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY .. /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]