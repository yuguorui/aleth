pragma solidity ^0.6.1;

contract Deployer {
    uint public haha;

    constructor() public {
        haha = 1;
    }

    function deploy() public returns (address) {
      address addr;
      assembly {
        addr := create2(0, 0, 0, 0xFFFFFFFFFFFFFFFF)
      }
      return addr;
    }

    function echo(uint num) public returns (uint) {
        return num;
    }

    function renderHelloWorld() public returns (uint) {
        return 42;
    }
}

// contract test {
//     function f(uint256 a) public returns (uint256 d) {
//         return a * 7;
//     }
// }
