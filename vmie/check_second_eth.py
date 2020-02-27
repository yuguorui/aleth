#!/usr/bin/env python3.8

##########################################
from web3 import Web3, HTTPProvider, IPCProvider, WebsocketProvider
w3 = Web3(HTTPProvider('http://localhost:9545'))
while True:
    print('********************')
    print('blocknumber:', w3.eth.blockNumber)
    receipt = w3.eth.waitForTransactionReceipt(trans_hash)
    print([log['data'] for log in receipt.logs])
    time.sleep(3)
