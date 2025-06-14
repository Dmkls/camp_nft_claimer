from web3 import AsyncWeb3, AsyncHTTPProvider
import asyncio
import json
from configs import config
from random import randint, uniform

RPC_URL = "https://rpc.basecamp.t.raas.gelato.cloud"
w3 = AsyncWeb3(provider=AsyncHTTPProvider(endpoint_uri=RPC_URL))

def read_json(path: str, encoding: str | None = None) -> list | dict:
    return json.load(open(path, encoding=encoding))

not_enough_founds_error_text = "0x9e7762db00000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000006"

async def _create_dict_transaction(wallet_address: str, multiplier: float = 1.1) -> dict:

    await asyncio.sleep(5)

    last_block = await w3.eth.get_block('latest')
    wallet_address = AsyncWeb3.to_checksum_address(wallet_address)
    max_priority_fee_per_gas = await w3.eth.max_priority_fee
    base_fee = int(last_block['baseFeePerGas'] * multiplier)
    max_fee_per_gas = base_fee + max_priority_fee_per_gas

    return {
        'chainId': await w3.eth.chain_id,
        'from': wallet_address,
        'maxPriorityFeePerGas': max_priority_fee_per_gas,
        'maxFeePerGas': max_fee_per_gas,
        'nonce': await w3.eth.get_transaction_count(wallet_address),
    }

async def _send_txn(address: str, txn: dict, private_key, msg: str):
    try:
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)
        txn_hash = await w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"{address} | {msg} | tx: {txn_hash.hex()} | Успешно")
    except Exception as error:
        print(f"{address} | {msg} | {error} | Во время минта произошла ошибка")

async def _create_contract_and_txn(
address: str,
abi_path: str,
wallet_address: str
):
    contract_address = AsyncWeb3.to_checksum_address(address)
    abi = read_json(abi_path)

    return w3.eth.contract(contract_address, abi=abi), await _create_dict_transaction(wallet_address)

async def _mint(private_key, ca: str, price: int):
    try:
        if price > 0:
            msg = 'Минт платной НФТ'
        else:
            msg = "Минт бесплатной НФТ"

        account = w3.eth.account.from_key(private_key)

        contract, dict_transaction = await _create_contract_and_txn(
                ca,
            "./data/abis/mint.json",
                account.address)

        dict_transaction["value"] = w3.to_wei(price, 'ether')

        txn_mint = await contract.functions.claim(
            account.address,
            1,
            AsyncWeb3.to_checksum_address("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"),
            w3.to_wei(price, 'ether'),
            [
                [],
                0,
                115792089237316195423570985008687907853269984665640564039457584007913129639935,
                AsyncWeb3.to_checksum_address("0x0000000000000000000000000000000000000000")
            ],
            b'0x'
        ).build_transaction(dict_transaction)

        await _send_txn(account.address, txn_mint, private_key, msg)

        return True
    except Exception as error:
        address = w3.eth.account.from_key(private_key).address
        if not_enough_founds_error_text in str(error):
            print(
                f"{address} | На этом кошельке уже сминчено максимальное количество НФТ")
            return False
        elif "insufficient funds for gas" in str(error):
            print(
                f"{address} | Недостаточно средств для минта: {round(w3.from_wei(await w3.eth.get_balance(address), 'ether'), 6)}/{price}")
        else:
            print(f"{address} | {error} | Во время создания транзакции произошла ошибка")
        return True


async def mint_nft(private_key: str, nft_type: int):
    if nft_type == 1:
        ca = "0x10cAA985Ef1dfcA51a0CDb33e939e115db0b6C03"
        price = 0
    else:
        ca = "0x529dCdAe937D2F50C9AE79637e1d43f2144F846A"
        price = 0.001
    await _mint(
        private_key,
        ca,
        price
    )

async def process_account(private_key: str):
    free_mints = randint(config.FREE_MINTS[0], config.FREE_MINTS[1])
    chargeable_mints = randint(config.CHARGEABLE_MINTS[0], config.CHARGEABLE_MINTS[1])

    for _ in range(free_mints):
        if not await mint_nft(private_key, 1):
            break
        await asyncio.sleep(uniform(config.DELAY_BETWEEN_MINTS[0], config.DELAY_BETWEEN_MINTS[1]))

    if free_mints:
        await asyncio.sleep(uniform(config.DELAY_BETWEEN_NFTS[0], config.DELAY_BETWEEN_MINTS[1]))

    for _ in range(chargeable_mints):
        if not await mint_nft(private_key, 2):
            break
        await asyncio.sleep(uniform(config.DELAY_BETWEEN_MINTS[0], config.DELAY_BETWEEN_MINTS[1]))

    return
