import json
import random
import time
import logging
from web3 import Web3
from colorama import init, Fore
from eth_account import Account
# модули Ethereum
from modules.ethereum.rainbow_bridge import rainbow_bridge
from modules.ethereum.send_mail import send_mail
from modules.ethereum.blur_deposit import blur_deposit
from modules.ethereum.mint_zerion import zerion_mint
from modules.ethereum.zora import zora_donate
from modules.ethereum.bungee_refuel import bungee_refuel
from modules.ethereum.ens_renewal import ensdomain_renewal
from modules.ethereum.withdraw_ens import ens_withdraw

# модули Gnosis
from modules.gnosis.send_gnosis import (send_gnosis)

# модули Arbitrum
from modules.arbitrum.radiant import radiant
from modules.arbitrum.santiment import santiment
from modules.arbitrum.aave import aave_deposit
from modules.arbitrum.weth_arb import weth_arb
from modules.arbitrum.vaultka import vaultka_deposit
from modules.arbitrum.arbitrum_bridge import arbitrum_withdraw
from modules.arbitrum.granary import granary
from modules.arbitrum.rari_bridge import rari_bridge
from modules.arbitrum.balancer import balancer
from modules.arbitrum.arbswap import arb_swap
from modules.arbitrum.mint_nft_arb import sparta_mint
from modules.arbitrum.traderjoy import traderjoy_swap

# модули Optimism
from modules.optimism.aave_op import aave_op_deposit
from modules.optimism.exactly import exactly_deposit
from modules.optimism.extrafi import extrafi_deposit
from modules.optimism.unitusdapp import unitus_deposit
from modules.optimism.picka_reward import picka
from modules.optimism.wepiggy import wepiggy_deposit
from modules.optimism.sonne_dep import sonne_deposit


# Settings
from settings import MIN_DELAY, MAX_DELAY, MIN_SEND, MAX_SEND, GAS_PRICE, MIN_SWAP, MAX_SWAP
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
- Optimism WarmUp (5)
- Eth WarmUp (6)
- ENS Domain Renew (7)
: """).lower()

# Проверка корректности выбора сети
if network_choice not in rpc_endpoints:
    print("Напиши нормально ебик. Иди подумай над своим поведением")
    exit()

# Выбор максимального числа модулей для исполнения
max_modules = 0
max_repeats = 0
if network_choice == "4":
    max_modules = int(input("Максимальное кол-во модулей Arbitrum от 1 до 12: "))
    max_modules = min(max(max_modules, 1), 12)

elif network_choice == "5":
    max_modules = int(input("Максимальное кол-во модулей Optimism от 1 до 7: "))
    max_modules = min(max(max_modules, 1), 7)

elif network_choice == "6":
    max_modules = int(input("Максимальное кол-во модулей Ethereum от 1 до 6: "))
    max_modules = min(max(max_modules, 1), 6)


elif network_choice == "2":
    try:
        max_repeats = int(input("Максимальное кол-во повторений send_gnosis: "))
    except ValueError:
        print("Введи целое число")



# Используемый RPC
rpc_endpoint = rpc_endpoints[network_choice]
web3 = Web3(Web3.HTTPProvider(rpc_endpoint))


# Чек Gwei
def check_gwei(network_choice, threshold_gwei):
    # Проверка, является ли выбранная сеть Ethereum
    if network_choice in ["1", "3", "4", "6", "7"]:
        rpc_endpoint = "https://rpc.ankr.com/eth"
        web3 = Web3(Web3.HTTPProvider(rpc_endpoint))
        current_gwei = web3.eth.gas_price / 10**9  # Приведение к нормальному виду
        if current_gwei > threshold_gwei:
            print(f"{current_gwei:.2f} gwei > {threshold_gwei} gwei.")
            while current_gwei > threshold_gwei:
                time.sleep(30)  # Проверка каждые 10 секунд
                current_gwei = web3.eth.gas_price / 10**9  # Приведение к нормальному виду
                print(f"{current_gwei:.2f} gwei > {threshold_gwei} gwei")
            print(f"{threshold_gwei} gwei. Start working")
    else:
        print("Цена газа не проверяется для выбранной сети.")


# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

web3 = Web3(Web3.HTTPProvider(rpc_endpoint))

tx_hash = None

for i, (wallet_address, private_key) in enumerate(zip(wallets, private_keys), 1):
    if network_choice in ["1", "3", "4", "6", "7"]:
        check_gwei(network_choice, GAS_PRICE)

    if network_choice == "1":
        threshold_gwei = GAS_PRICE
        check_gwei(network_choice, threshold_gwei)
        try:
            tx_hash = send_mail(wallet_address, private_key, web3, i, GAS_PRICE)
        except Exception as e:
            print(f"Error: {e}. Skipping to the next action.")
            continue
    elif network_choice == "7":
        threshold_gwei = GAS_PRICE
        check_gwei(network_choice, threshold_gwei)
        try:
            tx_hash = ensdomain_renewal(wallet_address, private_key, web3, i, GAS_PRICE)
        except Exception as e:
            if "Exception occurred" in str(e):
                print(Fore.YELLOW + f"No active Ens domain on the wallet {wallet_address}")
                continue
            else:
                print(f"Error: {e}. Skipping to the next action.")
                continue
    elif network_choice == "2":
        try:
            repeats = random.randint(1, max_repeats)
            for _ in range(repeats):
                tx_hash = send_gnosis(wallet_address, private_key, web3, i)
                delay_between_repeats = random.randint(MIN_DELAY, MAX_DELAY)
                print(f'{"":<7}Waiting for {delay_between_repeats} seconds before next send_gnosis...')
                time.sleep(delay_between_repeats)
        except Exception as e:
            print(f"Error: {e}. Skipping to the next action.")
            continue
    elif network_choice == "4":
        threshold_gwei = GAS_PRICE
        check_gwei(network_choice, threshold_gwei)  # Вызываем check_gwei() для чека газа в 4 модуле
        modules = ["radiant", "santiment", "weth_arb", "aave_deposit", "vaultka_deposit", "arbitrum_withdraw", "granary", "rari_bridge", "balancer","arb_swap", "sparta_mint", "traderjoy_swap"]
        # "radiant", "santiment", "weth_arb", "aave_deposit", "vaultka_deposit", "arbitrum_withdraw", "granary", "rari_bridge", "balancer","arb_swap", "sparta_mint"
        selected_modules = random.sample(modules, min(random.randint(1, len(modules)), max_modules))
        for module_type in selected_modules:
            try:
                if module_type == "traderjoy_swap":
                    tx_hash = traderjoy_swap(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "santiment":
                    tx_hash = santiment(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "radiant":
                    tx_hash = radiant(wallet_address, private_key, web3, i, GAS_PRICE)
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
                elif module_type == "arb_swap":
                    tx_hash = arb_swap(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "rari_bridge":
                    tx_hash = rari_bridge(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "sparta_mint":
                    tx_hash = sparta_mint(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "weth_arb":
                    tx_hash = weth_arb(wallet_address, private_key, web3, i, GAS_PRICE)
                random_sleep_duration = random.randint(MIN_DELAY, MAX_DELAY)
                print(f'Waiting for {random_sleep_duration} seconds before processing next action...')
                time.sleep(random_sleep_duration)
            except Exception as e:
                if "0x363918c5" in str(e):
                    print(Fore.YELLOW + "Nft for {wallet_address} already minted")
                elif "0x4feac00c" in str(e):
                    print(Fore.YELLOW + "Error occurred, trying another pair...")
                    try:
                        tx_hash = traderjoy_swap(wallet_address, private_key, web3, i, GAS_PRICE)
                    except Exception as e:
                        print(f"Error occurred during retry: {e}. Skipping to the next action.")
                        logging.error(f'Error occurred for wallet {wallet_address}: {str(e)}')
                        logging.exception("Exception occurred", exc_info=True)
                        continue
                else:
                    print(f"Error: {e}. Skipping to the next action.")
                    logging.error(f'Error occurred for wallet {wallet_address}: {str(e)}')
                    logging.exception("Exception occurred", exc_info=True)
                    continue
    elif network_choice == "3":
        threshold_gwei = GAS_PRICE
        check_gwei(web3, threshold_gwei)
        modules = ["rainbow_bridge", "blur_deposit"]
        selected_modules = random.sample(modules, random.randint(1, len(modules)))
        send_mail_index = random.randint(0, len(selected_modules))
        selected_modules.insert(send_mail_index, "send_mail")
        for module_type in selected_modules:
            try:
                if module_type == "send_mail":
                    tx_hash = send_mail(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "rainbow_bridge":
                    tx_hash = rainbow_bridge(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "blur_deposit":
                    tx_hash = blur_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                random_sleep_duration = random.randint(MIN_DELAY, MAX_DELAY)
                print(f'{"":<7}Waiting for {random_sleep_duration} seconds before processing next action...')
                time.sleep(random_sleep_duration)
            except Exception as e:
                print(f"Error: {e}. Skipping to the next action.")
                continue
    elif network_choice == "5":
        threshold_gwei = GAS_PRICE
        check_gwei(network_choice, threshold_gwei)
        modules = ["aave_op_deposit", "exactly_deposit", "extrafi_deposit", "unitus_deposit", "picka", "wepiggy_deposit", "sonne_deposit"]
        # "aave_op_deposit", "exactly_deposit", "extrafi_deposit", "unitus_deposit", "picka", "wepiggy_deposit", "sonne_deposit"
        selected_modules = random.sample(modules, min(random.randint(1, len(modules)), max_modules))
        for module_type in selected_modules:
            try:
                if module_type == "aave_op_deposit":
                    tx_hash = aave_op_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "exactly_deposit":
                    tx_hash = exactly_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "extrafi_deposit":
                    tx_hash = extrafi_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "unitus_deposit":
                    tx_hash = unitus_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "wepiggy_deposit":
                    tx_hash = wepiggy_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "sonne_deposit":
                    tx_hash = sonne_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "picka":
                    tx_hash = picka(wallet_address, private_key, web3, i, GAS_PRICE)
                random_sleep_duration = random.randint(MIN_DELAY, MAX_DELAY)
                print(f'Waiting for {random_sleep_duration} seconds before processing next action...')
                time.sleep(random_sleep_duration)
            except Exception as e:
                print(f"Error: {e}. Skipping to the next action.")
                continue
    elif network_choice == "6":
        threshold_gwei = GAS_PRICE
        check_gwei(network_choice, threshold_gwei)
        modules = ["rainbow_bridge", "blur_deposit", "zerion_mint", "zora_donate", "bungee_refuel", "ens_withdraw"]
        selected_modules = random.sample(modules, min(random.randint(1, len(modules)), max_modules))
        for module_type in selected_modules:
            try:
                if module_type == "rainbow_bridge":
                    tx_hash = rainbow_bridge(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "blur_deposit":
                    tx_hash = blur_deposit(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "zerion_mint":
                    tx_hash = zerion_mint(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "ens_withdraw":
                    tx_hash = ens_withdraw(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "zora_donate":
                    tx_hash = zora_donate(wallet_address, private_key, web3, i, GAS_PRICE)
                elif module_type == "bungee_refuel":
                    tx_hash = bungee_refuel(wallet_address, private_key, web3, i, GAS_PRICE)
                random_sleep_duration = random.randint(MIN_DELAY, MAX_DELAY)
                print(f'Waiting for {random_sleep_duration} seconds before processing next action...')
                time.sleep(random_sleep_duration)
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

