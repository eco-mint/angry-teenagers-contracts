import smartpy as sp

ADMINISTRATOR_ADDRESS = "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"
CONTRACT_METADATA_IPFS_LINK = "ipfs://QmNtph2DjrVcK9KXrNRsPSwMPpBpZjY7Ti6ceNcrbor45n"

MAIN_MAJ_CONTRACT_NAME = "AngryTeenagers Majority voting"
MAIN_MAJ_DYNAMIC_INIT_VALUE = 2000
MAIN_MAJ_GOVERNANCE_PARAMETERS = sp.record(vote_delay_blocks = sp.nat(1),
                                           vote_length_blocks = sp.nat(14400),
                                           percentage_for_supermajority = sp.nat(80),
                                           fixed_quorum_percentage = sp.nat(25),
                                           fixed_quorum = sp.bool(False),
                                           quorum_cap = sp.record(lower=sp.nat(1), upper=sp.nat(5236)))



OPTOUT_MAJ_CONTRACT_NAME = "AngryTeenagers Opt Out Majority voting"
OPTOUT_MAJ_DYNAMIC_INIT_VALUE = 2000
OPTOUT_MAJ_GOVERNANCE_PARAMETERS = sp.record(vote_delay_blocks = sp.nat(1),
                                               vote_length_blocks = sp.nat(14400),
                                               percentage_for_supermajority = sp.nat(50),
                                               fixed_quorum_percentage = sp.nat(25),
                                               fixed_quorum = sp.bool(True),
                                               quorum_cap = sp.record(lower=sp.nat(1), upper=sp.nat(5800)))


