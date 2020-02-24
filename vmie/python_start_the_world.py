#!/usr/bin/env python3.8

import json

from web3.auto import w3
from solc import compile_standard

from eth_account.account import Account

file_name = 'deployer.sol'
contract_name = 'Deployer'
print(f'Start compile {file_name} file')
with open(file_name) as f:
    compiled_sol  = compile_standard({
        "language": "Solidity",
        "sources": {
            file_name: {
                'content': f.read()
                }
            },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": [
                        "metadata", "evm.bytecode"
                        , "evm.bytecode.sourceMap"
                        ]
                    }
                },
            'evmVersion': "constantinople"
            }
        })
bytecode = compiled_sol['contracts'][file_name][contract_name]['evm']['bytecode']['object']
abi = json.loads(compiled_sol['contracts'][file_name][contract_name]['metadata'])['output']['abi']
print(f'abi: {abi}')


ADDRESS1 = "0x000f971B010Db1038D07139fe3b1075B02ceade7";
PRIVATE_KEY1 = "0xAAE560E014720F752143833D75ECFAA0A388FBA27C49BA5C8DBC7EB862188EC9";
PRIVATE_KEY2 = "0x2701386A48D4F2D5E80E9B3E1D06D48283C386045BC5BA44DCB4F46AF6C053E1";

person1 = Account().from_key(PRIVATE_KEY1)
assert(person1.address == ADDRESS1)
rawTx = dict(
        chainId=0x42,
        nonce=w3.eth.getTransactionCount(person1.address),
        gasPrice=w3.eth.gasPrice,
        gas=300000,
        data=bytecode,
        )
# print(rawTx)
signed_txn = person1.sign_transaction(rawTx)

connected = w3.isConnected()
assert(connected)

trans_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction) 
receipt = w3.eth.waitForTransactionReceipt(trans_hash)
print(f'Contract address: {receipt.contractAddress}')
print("=====================\nEvents:")
for log in receipt.logs:
    print(log['data'])
