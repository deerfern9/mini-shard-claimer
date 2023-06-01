import requests
from web3 import Web3
from colorama import Fore, init
from eth_account.messages import encode_defunct
init()

contract_address = '0x1bC274C3b3b24ceF54d01AEEB9fFc73Ac0b68936'
gwei = float(input('Enter gwei amount: '))
web3 = Web3(Web3.HTTPProvider("https://bsc.blockpi.network/v1/rpc/public"))

headers = {
    'authority': 'api.cyberconnect.dev',
    'accept': '*/*',
    'accept-language': 'en-GB,en;q=0.9,uk-UA;q=0.8,uk;q=0.7,ru-RU;q=0.6,ru;q=0.5,en-US;q=0.4',
    'content-type': 'application/json',
    'origin': 'https://link3.to',
    'referer': 'https://link3.to/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
}


def read_file(filename):
    result = []
    with open(filename, 'r') as file:
        for tmp in file.readlines():
            result.append(tmp.replace('\n', ''))

    return result


def write_to_file(filename, text):
    with open(filename, 'a') as file:
        file.write(f'{text}\n')


def get_nonce(address, proxy):
    json_data = {
        'query': '\n    mutation nonce($address: EVMAddress!) {\n  nonce(request: {address: $address}) {\n    status\n    message\n    data\n  }\n}\n    ',
        'variables': {
            'address': address,
        },
        'operationName': 'nonce',
    }

    response = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=json_data, proxies=proxy)
    nonce = response.json()['data']['nonce']['data']
    return nonce


def sign_signature(private_key, message):
    message_hash = encode_defunct(text=message)
    signed_message = web3.eth.account.sign_message(message_hash, private_key)

    signature = signed_message.signature.hex()
    return signature


def get_auth_token(address, message, signature, proxy):
    json_data = {
        'query': '\n    mutation login($address: EVMAddress!, $signature: String!, $signedMessage: String!, $token: String, $isEIP1271: Boolean, $chainId: Int) {\n  login(\n    request: {address: $address, signature: $signature, signedMessage: $signedMessage, token: $token, isEIP1271: $isEIP1271, chainId: $chainId}\n  ) {\n    status\n    message\n    data {\n      id\n      privateInfo {\n        address\n        accessToken\n        kolStatus\n      }\n    }\n  }\n}\n    ',
        'variables': {
            'signedMessage': message,
            'token': '',
            'address': address,
            'chainId': 56,
            'signature': signature,
            'isEIP1271': False,
        },
        'operationName': 'login',
    }

    resp = requests.post('https://api.cyberconnect.dev/profile/', headers=headers, json=json_data, proxies=proxy).json()
    token = resp['data']['login']['data']['privateInfo']['accessToken']
    return token


def claim_mini_shard_data(authorization, private, proxy):
    headers_claim = {
        'authority': 'api.cyberconnect.dev',
        'accept': '*/*',
        'authorization': authorization,
        'content-type': 'application/json',
        'origin': 'https://link3.to',
        'referer': 'https://link3.to/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    json_data = {
        'query': '\n    mutation claimMiniShard {\n  claimMiniShard {\n    status\n    tokenId\n    amount\n    signature\n    deadline\n  }\n}\n    ',
        'operationName': 'claimMiniShard',
    }

    response = requests.post('https://api.cyberconnect.dev/profile/', headers=headers_claim, json=json_data, proxies=proxy).json()
    data = response['data']['claimMiniShard']
    if data['status'] == 'SUCCESS':
        signature = data['signature']
        predata = signature[-2:]+signature[2:-2]
        deadline_hex = hex(int(data['deadline']))
        amount = data['amount']
        print(f'[{private}] Status: {data["status"]}; Amount: {amount}; Deadline: {deadline_hex}; predata: {predata};')
        return predata, deadline_hex[2:], amount
    else:
        print(f'[{private}] Status: {data["status"]}')
        return None, None, None


def claim_mini_shard(private, address, predata, amount,  hex_deadline):
    data = f'0x5e7da5a3000000000000000000000000{address[2:]}0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000{amount}000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000{predata}00000000000000000000000000000000000000000000000000000000{hex_deadline}0000000000000000000000000000000000000000000000000000000000000000'
    # data = '0x5e7da5a3000000000000000000000000C1a1D96b46CcAe51888589919B69C4bD6D083cb60000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000{amount}0000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001c7f0a0045139bf8dc576b7a7f48c9c9710fb73d5387e93f1abbe5595f4e405812542f8b1a02d4bfe9f90e5973c739dab7f11f6debae4dd9ebc035ca9b45616fe800000000000000000000000000000000000000000000000000000000645d0c880000000000000000000000000000000000000000000000000000000000000000'
    nonce = web3.eth.getTransactionCount(address)
    try:
        tx_create = web3.eth.account.sign_transaction({
            'to': contract_address,
            'value': 0,  # Set value if needed
            'gas': 150000,  # Set an appropriate gas limit for the transaction
            'gasPrice': web3.toWei(gwei, 'gwei'),
            'nonce': nonce,
            'data': data,
        },
            private
        )
        tx_hash = web3.eth.sendRawTransaction(tx_create.rawTransaction)
        write_to_file('hashes.txt', tx_hash.hex())
        print(f"[{private}] Transaction hash: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        write_to_file('ERRORS.txt', f'{private}:{address}:{e}')


def main():
    for i, wallet_info in enumerate(read_file('private;proxy.txt')):
        if i % 2 == 0:
            print(Fore.BLUE, end='')
        else:
            print(Fore.GREEN, end='')
        private, proxy = wallet_info.split(';')
        address = web3.eth.account.privateKeyToAccount(private).address
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        nonce = get_nonce(address, proxies)
        message = f'''link3.to wants you to sign in with your Ethereum account:\n{address}\n\n\nURI: https://link3.to\nVersion: 1\nChain ID: 56\nNonce: {nonce}\nIssued At: 2023-03-19T14:04:18.580Z\nExpiration Time: 2023-04-02T14:04:18.580Z\nNot Before: 2023-03-19T14:04:18.580Z'''
        sign = sign_signature(private, message)
        authorization = get_auth_token(address, message, sign, proxies)
        predata, deadline, amount = claim_mini_shard_data(authorization, private, proxies)
        if not predata:
            continue
        claim_mini_shard(private, address, predata, amount, deadline)


if __name__ == '__main__':
    main()
