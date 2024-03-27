import json
import random
import time
import logging
from web3 import Web3
from colorama import init, Fore
from eth_account import Account
# модули Ethereum
from modules.rainbow_bridge import rainbow_bridge
from modules.send_mail import send_mail
from modules.blur_deposit import blur_deposit
from modules.send_gnosis import send_gnosis

# модули Arbitrum
from modules.radiant import radiant
from modules.santiment import santiment
from modules.aave import aave_deposit
from modules.weth_arb import weth_arb
from modules.vaultka import vaultka_deposit
from modules.arbitrum_bridge import arbitrum_withdraw
from modules.granary import granary
from modules.rari_bridge import rari_bridge
from modules.balancer import balancer

# Settings
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
- Arbitrum WarmUp (4)
: """).lower()

# Проверка корректности выбора сети
if network_choice not in rpc_endpoints:
    print("Напиши нормально ебик. Иди подумай над своим поведением")
    exit()

# Выбор максимального числа модулей для исполнения
max_modules = 0
if network_choice == "4":
    max_modules = int(input("Максимальное кол-во модулей Arbitrum от 1 до 9: "))
    max_modules = min(max(max_modules, 1), 9)

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

for i, (wallet_address, private_key) in enumerate(zip(wallets, private_keys), 1):
    if network_choice in ["1", "3", "4"]:
        check_gwei(web3, GAS_PRICE)

    if network_choice == "1":
        threshold_gwei = GAS_PRICE
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
    elif network_choice == "4":
        threshold_gwei = GAS_PRICE
        check_gwei(web3, threshold_gwei)  # Вызываем check_gwei() для чека газа в 4 модуле
        modules = ["radiant", "santiment", "weth_arb", "aave_deposit", "vaultka_deposit", "arbitrum_withdraw", "granary", "rari_bridge", "balancer"]
        selected_modules = random.sample(modules, min(random.randint(1, len(modules)), max_modules))
        random_sleep_duration = random.randint(MIN_DELAY, MAX_DELAY)
        for module_type in selected_modules:
            try:
                if module_type == "radiant":
                    tx_hash = radiant(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "santiment":
                    tx_hash = santiment(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "aave_deposit":
                    tx_hash = aave_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "vaultka_deposit":
                    tx_hash = vaultka_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "arbitrum_withdraw":
                    tx_hash = arbitrum_withdraw(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "granary":
                    tx_hash = granary(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "balancer":
                    tx_hash = balancer(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "rari_bridge":
                    tx_hash = rari_bridge(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "weth_arb":
                    tx_hash = weth_arb(wallet_address, private_key, web3, i, GAS_PRICE)
                time.sleep(random_sleep_duration)
                print(f'Waiting for {random_sleep_duration} seconds before processing next action...')
            except Exception as e:
                print(f"Error: {e}. Skipping to the next action.")
                continue
    elif network_choice == "3":
        threshold_gwei = GAS_PRICE
        check_gwei(web3, threshold_gwei)
        modules = ["rainbow_bridge", "blur_deposit"]
        selected_modules = random.sample(modules, random.randint(1, len(modules)))
        send_mail_index = random.randint(0, len(selected_modules))
        selected_modules.insert(send_mail_index, "send_mail")
        random_sleep_duration = random.randint(MIN_DELAY, MAX_DELAY)
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

    delay_before_next_wallet = random.randint(MIN_DELAY, MAX_DELAY)
    print(f'Waiting for {delay_before_next_wallet} seconds before processing next wallet...')
    time.sleep(delay_before_next_wallet)

print("Transaction processing completed for all wallets.")

