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

traderjoy_contract_abi = abi_data['traderjoy']
traderjoy_contract_address = "0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30"  # Адрес контракта

# Генерация кошельков из приватных ключей
wallets = [Account.from_key(private_key).address for private_key in private_keys]

# Словарь сопоставления контрактных адресов токенов и их названий
# Arbitrum Swap
def traderjoy_swap(wallet_address, private_key, web3, i, GAS_PRICE):
    # Инициализация контракта
    traderjoy_contract = web3.eth.contract(address=web3.to_checksum_address(traderjoy_contract_address),
                                         abi=traderjoy_contract_abi)

    payable_amount = web3.to_wei(random.uniform(MIN_SWAP, MAX_SWAP), 'ether')

    # Контракты токенов
    WETH = web3.to_checksum_address('0x82af49447d8a07e3bd95bd0d56f35241523fbab1')
    USDC_E = web3.to_checksum_address('0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8')
    USDT = web3.to_checksum_address('0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9')
    ARB = web3.to_checksum_address('0x912CE59144191C1204E64559FE8253a0e49E6548')
    PENDLE = web3.to_checksum_address('0x0c880f6761F1af8d9Aa9C466984b80DAb9a8c9e8')
    MAGIC = web3.to_checksum_address('0x539bdE0d7Dbd336b79148AA742883198BBF60342')
    WOO = web3.to_checksum_address('0xcAFcD85D8ca7Ad1e1C6F82F651fA15E33AEfD07b')
    TIA = web3.to_checksum_address('0xD56734d7f9979dD94FAE3d67C7e928234e71cD4C')

    # Контракты ПАР
    ETH_USDT = web3.to_checksum_address('0xd387c40a72703B38A5181573724bcaF2Ce6038a5') # для usdt
    ETH_ARB = web3.to_checksum_address('0x0Be4aC7dA6cd4bAD60d96FbC6d091e1098aFA358') # для arb
    ETH_PENDLE = web3.to_checksum_address('0xe2b32e6Dd706af1aE7E6Ea71d0477b5aDaF9c9D1') # для PENDLE
    ETH_MAGIC = web3.to_checksum_address('0xE847C55a3148580E864EC31E7273bc4eC25089c1') # для magic
    ETH_WOO = web3.to_checksum_address('0xB87495219C432fc85161e4283DfF131692A528BD') # для woo
    ETH_TIA = web3.to_checksum_address('0xB57EAd49eD94eAd81bc8d20EEB90e9758bd88B33') # для tia

    # Маршруты свапов
    ETH_TO_USDT = [WETH, USDC_E, USDT] # для usdt
    ETH_TO_ARB = [WETH, ARB] # для arb
    ETH_TO_PENDLE = [WETH, PENDLE]  # для PENDLE
    ETH_TO_MAGIC = [WETH, MAGIC] # для magic
    ETH_TO_WOO = [WETH, WOO] # для woo
    ETH_TO_TIA = [WETH, TIA]  # для tia

    # Путь для свапа
    swap_path_usdt = {'pairBinSteps': [15, 1], 'versions': [2, 2], 'tokenPath': ETH_TO_USDT} # для usdt
    swap_path_arb = {'pairBinSteps': [0], 'versions': [0], 'tokenPath': ETH_TO_ARB}  # для usdt
    swap_path_pendle = {'pairBinSteps': [25], 'versions': [2], 'tokenPath': ETH_TO_PENDLE}  # для PENDLE
    swap_path_magic = {'pairBinSteps': [20], 'versions': [2], 'tokenPath': ETH_TO_MAGIC} # для magic
    swap_path_woo = {'pairBinSteps': [25], 'versions': [2], 'tokenPath': ETH_TO_WOO}  # для woo
    swap_path_tia = {'pairBinSteps': [25], 'versions': [2], 'tokenPath': ETH_TO_TIA}  # для woo

    # Список всех возможных пар и их соответствующих путей
    PAIRS_AND_PATHS = {
        'ETH_USDT': (ETH_USDT, swap_path_usdt),
        'ETH_ARB': (ETH_ARB, swap_path_arb),
        'ETH_PENDLE': (ETH_PENDLE, swap_path_pendle),
        'ETH_MAGIC': (ETH_MAGIC, swap_path_magic),
        'ETH_WOO': (ETH_WOO, swap_path_woo),
        'ETH_TIA': (ETH_TIA, swap_path_tia)
    }

    # Выбираем случайную пару и ее путь
    pair_name, (pair_address, pair_path) = random.choice(list(PAIRS_AND_PATHS.items()))


    # Получение getSwapOut
    amountIn = payable_amount
    swapForY = True
    amounts_out = traderjoy_contract.functions.getSwapOut(pair_address, amountIn, swapForY).call()
    minReturn = amounts_out[1]  # Получаем последний элемент списка как minReturn

    # Вывод параметров транзакции в лог перед отправкой

    # Заполняем транзакцию
    amountOutMin = minReturn
    to = wallet_address
    deadline = int(time.time()) + 10 * 60  # Дедлайн транзакции

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
        'to': traderjoy_contract_address,
        'value': payable_amount,
        'data': traderjoy_contract.encodeABI(fn_name='swapExactNATIVEForTokens', args=[amountOutMin, pair_path, to, deadline]),
    })

    print(f'Start with wallet [{i}/{len(wallets)}]: {wallet_address}')
    print(Fore.CYAN + f'TraderJoy Swap {web3.from_wei(amountIn, "ether")} {pair_name}')
    try:
        tx_params = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': gas_limit,
            'to': traderjoy_contract_address,
            'value': payable_amount,
            'data': traderjoy_contract.encodeABI(fn_name='swapExactNATIVEForTokens', args=[amountOutMin, pair_path, to, deadline]),
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
