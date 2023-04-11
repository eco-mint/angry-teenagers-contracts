import smartpy as sp

CONTRACT_NAME = "AngryTeenagers Opt Out"
ADMINISTRATOR_ADDRESS = "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"
CONTRACT_METADATA_IPFS_LINK ="ipfs://QmYxWmU1D89fmqm1a9SwsQ3pfyb4Cj9xc42nb9QeHD6Fwa"
GOVERNANCE_PARAMETERS = sp.record(vote_delay_blocks=sp.nat(1),
                                  vote_length_blocks=sp.nat(120),
                                  objection_threshold_pertenmill=sp.nat(1000))
