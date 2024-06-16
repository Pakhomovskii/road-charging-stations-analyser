import logging

# Создаем логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования для этого логгера

# Создаем обработчик для записи в файл
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования для обработчика

# Создаем форматтер для определения формата сообщений в логе
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавляем обработчик к логгеру
logger.addHandler(file_handler)