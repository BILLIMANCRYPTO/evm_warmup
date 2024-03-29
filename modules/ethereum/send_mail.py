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

mail_contract_abi = abi_data['mail']
mail_contract_address = "0xa3b31028893c20bEAA882d1508Fe423acA4A70e5"  # Адрес контракта

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

# Send_mail
def send_mail(wallet_address, private_key, web3, i, GAS_PRICE):
    # Инициализация контракта
    mail_contract = web3.eth.contract(address=web3.to_checksum_address(mail_contract_address), abi=mail_contract_abi)

    # Work contract
    destination_mailbox = '0xF8f0929809fe4c73248C27DA0827C98bbE243FCc'
    message = '0x457468657265756de280997320696e7465726f7065726162696c697479206a75737420676f7420736e61726b7920f09faa84'
    destination_chain_id = random.choice(list(chain_ids.keys()))
    
    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.1)
    payable_amount = web3.to_wei(random.uniform(0, 0), 'ether')
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': mail_contract_address,
        'value': payable_amount,
        'data': mail_contract.encodeABI(fn_name='sendMail', args=[destination_chain_id, destination_mailbox, message]),
    })

    print(f'Start with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f"Send Mail to {chain_ids[destination_chain_id]}")
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': mail_contract_address,
            'value': payable_amount,
            'data': mail_contract.encodeABI(fn_name='sendMail', args=[destination_chain_id, destination_mailbox, message]),
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