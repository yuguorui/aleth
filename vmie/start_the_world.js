#!/usr/bin/env node

const fs = require('fs');
const solc = require('solc');
const Web3 = require('web3');
const child_process = require('child_process');
const process = require('process');

const ADDRESS = "0x000f971B010Db1038D07139fe3b1075B02ceade7";

// 需要在私钥前加入0x，以避免生成错误地址。
const PRIVATE_KEY1 = "0xAAE560E014720F752143833D75ECFAA0A388FBA27C49BA5C8DBC7EB862188EC9";
const PRIVATE_KEY2 = "0x2701386A48D4F2D5E80E9B3E1D06D48283C386045BC5BA44DCB4F46AF6C053E1";

// process.on('SIGINT', () => {
//     console.log("Caught interrupt signal");
//     child_process.execSync('docker-compose down');
//     process.exit();
// });

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
            outputSelection: { '*': { '*': ['*'] } },
            evmVersion: "constantinople"
        }
    };
    const account = web3.eth.accounts.privateKeyToAccount(private_key);
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

        const signedData = await account.signTransaction({
            data: deploy_template.encodeABI(),
            // gas: web3.utils.toHex(await deploy_template.estimateGas()),
            gas: 300000,
            common: {
                customChain: {
                    networkId: 0x42,
                    chainId: 0x42
                },
                hardfork: 'constantinople'
            },
            chainId: '0x42'
        });

        // Send the transaction
        const receipt = await web3.eth.sendSignedTransaction(signedData.rawTransaction);
        receipts.push({ 'receipt': receipt, 'abi': abi });

    }
    return receipts;
}

async function methodSend(web3, address, abi, private_key, method_name, ...args) {
    const account = web3.eth.accounts.privateKeyToAccount(private_key);
    const contract_interface = new web3.eth.Contract(abi, address);
    const method_template = contract_interface.methods[method_name](...args);
    console.log(method_template.encodeABI());

    const rawData = {
        to: address,
        data: method_template.encodeABI(),
        // gas: web3.utils.toHex(await method_template.estimateGas()),
        gas: 300000,
        common: {
            customChain: {
                networkId: 0x42,
                chainId: 0x42
            },
            // hardfork: 'constantinople'
        },
        chainId: '0x42'
    };

    const signedData = await account.signTransaction(rawData);
    const receipt = await web3.eth.sendSignedTransaction(signedData.rawTransaction);
    return receipt;
}

async function methodCall(web3, address, abi, method_name, ...args) {
    // console.log(abi);
    const contract_interface = new web3.eth.Contract(abi, address);
    // web3.eth.defaultBlock = 1;
    // console.log(contract_interface.methods.renderHelloWorld().encodeABI());
    return await contract_interface.methods[method_name]().call();
}

async function main() {
    try {
        // start docker-compose
        // const cmd = child_process.spawn('docker-compose', ['up']);
        // cmd.stdout.on('data', (msg) => { process.stdout.write(msg.toString()) });
        // cmd.stderr.on('data', (msg) => { process.stdout.write(msg.toString()) });
        // await sleep(6000);

        // deploy the contract
        const web3 = new Web3();
        web3.setProvider(new web3.providers.HttpProvider('http://localhost:8545'));
        const deploy_receipt = (await compileAndDeploy('./deployer.sol', web3, PRIVATE_KEY1))[0];

        console.log(deploy_receipt);
        // console.log(await methodCall(web3, deploy_receipt.receipt.contractAddress, deploy_receipt.abi, 'renderHelloWorld()'));
        // console.log(await methodSend(web3, deploy_receipt.receipt.contractAddress, deploy_receipt.abi, PRIVATE_KEY1, 'deploy()'));
        console.log('====================================================================================================');
        console.log(deploy_receipt.receipt.logs);
        // console.log(await web3.eth.call({
        //     to: deploy_receipt.receipt.contractAddress,
        //     data: "0x942ae0a7",
        //     from: ADDRESS,
        //     common: {
        //         customChain: {
        //             networkId: 0x42,
        //             chainId: 0x42
        //         },
        //         hardfork: 'constantinople'
        //     },
        //     chainId: '0x42'
        // }));

        // console.log(await web3.eth.getCode(deploy_receipt.receipt.contractAddress));
        // console.log(await web3.eth.getTransactionFromBlock(deploy_receipt.receipt.blockHash, 0));

        // {
        //     const account = web3.eth.accounts.privateKeyToAccount(PRIVATE_KEY1);
        //     const contract_interface = new web3.eth.Contract(deploy_receipt.abi, deploy_receipt.receipt.contractAddress);
        //     const method_template = contract_interface.methods.deploy();
        //     console.log(method_template.encodeABI());

        //     const rawTx = {
        //         to: deploy_receipt.receipt.contractAddress,
        //         data: method_template.encodeABI(),
        //         gas: 300000,
        //         common: {
        //             customChain: {
        //                 networkId: 0x42,
        //                 chainId: 0x42
        //             },
        //             hardfork: 'constantinople'
        //         },
        //         chainId: '0x42'
        //     };
        //     console.log('rawTx', rawTx);
        //     const signedData = await account.signTransaction(rawTx);
        //     const receipt = await web3.eth.sendSignedTransaction(signedData.rawTransaction);
        //     console.log(receipt);
        // }
    } catch (error) {
        console.log('error,', error);
    } finally {
        // child_process.execSync('docker-compose down');
    }
}

main();
// compileAndDeploy('./deployer.sol');
