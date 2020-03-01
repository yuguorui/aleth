#!/usr/bin/env python3.8

import os
import re
import asyncio

from web3 import Web3, HTTPProvider, IPCProvider, WebsocketProvider

################## Constant ##################
Node_IDs = [
    '2930fe0f124286817a9c23064defe90ed48f12397ec11f88e35ee15e1bb9ec5269d0833e2e067b34687fb82506f54aa88b0c8ce3ee7e922813f431dab33bae59',
    '5f21c6db21b95b276ea37f4491cd0ca87fb81ec8de8a80fab45961442551646dcf540fd580c60ae9863d224b38bbe6e71bd868e6baa926014409369922925519',
    '6e7eab31df4c8a5ad5567682fb1e01aecee077986cbb4ab4917b94904aba932b9976e2aa72255fbcb64a6f28979f0ea18a04b932854b8c81905f65199e92f25b',
    '442ec45a32a9b59dcbaba0aa40434d21050d043b2a57f0b0ac2e7a1ce2693cf5af15ade71baebeaf2dcc02ed4f45538f85873f2d595ca7a99ff00302f361471b',
    '3c61375bdb09ec77f8df4ad4de9165014262abea0459ccce1edb3112666f3f9291169656ec71b9fc72faa31c2b94abeb4f858a484d33f4d4f504875b5b55b844'
]
NUM = len(Node_IDs)

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


def generate_callback(filename):
    def callback(line):
        line = line.decode('utf-8')
        line = ansi_escape_8bit.sub('', line)
        with open(filename, 'a') as f:
            f.write(line)
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
    execute(cmd, generate_callback(f'aleth{i}.log.txt'), generate_callback(f'aleth{i}.log.txt'))

print('## 3. Connect to RPC...')
web3s = [Web3(HTTPProvider(f'http://localhost:{8545+i}')) for i in range(1, NUM+1)]
async def watch_blocks():
    await asyncio.sleep(5)
    while True:
        print('Height:', [web3.eth.blockNumber for web3 in web3s], end='\r')
        await asyncio.sleep(1)
loop.create_task(watch_blocks())

loop.run_forever()
