import smartpy as sp

CONTRACT_NAME = "AngryTeenagers Opt Out"
ADMINISTRATOR_ADDRESS = "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"
CONTRACT_METADATA_IPFS_LINK ="ipfs://QmR8PKUiDkZtTKQDx3uxRwmASkop9MTvTXHdaAbjdYKgNs"
GOVERNANCE_PARAMETERS = sp.record(vote_delay_blocks=sp.nat(1),
                                  vote_length_blocks=sp.nat(14400),
                                  percentage_for_objection=sp.nat(10))
