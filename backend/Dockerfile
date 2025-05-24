# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код в контейнер
COPY . .

# Указываем переменные окружения
ENV FLASK_APP=run.py
ENV FLASK_ENV=development

# Открываем порт
EXPOSE 5000

# Команда запуска приложения
CMD ["flask", "run", "--host=0.0.0.0"]