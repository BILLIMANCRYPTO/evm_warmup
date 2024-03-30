import json
import random
import time
import logging
from web3 import Web3
from colorama import init, Fore
from settings import MIN_DELAY, MAX_DELAY, MIN_SEND, MAX_SEND, GAS_PRICE, MIN_BUNGEE, MAX_BUNGEE
from eth_account import Account
from modules.keys import private_keys

# Чтение ABI контрактов из файла abi.json
with open('abi.json', 'r') as f:
    abi_data = json.load(f)

bungee_contract_abi = abi_data['bungee_eth']
bungee_contract_address = "0xb584D4bE1A5470CA1a8778E9B86c81e165204599"  # Адрес контракта

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

# RainbowBrdige
def bungee_refuel(wallet_address, private_key, web3, i, GAS_PRICE):
    # Инициализация контракта
    bungee_contract = web3.eth.contract(address=web3.to_checksum_address(bungee_contract_address), abi=bungee_contract_abi)

    # Удаление префикса "0x" из адреса кошелька
    _to = wallet_address
    destinationChainId = 100
    
    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.1)
    payable_amount = web3.to_wei(random.uniform(MIN_BUNGEE, MAX_BUNGEE), 'ether') # меняй сумму
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': bungee_contract_address,
        'value': payable_amount,
        'data': bungee_contract.encodeABI(fn_name='depositNativeToken', args=[destinationChainId, _to]),
    })

    print(f'Start with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'Bungee bridge {web3.from_wei(payable_amount, "ether")} eth')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': bungee_contract_address,
            'value': payable_amount,
            'data': bungee_contract.encodeABI(fn_name='depositNativeToken', args=[destinationChainId, _to]),
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
