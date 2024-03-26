import json
import random
import time
import logging
from web3 import Web3
from colorama import init, Fore
from eth_account import Account
from modules.rainbow_bridge import rainbow_bridge
from modules.send_mail import send_mail
from modules.blur_deposit import blur_deposit
from modules.send_gnosis import send_gnosis
from settings import MIN_DELAY, MAX_DELAY, MIN_SEND, MAX_SEND, GAS_PRICE
from modules.utils import rpc_endpoints
from modules.chains import chain_ids
from modules.keys import private_keys

init(autoreset=True)  # Инициализация colorama

# Функция для выбора случайного цвета из списка цветов colorama
def random_color():
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
    return random.choice(colors)

# Вывод с использованием рандомных цветов и символов Unicode
print(random_color() + ' ╔═══╗╔═══╗╔══╗╔╗─╔╗╔════╗╔══╗   ╔══╗ ╔══╗╔══╗')
print(random_color() + ' ║╔══╝║╔═╗║║╔╗║║╚═╝║╚═╗╔═╝║╔╗║   ║╔╗╚╗║╔╗║║╔╗║ ')
print(random_color() + ' ║║╔═╗║╚═╝║║╚╝║║╔╗ ║  ║║  ║╚╝║   ║║╚╗║║╚╝║║║║║')
print(random_color() + ' ║║╚╗║║╔╗╔╝║╔╗║║║╚╗║  ║║  ║╔╗║   ║║ ║║║╔╗║║║║║')
print(random_color() + ' ║╚═╝║║║║║ ║║║║║║ ║║  ║║  ║║║║   ║╚═╝║║║║║║╚╝║')
print(random_color() + ' ╚═══╝╚╝╚╝ ╚╝╚╝╚╝ ╚╝  ╚╝  ╚╝╚╝   ╚═══╝╚╝╚╝╚══╝', '\n')

# Настройка логгирования
logging.basicConfig(filename='transaction_errors.log', level=logging.ERROR)

# Перемешивание списка приватных ключей
random.shuffle(private_keys)

# Выбор сети
network_choice = input("""
Выбери режим работы:
- Eth sendMail (1) 
- Gnosis sendMail (2)
- Eth Pro Mode (3)
: """).lower()

# Проверка корректности выбора сети
if network_choice not in rpc_endpoints:
    print("Напиши нормально ебик. Иди подумай над своим поведением")
    exit()

# Используемый RPC
rpc_endpoint = rpc_endpoints[network_choice]
web3 = Web3(Web3.HTTPProvider(rpc_endpoint))


# Чек Gwei
def check_gwei(web3, threshold_gwei):
    current_gwei = web3.eth.gas_price / 10**9  # Приведение к нормальному виду
    if current_gwei > threshold_gwei:
        print(f"{current_gwei:.2f} gwei > {threshold_gwei} gwei.")
        while current_gwei > threshold_gwei:
            time.sleep(30)  # Проверка каждые 10 секунд
            current_gwei = web3.eth.gas_price / 10**9  # Приведение к нормальному виду
            print(f"{current_gwei:.2f} gwei > {threshold_gwei} gwei")
        print(f"{threshold_gwei} gwei. Start working")


# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

web3 = Web3(Web3.HTTPProvider(rpc_endpoint))

# Отправка транзакции с каждого кошелька
for i, (wallet_address, private_key) in enumerate(zip(wallets, private_keys), 1):
    # Проверка цены газа перед каждой транзакцией
    if network_choice == "1" or network_choice == "3":
        check_gwei(web3, GAS_PRICE) # gwei настройка

    if network_choice == "1":
        threshold_gwei = GAS_PRICE  # gwei настройка
        check_gwei(web3, threshold_gwei)
        try:
            tx_hash = send_mail(wallet_address, private_key, web3, i, GAS_PRICE)
        except Exception as e:
            print(f"Error: {e}. Skipping to the next action.")
            continue
    elif network_choice == "2":
        try:
            tx_hash = send_gnosis(wallet_address, private_key, web3, i)
        except Exception as e:
            print(f"Error: {e}. Skipping to the next action.")
            continue
    elif network_choice == "3":
        threshold_gwei = GAS_PRICE  # gwei настройка
        modules = ["rainbow_bridge", "blur_deposit"]
        # Случайный выбор модулей из списка
        selected_modules = random.sample(modules, random.randint(1, len(modules)))
        # Вставляем send_mail в случайное место в списке
        # selected_modules = random.sample(modules, random.randint(1, len(modules))) как убрать этот модуль 
        send_mail_index = random.randint(0, len(selected_modules)) # это можно убрать, если нужно обязательное исполнение модуля 
        selected_modules.insert(send_mail_index, "send_mail") # это можно убрать, если нужно обязательное исполнение модуля
        random_sleep_duration = random.randint(MIN_DELAY, MAX_DELAY)  # Случайная задержка от 100 до 200 секунд
        for module_type in selected_modules:
            try:
                if module_type == "send_mail":
                    tx_hash = send_mail(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "rainbow_bridge":
                    tx_hash = rainbow_bridge(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "blur_deposit":
                    tx_hash = blur_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                time.sleep(random_sleep_duration)
                print(f'Waiting for {random_sleep_duration} seconds before processing next action...')
            except Exception as e:
                print(f"Error: {e}. Skipping to the next action.")
                continue
    else:
        print("Invalid network choice")
        break

    if tx_hash:
        print('')
    else:
        print(f'Skipping wallet {wallet_address} due to error.')

    # Рандомное время ожидания между 500 и 1000 секундами перед следующей транзакцией
    delay_before_next_wallet = random.randint(MIN_DELAY, MAX_DELAY)
    print(f'Waiting for {delay_before_next_wallet} seconds before processing next wallet...')
    time.sleep(delay_before_next_wallet)

print("Transaction processing completed for all wallets.")