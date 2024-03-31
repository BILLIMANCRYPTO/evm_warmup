import json
import random
import time
import logging
import requests
import re
from web3 import Web3
from colorama import init, Fore
from bs4 import BeautifulSoup
from settings import MIN_DELAY, MAX_DELAY, MIN_SEND, MAX_SEND, GAS_PRICE
from eth_account import Account
from modules.keys import private_keys

# Чтение ABI контрактов из файла abi.json
with open('abi.json', 'r') as f:
    abi_data = json.load(f)
    
ens_contract_abi = abi_data['ens_renewal']
getbytes_contract_abi = abi_data['ens_getbytes']
getname_contract_abi = abi_data['ens_getname']
oldgetname_contract_abi = abi_data['ens_oldgetname']
ens_contract_address = "0x253553366Da8546fC250F225fe3d25d0C782303b"
getbytes_contract_address = "0xa58E81fe9b61B5c3fE2AFD33CF304c454AbFc7Cb"
ens_getname_contract_address = "0xA2C122BE93b0074270ebeE7f6b7292C7deB45047"
oldens_getname_contract_address= "0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63"

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

def wait_random_time():
    delay = random.randint(1, 1)
    time.sleep(delay)


# Функция для парсинга ENS домена
def parse_ens_domain(wallet_address, private_key, web3, i, GAS_PRICE):
    try:
        # Получаем bytes32 через вызов node контракта getbytes
        getbytes_contract_address = "0xa58E81fe9b61B5c3fE2AFD33CF304c454AbFc7Cb"
        getbytes_contract = web3.eth.contract(address=getbytes_contract_address, abi=getbytes_contract_abi)
        bytes32_value = getbytes_contract.functions.node(wallet_address).call()

        # Получаем имя домена через вызов name контракта getname
        ens_getname_contract_address = "0xA2C122BE93b0074270ebeE7f6b7292C7deB45047"
        getname_contract = web3.eth.contract(address=ens_getname_contract_address, abi=getname_contract_abi)
        domain_name_bytes = getname_contract.functions.name(bytes32_value).call()

        # Убираем .eth из имени домена
        ens_domain = domain_name_bytes.split('.eth')[0]

        # Если ens_domain пустой, проверяем его наличие на контракте 0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63
        if not ens_domain:
            oldens_getname_contract_address = "0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63"
            oldgetname_contract = web3.eth.contract(address=oldens_getname_contract_address,
                                                    abi=oldgetname_contract_abi)
            old_domain_name_bytes = oldgetname_contract.functions.name(bytes32_value).call()
            old_ens_domain = old_domain_name_bytes.split('.eth')[0]
            if old_ens_domain:
                ens_domain = old_ens_domain

        return ens_domain
    except Exception as e:
        logging.error(f'Error occurred while parsing ENS domain for wallet {wallet_address}: {e}')
        return None


# Функция для получения цены продления домена
def get_rent_price(wallet_address, private_key, web3, i, GAS_PRICE, ens_domain):
    duration = 31536000  # Задаем значение по умолчанию (1 год аренды)
    try:
        ens_contract = web3.eth.contract(address=web3.to_checksum_address(ens_contract_address), abi=ens_contract_abi)
        rent_price_tuple = ens_contract.functions.rentPrice(ens_domain, duration).call()
        if isinstance(rent_price_tuple, tuple) and len(rent_price_tuple) > 0:
            rent_price = rent_price_tuple[0]  # Извлекаем первый элемент кортежа
            return rent_price
        else:
            logging.error(f"Rent price for ENS domain {ens_domain} is not a tuple or empty")
            return None
    except Exception as e:
        logging.error(f'Error occurred while getting rent price for ENS domain {ens_domain}: {e}')
        return None



# Ens Renewal
def ens_renewal(wallet_address, private_key, web3, i, GAS_PRICE, ens_domain, duration, rent_price):
    ens_contract = web3.eth.contract(address=web3.to_checksum_address(ens_contract_address), abi=ens_contract_abi)

    # Добавим проверку на None перед вызовом web3.to_wei()
    if rent_price is None:
        logging.error(f"Rent price for ENS domain {ens_domain} is None")
        return None

    payable_amount = rent_price # Преобразуем в wei, а не в ether

    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.05)
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': ens_contract_address,
        'value': payable_amount,
        'data': ens_contract.encodeABI(fn_name='renew', args=[ens_domain, duration]),
    })

    print(f'Start with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'Renewal {ens_domain}.eth')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': ens_contract_address,
            'value': payable_amount,
            'data': ens_contract.encodeABI(fn_name='renew', args=[ens_domain, duration]),
            'chainId': 1,  # ID сети ETH
        }

        signed_tx = web3.eth.account.sign_transaction(tx_params, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f'Transaction sent: {tx_hash.hex()}')

        # Ожидание подтверждения транзакции
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt.status == 1:
            print(Fore.GREEN + f'Transaction {tx_hash.hex()} successfully confirmed')
        else:
            print(Fore.RED + f'Transaction {tx_hash.hex()} failed')

        return tx_hash.hex()

    except Exception as e:
        logging.error(f'Error occurred for wallet {wallet_address}: {e}')
        logging.exception("Exception occurred", exc_info=True)
        return None



def ensdomain_renewal(wallet_address, private_key, web3, i, GAS_PRICE):
    try:
        ens_domain = parse_ens_domain(wallet_address, private_key, web3, i, GAS_PRICE)
        if ens_domain is None:
            return None

        wait_random_time()

        rent_price = get_rent_price(wallet_address, private_key, web3, i, GAS_PRICE, ens_domain)
        if rent_price is None:
            return None

        wait_random_time()

        duration = 31536000  # 1 year
        tx_hash = ens_renewal(wallet_address, private_key, web3, i, GAS_PRICE, ens_domain, duration, rent_price)

        return tx_hash
    except Exception as e:
        logging.error(f'Error occurred for wallet {wallet_address}: {e}')
        logging.exception("Exception occurred", exc_info=True)
        print(f"Error occurred for wallet {wallet_address}: {e}. Skipping to the next action.")
        return None
