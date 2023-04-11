import smartpy as sp

CONTRACT_NAME = "AngryTeenagers DAO"
ADMINISTRATOR_ADDRESS = "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"
CONTRACT_METADATA_IPFS_LINK = "ipfs://QmNVEZ7Afr55pMMEfS7MWqA5zoHLiiMLtcK6sa44MNKzNK"

# TODO: The opt out contract is not added. the majority one is not valid
POLL_MANAGER_INIT_VALUE = sp.map(l = { 0 : sp.record(name=sp.string("MajorityVote"), address=sp.address("KT1XKLLrQW4vsRvzHMnSYiK51uPVfGXLHg9V")),
                                       1: sp.record(name=sp.string("OptOutVote"), address=sp.address("KT1NifZHyuq6FhnrBjKzdCEcJb1bxG8JbCLs"))}, tkey=sp.TNat, tvalue=sp.TRecord(name=sp.TString, address=sp.TAddress))
