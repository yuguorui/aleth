pragma solidity ^0.6.1;

contract Deployer {
    function deploy() public {
      address addr;
      assembly {
        addr := create2(0, 0, 0, 0xFFFFFFFFFFFFFFFF)
      }
    }
    function renderHelloWorld() public pure returns (string memory) {
        return "helloWorld";
    }
}
