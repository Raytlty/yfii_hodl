import json
import time
from web3 import Web3, HTTPProvider

provider = "https://mainnet.infura.io/v3/bda996b482e944bdbd5bad497e8f7205"
web3 = Web3(HTTPProvider(provider))

factory_addr = "0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd"
proxy_addr = "0x6317C5e82A06E1d8bf200d21F4510Ac2c038AC81"
weth_addr = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
multicall_addr = "0xeefBa1e63905eF1D7ACbA5a8513c70307C1cE441"
dai_token = Web3.toChecksumAddress("0x6b175474e89094c44da98b954eedeac495271d0f")
yfii_token = "0xa1d0E215a23d7030842FC67cE582a6aFa3CCaB83"


pool_abi = json.load(open('abi/BPool.json'))['abi']
erc20_abi = json.load(open('abi/erc20.json'))
pool_addr = "0x16cAC1403377978644e78769Daa49d8f6B6CF565"
yfii_ex = web3.eth.contract(pool_addr, abi=pool_abi)
dai = web3.eth.contract(dai_token, abi=erc20_abi)
yfii = web3.eth.contract(yfii_token, abi=erc20_abi)

gas_price = Web3.toWei(50, "gwei")

def get_balance(address):
    b1 = dai.functions.balanceOf(address).call()
    b2 = yfii.functions.balanceOf(address).call()
    return Web3.fromWei(b1, "ether"), Web3.fromWei(b2, "ether")

def get_price():
    price = yfii_ex.functions.getSpotPrice(dai_token, yfii_token).call()
    price = Web3.fromWei(price, "ether")
    # print(price)
    return price

def watch(privkey, address, price, amount):
    # check allowance
    allowance = dai.functions.allowance(Web3.toChecksumAddress(address), pool_addr).call()
    print('DAI allowance:', allowance)
    if allowance < Web3.toWei(price * amount * 1.05, 'ether'):
        # dai approve
        print('approving dai...')
        tx = dai.functions.approve(pool_addr, 2**256-1).buildTransaction({
            "chainId": 1,
            "from": Web3.toChecksumAddress(address),
            "value": 0,
            "gasPrice": gas_price,
            "gas": 300000,
            "nonce": web3.eth.getTransactionCount(Web3.toChecksumAddress(address))
            })
        signed_tx = web3.eth.account.sign_transaction(tx, privkey)
        txhash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print('txhash:', txhash.hex())
        print('waiting for receipt...')
        receipt = web3.eth.waitForTransactionReceipt(txhash, timeout=100000)
        print('receipt:', receipt)
    print("=========start watching========")

    while 1:
        b1, b2 = get_balance(address)
        p = get_price()
        print(f"DAI balance:{b1}, YFII balance:{b2}, price:{p}")
        if p < price:
            print("buying YFII...")
            # buy YFII, allow slippage 0.005
            maxAmountIn = Web3.toWei(price * amount * 1.005, "ether")
            minAmountOut = Web3.toWei(amount, "ether")
            maxPrice = Web3.toWei(price * 1.005, "ether")
            tx = yfii_ex.functions.swapExactAmountOut(dai_token, maxAmountIn, yfii_token, minAmountOut, maxPrice).buildTransaction({
                "chainId": 1,
                "from": Web3.toChecksumAddress(address),
                "value": 0,
                "gasPrice": gas_price, 
                "gas": 300000,
                "nonce": web3.eth.getTransactionCount(Web3.toChecksumAddress(address))
                })
            signed_tx = web3.eth.account.sign_transaction(tx, privkey)
            txhash = None
            try:
                txhash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
            except Exception as e:
                print('sendTx failed:', e)
            if txhash:
                print('txhash:', txhash.hex())
                print('waiting for receipt...')
                receipt = web3.eth.waitForTransactionReceipt(txhash, timeout=100000)
                print('receipt:', receipt)
                exit()
        time.sleep(5)

if __name__ == "__main__":
    print("YFII to the moon!")
    privkey = input("your private key:")
    address = input("your address:")
    price = float(input("buy price(DAI):"))
    amount = float(input("buy amount(YFII):"))
    gas = float(input("gas price(GWEI, default 50):"))
    gas_price = Web3.toWei(gas, 'gwei')
    watch(privkey, address, price, amount)
