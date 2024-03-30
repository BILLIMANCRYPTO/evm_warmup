import json
import random
import time
import logging
from web3 import Web3
from colorama import init, Fore
from settings import MIN_DELAY, MAX_DELAY, MIN_SEND, MAX_SEND, GAS_PRICE
from eth_account import Account
from modules.keys import private_keys
from modules.utils import rpc_endpoints
from modules.chains import chain_ids

# Чтение ABI контрактов из файла abi.json
with open('abi.json', 'r') as f:
    abi_data = json.load(f)

weth_op_contract_abi = abi_data['weth_op']
sonne_contract_abi = abi_data['sonne_op']
sonne_coll_contract_abi = abi_data['sonne_coll']
weth_op_contract_address = "0x4200000000000000000000000000000000000006"
sonne_contract_address = "0xf7B5965f5C117Eb1B5450187c9DcFccc3C317e8E"
sonne_coll_contract_address = "0x60CF091cD3f50420d50fD7f707414d0DF4751C58"

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

# Функция для ожидания случайного времени
def wait_random_time():
    delay = random.randint(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)

# Функция wrap_eth
def wrap_eth(wallet_address, private_key, web3, i, GAS_PRICE, payable_amount):
    weth_op_contract = web3.eth.contract(
        address=web3.to_checksum_address(weth_op_contract_address),
        abi=weth_op_contract_abi
    )


    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.2)
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': weth_op_contract_address,
        'value': payable_amount,
        'data': weth_op_contract.encodeABI(fn_name='deposit'),
    })

    print(f'Start Sonne module with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'Wrap {web3.from_wei(payable_amount, "ether")} ETH to WETH')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': weth_op_contract_address,
            'value': payable_amount,
            'data': weth_op_contract.encodeABI(fn_name='deposit'),
            'chainId': 10,  # ID сети ETH
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

# Функция approve_weth
def approve_weth(wallet_address, private_key, web3, i, GAS_PRICE):
    weth_op_contract = web3.eth.contract(
        address=web3.to_checksum_address(weth_op_contract_address),
        abi=weth_op_contract_abi
    )

    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.2)
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': weth_op_contract_address,
        'value': 0,
        'data': weth_op_contract.encodeABI(fn_name='approve', args=[sonne_contract_address, 115792089237316195423570985008687907853269984665640564039457584007913129639935]),
    })

    print(f'Approve with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'WETH APPROVE FOR SONNE FINANCE')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': weth_op_contract_address,
            'value': 0,
            'data': weth_op_contract.encodeABI(fn_name='approve', args=[sonne_contract_address, 115792089237316195423570985008687907853269984665640564039457584007913129639935]),
            'chainId': 10,  # ID сети ETH
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

# Функция sonne_liq
def sonne_liq(wallet_address, private_key, web3, i, GAS_PRICE, payable_amount):
    sonne_contract = web3.eth.contract(
        address=web3.to_checksum_address(sonne_contract_address),
        abi=sonne_contract_abi
    )


    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.2)
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': sonne_contract_address,
        'value': 0,
        'data': sonne_contract.encodeABI(fn_name='mint', args=[payable_amount]),
    })

    print(f'Sonne Deposit with wallet: [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'Deposit {web3.from_wei(payable_amount, "ether")} weth to Sonne Finance')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': sonne_contract_address,
            'value': 0,
            'data': sonne_contract.encodeABI(fn_name='mint', args=[payable_amount]),
            'chainId': 10,  # ID сети ETH
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

# Sonne colletarl EnterMarkets
def sonne_enter(wallet_address, private_key, web3, i, GAS_PRICE):
    sonne_coll_contract = web3.eth.contract(
        address=web3.to_checksum_address(sonne_coll_contract_address),
        abi=sonne_coll_contract_abi
    )

    cTokens = ['0xf7B5965f5C117Eb1B5450187c9DcFccc3C317e8E']

    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.2)
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': sonne_coll_contract_address,
        'value': 0,
        'data': sonne_coll_contract.encodeABI(fn_name='enterMarkets', args=[cTokens]),
    })

    print(f'Enter Markets with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'Collateral mode ON')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': sonne_coll_contract_address,
            'value': 0,
            'data': sonne_coll_contract.encodeABI(fn_name='enterMarkets', args=[cTokens]),
            'chainId': 10,  # ID сети ETH
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


# Функция sonne_deposit
def sonne_deposit(wallet_address, private_key, web3, i, GAS_PRICE):
    # Вычисление payable_amount
    payable_amount = web3.to_wei(random.uniform(MIN_SEND, MAX_SEND), 'ether')

    try:
        wrap_eth(wallet_address, private_key, web3, i, GAS_PRICE, payable_amount)
        wait_random_time()
        approve_weth(wallet_address, private_key, web3, i, GAS_PRICE)
        wait_random_time()
        sonne_liq(wallet_address, private_key, web3, i, GAS_PRICE, payable_amount)
        wait_random_time()
        tx_hash = sonne_enter(wallet_address, private_key, web3, i, GAS_PRICE)

        # Возвращаем Hash
        return tx_hash

    except Exception as e:
        logging.error(f'Error occurred for wallet {wallet_address}: {e}')
        logging.exception("Exception occurred", exc_info=True)
        print(f"Error occurred for wallet {wallet_address}: {e}. Skipping to the next action.")
        # В случае ошибки выбрасываем исключение
        raise e


