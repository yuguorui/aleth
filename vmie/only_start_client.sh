#!/bin/bash
set -e

echo "Clear history blocks..."
rm -rf ~/.ethereum

echo "Start eth client..."
../build/eth/eth --config config.json --no-discovery \
    -v 5 -m on -a 000f971b010db1038d07139fe3b1075b02ceade7 \
    --unsafe-transactions -j --rpccorsdomain '*' -t 2 \
    --listen 30303 2>&1 | \
    stdbuf -o 0 sed -r "s/[[:cntrl:]]\[[0-9]{1,3}m//g" | \
    stdbuf -o 0 grep -v 'Generating' | \
    stdbuf -o 0 grep -v 'Rejigging' |\
    tee miner.out.txt
