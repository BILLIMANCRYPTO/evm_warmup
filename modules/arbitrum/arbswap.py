import json
import random
import time
import logging
from web3 import Web3
from colorama import init, Fore
from settings import MIN_DELAY, MAX_DELAY, MIN_SEND, MAX_SEND, GAS_PRICE, MIN_SWAP, MAX_SWAP
from eth_account import Account
from modules.keys import private_keys
from modules.utils import rpc_endpoints
from modules.chains import chain_ids

# Чтение ABI контрактов из файла abi.json
with open('abi.json', 'r') as f:
    abi_data = json.load(f)

arbswap_contract_abi = abi_data['arbswap']
arbswap_contract_address = "0x6947A425453D04305520E612F0Cb2952E4D07d62"  # Адрес контракта

# Адрес и ABI контракта, в котором находится метод getAmountsOut
arbswapgetdata_contract_abi = abi_data['arbswap_getdata']
arbswapgetdata_contract_address = "0xD01319f4b65b79124549dE409D36F25e04B3e551"

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

# Словарь сопоставления контрактных адресов токенов и их названий
token_names = {
    '0x912CE59144191C1204E64559FE8253a0e49E6548': 'ARB',
    '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8': 'USDC.E',
    '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1': 'DAI',
    '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9': 'USDT',
    '0xaf88d065e77c8cC2239327C5EDb3A432268e5831': 'USDC',
    '0x5979D7b546E38E414F7E9822514be443A4800529': 'wstETH'
}

# Arbitrum Swap
def arb_swap(wallet_address, private_key, web3, i, GAS_PRICE):
    # Инициализация контракта
    arbswap_contract = web3.eth.contract(address=web3.to_checksum_address(arbswap_contract_address),
                                         abi=arbswap_contract_abi)
    # Инициализация контракта для вызова getAmountsOut
    arbswapgetdata_contract = web3.eth.contract(address=web3.to_checksum_address(arbswapgetdata_contract_address),
                                                abi=arbswapgetdata_contract_abi)
    payable_amount = web3.to_wei(random.uniform(MIN_SWAP, MAX_SWAP), 'ether')
    # Контракты токенов
    WETH = web3.to_checksum_address('0x82af49447d8a07e3bd95bd0d56f35241523fbab1')
    ARB = web3.to_checksum_address('0x912CE59144191C1204E64559FE8253a0e49E6548')
    USDC_E = web3.to_checksum_address('0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8')
    DAI = web3.to_checksum_address('0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1')
    USDT = web3.to_checksum_address('0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9')
    USDC = web3.to_checksum_address('0xaf88d065e77c8cC2239327C5EDb3A432268e5831')
    wstETH = web3.to_checksum_address('0x5979D7b546E38E414F7E9822514be443A4800529')

    available_tokens = [ARB, USDC_E, DAI, USDT, USDC, wstETH]

    # Выбор случайного токена из списка
    selected_token = random.choice(available_tokens)

    # Получение minReturn
    amountIn = payable_amount
    path = [WETH, selected_token]
    amounts_out = arbswapgetdata_contract.functions.getAmountsOut(amountIn, path).call()
    minReturn = amounts_out[1]  # Получаем последний элемент списка как minReturn

    # Вывод параметров транзакции в лог перед отправкой
    token_name = token_names[selected_token]
    logging.info(f"  minReturn: {minReturn} {token_name}")  # Вывод minReturn

    # Замените 'srcToken' и 'dstToken' на адреса соответствующих токенов
    srcToken = web3.to_checksum_address('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE')
    dstToken = selected_token
    amount = payable_amount
    flag = 1

    nonce = web3.eth.get_transaction_count(wallet_address)
    balance = web3.eth.get_balance(wallet_address)
    if balance <= 0:
        logging.error(f"Insufficient balance in wallet {wallet_address}")
        return None

    current_gas_price = web3.eth.gas_price
    gas_price = int(current_gas_price * 1.1)

    # Оценка gasLimit
    gas_limit = web3.eth.estimate_gas({
        'from': wallet_address,
        'to': arbswap_contract_address,
        'value': payable_amount,
        'data': arbswap_contract.encodeABI(fn_name='swap', args=[srcToken, dstToken, amount, minReturn, flag]),
    })

    print(f'Start with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'ArbSwap {web3.from_wei(amountIn, "ether")} eth to {minReturn / 10**18} {token_name}')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': arbswap_contract_address,
            'value': payable_amount,
            'data': arbswap_contract.encodeABI(fn_name='swap', args=[srcToken, dstToken, amount, minReturn, flag]),
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
