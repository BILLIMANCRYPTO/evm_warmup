import random

# Рандомное время ожидания между транзакциями (в секундах)
MIN_DELAY = 6  # Минимальное время ожидания
MAX_DELAY = 10  # Максимальное время ожидания

# Рандомная отправляемая сумма (в ETH)
MIN_SEND = 0.01  # Минимальная сумма
MAX_SEND = 0.1   # Максимальная сумма

# Стоимость газа (в Gwei)
GAS_PRICE = 15 # Установленное значение стоимости газа

# Функция для генерации случайной суммы в пределах заданного диапазона
def generate_random_amount():
    return random.uniform(MIN_SEND, MAX_SEND)

# Функция для генерации случайной задержки между транзакциями
def generate_random_delay():
    return random.randint(MIN_DELAY, MAX_DELAY)
