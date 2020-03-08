#!/usr/bin/env python3

import os
import re
import asyncio
import json

from web3 import Web3, HTTPProvider, IPCProvider, WebsocketProvider
from eth_account.account import Account
from solc import compile_standard

################## Constant ##################
Node_IDs = [
    '079b30b7845e904c1dfc70b4734040c476ed22cc7280637604d4c35577b83ae964f8a03a705eb36afb325f46ce6e5ade0973b1fdfb68ee40a5a1c12178e89708',
    '90a47987787deaa0ff877f06d53961e164eb5593bb224dcdcbb897f91f9ece7547116f07bbaa04171ede587d31f96f2b230fe2d58159dbe1f6b0d4d39044607f',
    'cd9a2eff4fa3c8d00d7b6c837bb8ddb2dd27a798ada724131b16a3b776bcea52a6f3cf1ea4fc3a43153a5f7043f842402f77acfce22b00858dcabd9d733917a6',
    '2efc9ac40493033eaacecd0a0b0f58fa98f5d3eac546d321172298a4ea3ddfa48befd9258b1fd9d759688148649369e39c2e2d0638b245fc61768bd98999924a',
    'a1e2537e0d48122878d887875edfd36498cfd745d439feb33dfe70ddeccbe28131943b832d6686348549d91a6d25b4f5fa61479acea26e683b63520a166ca560'
]
NUM = len(Node_IDs)

ADDRESS1 = "0x000f971B010Db1038D07139fe3b1075B02ceade7"
PRIVATE_KEY1 = "0xAAE560E014720F752143833D75ECFAA0A388FBA27C49BA5C8DBC7EB862188EC9"

################## Clean Environment ##################
print("## 1. Clean the environment...")
for i in range(1, NUM+1):
    os.system(f"find .ethereum{i} ! -name .ethereum{i} ! -name 'network.rlp' -exec rm -rf {{}} +")

################## Start the process ##################
ansi_escape_8bit = re.compile(r'(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~])')

async def _read_stream(stream, cb):  
    while True:
        line = await stream.readline()
        if line:
            cb(line)
        else:
            break

async def _stream_subprocess(cmd, stdout_cb, stderr_cb):  
    process = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    await asyncio.gather(
        _read_stream(process.stdout, stdout_cb),
        _read_stream(process.stderr, stderr_cb)
        )
    return await process.wait()


loop = asyncio.get_event_loop()
def execute(cmd, stdout_cb, stderr_cb):  
    return loop.create_task(_stream_subprocess(
            cmd,
            stdout_cb,
            stderr_cb,
    ))


restartLock = asyncio.Lock()
restartLock.acquire()
def generate_callback(filename, instance_id):
    def callback(line):
        line = line.decode('utf-8')
        line = ansi_escape_8bit.sub('', line)
        with open(filename, 'a') as f:
            f.write(line)
        if instance_id == 1 and 'Import Failure' in line:
            print('[!] Detected invalid block, redeploy the contract...')
            # restartLock.release()
    return callback

print('## 2. Start all the instance...')
for i in range(1, NUM+1):
    cmd = f'../build/eth/eth --config config.json --no-discovery --json-rpc-port {8545+i} --db-path .ethereum{i} --listen {30303+i} -m on -v 5 -a 000f971b010db1038d07139fe3b1075b02ceade7 -t 1 --peerset'.split(' ')
    peersets = []
    for j, node_id in enumerate(Node_IDs, 1):
        if j == i:
            continue
        peersets.append(f'required:{node_id}@127.0.0.1:{30303+j}')
    cmd.append(' '.join(peersets))
    execute(cmd, generate_callback(f'aleth{i}.log.txt', i), generate_callback(f'aleth{i}.log.txt', i))

print('## 3. Connect to RPC...')
web3s = [Web3(HTTPProvider(f'http://localhost:{8545+i}')) for i in range(1, NUM+1)]
async def watch_blocks():
    await asyncio.sleep(5)
    while True:
        print('Height:', [web3.eth.blockNumber for web3 in web3s])# , end='\r')
        await asyncio.sleep(1)
loop.create_task(watch_blocks())

print("### 4. Compile the contract...")
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


async def try_deploy_contract():
    print("### 5. Deploy the contract...")
    await asyncio.sleep(7)
    while True:
        try:
                print('## 6. connect to the client...')
                w3 = Web3(HTTPProvider('http://localhost:8546'))
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
                return w3.eth.waitForTransactionReceipt(trans_hash)
        except asyncio.CancelledError:
            print("[!] Task canceled...restarting")
            continue
        else:
            break
loop.create_task(try_deploy_contract())


loop.run_forever()
