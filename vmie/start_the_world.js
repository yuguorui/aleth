#!/usr/bin/env node

const fs = require('fs');
const solc = require('solc');
const Web3 = require('web3');
const Tx = require('ethereumjs-tx').Transaction;
const Common = require('ethereumjs-common').default;
const child_process = require('child_process');

const ADDRESS = "0x000f971B010Db1038D07139fe3b1075B02ceade7";
const PRIVATE_KEY1 = "AAE560E014720F752143833D75ECFAA0A388FBA27C49BA5C8DBC7EB862188EC9";
const PRIVATE_KEY2 = "2701386A48D4F2D5E80E9B3E1D06D48283C386045BC5BA44DCB4F46AF6C053E1";

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function compileAndDeploy(filename, web3, privateKey) {
    const source = fs.readFileSync(filename, 'utf8');
    const input = {
        language: 'Solidity',
        sources: {
            [filename]: { content: source }
        },
        settings: {
            outputSelection: { '*': { '*': ['*'] } }
        }
    };
    const source_address = web3.eth.accounts.privateKeyToAccount(privateKey).address;
    const output = JSON.parse(solc.compile(JSON.stringify(input)));
    for (var contractName in output.contracts[filename]) {
        const contract = output.contracts[filename][contractName];
        const abi = contract.abi;
        const bytecode = contract.evm.bytecode.object;
        const contract_interface = new web3.eth.Contract(abi);

        // Construct the raw transaction
        const gasPrice = await web3.eth.getGasPrice();
        const gasPriceHex = web3.utils.toHex(gasPrice);
        // const gasLimitHex = web3.utils.toHex((await web3.eth.getBlock('latest')).gasLimit);
        const gasLimitHex = web3.utils.toHex(300000);

        const nonce = await web3.eth.getTransactionCount(source_address);
        const nonceHex = web3.utils.toHex(nonce);

        const rawTx = {
            nonce: nonceHex,
            gasPrice: gasPriceHex,
            gasLimit: gasLimitHex,
            data: '0x' + bytecode,
            from: source_address
        };
        console.log(rawTx);

        // Sign and serialize the transaction
        console.log(Common);
        const tx = new Tx(rawTx, {
            common: Common.forCustomChain(
                'mainnet',
                {
                    name: 'my-network',
                    networkId: 0x42,
                    chainId: 0x42,
                },
                'constantinople',
            )
        });
        tx.sign(Buffer.from(privateKey, 'hex'));
        const serializedTx = tx.serialize();

        // Send the transaction
        const receipt = await web3.eth.sendSignedTransaction(serializedTx.toString('hex'))
        console.log(receipt);

        // const deploy_obj = await contract_interface.deploy({
        //     data: bytecode,
        //     arguments: []
        // });
        // const response = await deploy_obj.send({
        //     from: web3.eth.accounts.wallet[account_index].address,
        //     gas: await deploy_obj.estimateGas()
        // });

        // web3.eth.accounts.signTransaction(rawTx, privateKey).then(signed => {
        //     web3.eth.sendSignedTransaction(signed.rawTransaction).on('receipt', console.log)
        // });

        // console.log(response) // instance with the new contract address
    }
}

async function main() {
    try {
        // start docker-compose
        // child_process.execSync('docker-compose up -d');
        // await sleep(3000);

        // deploy the contract
        const web3 = new Web3();
        web3.setProvider(new web3.providers.HttpProvider('http://localhost:8545'));

        // add account to wallet address
        await web3.eth.accounts.wallet.add(PRIVATE_KEY1);
        await web3.eth.accounts.wallet.add(PRIVATE_KEY2);

        // deploy contract with 0th account.
        await compileAndDeploy('./deployer.sol', web3, PRIVATE_KEY2);
    } catch (error) {
        console.log('error,', error);
    } finally {
        // child_process.execSync('docker-compose down');
    }
}

main();
// compileAndDeploy('./deployer.sol');
