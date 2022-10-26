import smartpy as sp

CONTRACT_NAME = "AngryTeenagers Opt Out"
ADMINISTRATOR_ADDRESS = "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"
CONTRACT_METADATA_IPFS_LINK ="ipfs://QmbDLHXZz9SjVPMQHYDW6VUEGEqKP8pxjRmQTa2fzLggN2"
GOVERNANCE_PARAMETERS = sp.record(vote_delay_blocks=sp.nat(1),
                                  vote_length_blocks=sp.nat(14400),
                                  objection_threshold_pertenmill=sp.nat(1000))
