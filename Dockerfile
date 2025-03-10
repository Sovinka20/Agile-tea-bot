# Используем официальный образ Python в качестве базового образа
FROM python:3.9-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем только необходимые файлы
COPY requirements.txt ./
COPY bot.py ./
COPY utils.py ./
COPY message_utils.py ./
COPY commands.py ./
COPY admin_commands.py ./

# Если есть другие файлы или папки
# COPY other_files/ ./other_files/  

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота при старте контейнера
CMD ["python", "bot.py"]