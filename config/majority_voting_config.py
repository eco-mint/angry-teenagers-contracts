import smartpy as sp

ADMINISTRATOR_ADDRESS = "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"
CONTRACT_METADATA_IPFS_LINK = "ipfs://QmQqaH85s3qBYyMEJLVmLUtv9hgd7cgrheG6mv2Mv1WZD3"

MAIN_MAJ_CONTRACT_NAME = "AngryTeenagersPilot_Dao_Majority"
MAIN_MAJ_DYNAMIC_INIT_VALUE_PERTENMILL = 3000
MAIN_MAJ_GOVERNANCE_PARAMETERS = sp.record(vote_delay_blocks = sp.nat(1),
                                           vote_length_blocks = sp.nat(28800),
                                           supermajority_pertenmill = sp.nat(8000),
                                           fixed_quorum_pertenmill = sp.nat(4000),
                                           fixed_quorum = sp.bool(False),
                                           quorum_cap_pertenmill = sp.record(lower=sp.nat(1000), upper=sp.nat(9000)))



OPTOUT_MAJ_CONTRACT_NAME = "AngryTeenagersPilot_Dao_OptOutMajority"
OPTOUT_MAJ_DYNAMIC_INIT_VALUE_PERTENMILL = 3000
OPTOUT_MAJ_GOVERNANCE_PARAMETERS = sp.record(vote_delay_blocks = sp.nat(1),
                                               vote_length_blocks = sp.nat(28800),
                                               supermajority_pertenmill = sp.nat(5000),
                                               fixed_quorum_pertenmill = sp.nat(2500),
                                               fixed_quorum = sp.bool(True),
                                               quorum_cap_pertenmill = sp.record(lower=sp.nat(1000), upper=sp.nat(9000)))


