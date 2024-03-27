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

balancer_contract_abi = abi_data['balancer']
balancer_contract_address = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"  # Адрес контракта

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

# Balancer
def balancer(wallet_address, private_key, web3, i, GAS_PRICE):
    # Инициализация контракта
    balancer_contract = web3.eth.contract(address=web3.to_checksum_address(balancer_contract_address), abi=balancer_contract_abi)
    payable_amount = web3.to_wei(random.uniform(0.0001, 0.0002), 'ether')

    # Work contract
    poolId = '0x32df62dc3aed2cd6224193052ce665dc181658410002000000000000000003bd'
    sender = wallet_address
    recipient = wallet_address
    assets = [
        '0x3082CC23568eA640225c2467653dB90e9250AaA0',
        '0x0000000000000000000000000000000000000000'
    ]
    maxAmountsIn = [0, payable_amount]
    userData = '0x0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000002b38d7174f50ae00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005af3107a4000'
    fromInternalBalance = False

    #Создаю кортеж
    request = (assets, maxAmountsIn, userData, fromInternalBalance)

    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.1)
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': balancer_contract_address,
        'value': payable_amount,
        'data': balancer_contract.encodeABI(fn_name='joinPool', args=[poolId, sender, recipient, request]),
    })

    print(f'Start with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'Balancer add Liquidity {web3.from_wei(payable_amount, "ether")} eth')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': balancer_contract_address,
            'value': payable_amount,
            'data': balancer_contract.encodeABI(fn_name='joinPool', args=[poolId, sender, recipient, request]),
            'chainId': 42161,  # ID сети ETH
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