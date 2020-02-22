#!/usr/bin/env node

const fs = require('fs');
const solc = require('solc');
const Web3 = require('web3');
const Tx = require('ethereumjs-tx').Transaction;
const Common = require('ethereumjs-common').default;
const child_process = require('child_process');
const process = require('process');

const ADDRESS = "0x000f971B010Db1038D07139fe3b1075B02ceade7";
const PRIVATE_KEY1 = "AAE560E014720F752143833D75ECFAA0A388FBA27C49BA5C8DBC7EB862188EC9";
const PRIVATE_KEY2 = "2701386A48D4F2D5E80E9B3E1D06D48283C386045BC5BA44DCB4F46AF6C053E1";

process.on('SIGINT', () => {
    console.log("Caught interrupt signal");
    child_process.execSync('docker-compose down');
    process.exit();
});

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function compileAndDeploy(filename, web3, private_key) {
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
    const source_address = web3.eth.accounts.privateKeyToAccount(private_key).address;
    const output = JSON.parse(solc.compile(JSON.stringify(input)));

    const receipts = [];
    for (var contractName in output.contracts[filename]) {
        const contract = output.contracts[filename][contractName];
        const abi = contract.abi;
        const bytecode = contract.evm.bytecode.object;

        // 因为服务器缺乏一些特定的RPC调用接口，所以在本地签名后再发送交易。
        // Construct the raw transaction
        const conrtact_template = new web3.eth.Contract(abi);
        const deploy_template = conrtact_template.deploy({ data: '0x' + bytecode });
        console.log(await web3.eth.getTransactionCount(source_address));
        const rawTx = {
            from: source_address,
            nonce: web3.utils.toHex(await web3.eth.getTransactionCount(source_address)),
            data: deploy_template.encodeABI(),
            gasPrice: web3.utils.toHex(await web3.eth.getGasPrice()),
            gasLimit: web3.utils.toHex(await deploy_template.estimateGas())

        };
        console.log(rawTx);

        // Sign and serialize the transaction
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
        tx.sign(Buffer.from(private_key, 'hex'));
        const serializedTx = tx.serialize();

        // Send the transaction
        const receipt = await web3.eth.sendSignedTransaction(serializedTx.toString('hex'));
        receipts.push({ 'receipt': receipt, 'abi': abi });
    }
    return receipts;
}

async function callContractMethod(address, abi, private_key, method_name, ...args) {
    const source_address = web3.eth.accounts.privateKeyToAccount(private_key).address;
    const contract_interface = new web3.eth.Contract(abi);
    const method_template = contract_interface.methods[method_name](args);
    const rawTx = {
        from: source_address,
        to: address,
        nonce: web3.utils.toHex(await web3.eth.getTransactionCount(source_address, 'pending')),
        data: method_template.encodeABI(),
        gasPrice: web3.utils.toHex(await web3.eth.getGasPrice()),
        gasLimit: web3.utils.toHex(await method_template.estimateGas())
    };
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
    tx.sign(Buffer.from(private_key, 'hex'));
    const serializedTx = tx.serialize();
    const receipt = await web3.eth.sendSignedTransaction(serializedTx.toString('hex'));
}

async function main() {
    try {
        // start docker-compose
        const cmd = child_process.spawn('docker-compose', ['up']);
        cmd.stdout.on('data', (msg) => { process.stdout.write(msg.toString()) });
        cmd.stderr.on('data', (msg) => { process.stdout.write(msg.toString()) });
        await sleep(6000);

        // deploy the contract
        const web3 = new Web3();
        web3.setProvider(new web3.providers.HttpProvider('http://localhost:8545'));
        console.log(await compileAndDeploy('./deployer.sol', web3, PRIVATE_KEY2));
        await sleep(10000);
        console.log(await compileAndDeploy('./deployer.sol', web3, PRIVATE_KEY2));
    } catch (error) {
        console.log('error,', error);
    } finally {
        child_process.execSync('docker-compose down');
    }
}

main();
// compileAndDeploy('./deployer.sol');
