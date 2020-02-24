pragma solidity ^0.5.1;

contract Deployer {

    event Result(address con);

    constructor() public {
      emit Result(0x000f971B010Db1038D07139fe3b1075B02ceade7);
      address addr;
      assembly {
        addr := create2(0, 0, 0, 0x20000000)
      }
      emit Result(addr);
    }
}