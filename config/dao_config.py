import smartpy as sp

CONTRACT_NAME = "AngryTeenagers DAO"
ADMINISTRATOR_ADDRESS = "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"
CONTRACT_METADATA_IPFS_LINK = "ipfs://Qmdv2pjNJfhzga6tGf7cG83STZwo81rSoLwPsFXGGKioR1"

# TODO: The opt out contract is not added. the majority one is not valid
POLL_MANAGER_INIT_VALUE = sp.map(l = { 0 : sp.record(name=sp.string("MajorityVote"), address=sp.address("KT1Vk3GjhwHP732NcVBRT6yNmoAxy2Jyh81G")),
                                       1: sp.record(name=sp.string("OptOutVote"), address=sp.address("KT1CBeoEjK9gHmifS7W71HoNddoLD9hv1HxE"))}, tkey=sp.TNat, tvalue=sp.TRecord(name=sp.TString, address=sp.TAddress))
