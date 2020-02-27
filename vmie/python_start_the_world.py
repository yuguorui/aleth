#!/usr/bin/env python3.8

import json
import time
import os
import re
from shutil import rmtree
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Process, Queue
from threading import Thread, Lock

# from web3.auto import w3
from web3 import Web3, HTTPProvider, IPCProvider, WebsocketProvider
from solc import compile_standard

from eth_account.account import Account

##################### Constant #####################
ADDRESS1 = "0x000f971B010Db1038D07139fe3b1075B02ceade7"
PRIVATE_KEY1 = "0xAAE560E014720F752143833D75ECFAA0A388FBA27C49BA5C8DBC7EB862188EC9"
PRIVATE_KEY2 = "0x2701386A48D4F2D5E80E9B3E1D06D48283C386045BC5BA44DCB4F46AF6C053E1"

##################### Compile contract #####################
file_name = 'deployer.sol'
contract_name = 'Deployer'
print(f'[!] Start compile "{file_name}" file')
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
print(f'[!] abi: {abi}')


##################### Start client and deploy the contract #####################

ansi_escape_8bit = re.compile(
    r'(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])'
)


Node_ID = ''
CritialBlockNumber = -1

def start_and_deploy(lock):
    lock.acquire()
    while True:
        global Node_ID
        print('## 1. clean the environment')
        os.system('rm -rf .ethereum')
        os.system('rm -rf ./aleth.log.txt')
        print('## 2. Start the client...')
        cli_args = '../build/eth/eth --config config.json --no-discovery --json-rpc-port 8545 --db-path .ethereum --listen 30303 -m on -v 9 -a 000f971b010db1038d07139fe3b1075b02ceade7 --unsafe-transactions -t 2'.split(' ')
        process = Popen(cli_args, bufsize=1, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
        
        ## 3. create a new process and connect to client
        time.sleep(3)
        q = Queue()
        deployer = Process(target=connect_to_client, args=(q,))
        deployer.start()
        ## 4. check for invalid block
        while(True):
            line = ansi_escape_8bit.sub('', process.stdout.readline())
            with open('./aleth.log.txt', 'a') as f:
                f.write(line)
            if lock.locked() and deployer.exitcode is not None:
                lock.release()
                print('Event:', q.get())
            if 'Node ID' in line:
                Node_ID = re.search('//(.*)@', line).group(1)
                print(f'[.] Node id: {Node_ID}')
            if 'Import Failure' in line:
                print('[!] Detected invalid block, restart...')
                deployer.terminate()
                process.terminate()
                time.sleep(3)
                break
    

def connect_to_client(q):
    global CritialBlockNumber
    print('## 3. connect to the client...')
    w3 = Web3(HTTPProvider('http://localhost:8545'))
    person1 = Account().from_key(PRIVATE_KEY1)
    assert(person1.address == ADDRESS1)
    rawTx = dict(
            chainId=0x42,
            nonce=w3.eth.getTransactionCount(person1.address),
            gasPrice=w3.eth.gasPrice,
            gas=3000000,
            data=bytecode,
            )
    # print(rawTx)
    signed_txn = person1.sign_transaction(rawTx)

    connected = w3.isConnected()
    assert(connected)
    trans_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    print('## 4. Wait for the receipt...')
    receipt = w3.eth.waitForTransactionReceipt(trans_hash)
    print(f'Contract address: {receipt.contractAddress}, blocknumber: {w3.eth.blockNumber}')
    assert(len(receipt.logs) >= 1)
    q.put(receipt.logs[0])


lock1 = Lock()
t1 = Thread(target=start_and_deploy, args=(lock1,))
t1.start()
# print(lock1.locked())
lock1.acquire()

##################### Start another client #####################
print('## 5. clean the environment')
os.system('rm -rf .ethereum2')
os.system('rm -rf ./aleth2.log.txt')
print('## 6. Start another client...')
time.sleep(10)
# cli_args = '../build/eth/eth --config config.json --no-discovery --json-rpc-port 9545 --listen 30305 --db-path .ethereum2 --allow-local-discovery -v 5 -m on -t 2'.format(Node_ID).split(' ')
cli_args = '../build/eth/eth --config config.json --no-discovery --json-rpc-port 9545 --listen 30305 --db-path .ethereum2 --peerset required:{}@127.0.0.1:30303 -v 5 -m on -t 2'.format(Node_ID).split(' ')
print(cli_args)
process = Popen(cli_args, bufsize=0, stdout=PIPE, stderr=STDOUT, universal_newlines=True)

while True:
    line = ansi_escape_8bit.sub('', process.stdout.readline())
    with open('./aleth2.log.txt', 'a') as f:
        f.write(line)
    if 'Import Failure' in line:
        print('[!] Found import error in client 2')
        break

print()
w3_1 = Web3(HTTPProvider('http://localhost:8545'))
w3_2 = Web3(HTTPProvider('http://localhost:9545'))
while True:
    try:
        time.sleep(3)
        print('client1:', w3_1.eth.mining, ', Height:', w3_1.eth.blockNumber)
        print('client2:', w3_2.eth.mining, ', Height:', w3_2.eth.blockNumber)
    except Exception as e:
        print(e)
