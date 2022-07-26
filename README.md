# README

This folder contains all the contracts code for the Angry Teenagers NFTs (https://www.angryteenagers.xyz/).
Code is developed, compiled and unit tested for the Tezos blockchain using SmartPy v0.11.1 (https://smartpy.io/)

The Angry Teenagers project contains:
- A FA2 contract to hold the NFT collection (./nft/angry_teenagers_nft.py see https://gitlab.com/tezos/tzip/-/blob/master/proposals/tzip-12/tzip-12.md)
- A sale contract to sell the NFTs (./sale/angry_teenagers_sale.py)
- A DAO with a main component (./dao/angry_teenagers_dao.py) and two voting strategies (./dao/angry_teenagers_majority.py and ./dao/angry_teenagers_opt_out.py)

Each of these files are unit/functional tested using SmartPY. Tests are always located at the end of the contract definition.

## HOWTO Generate the contract metadata

Each contract contains metadata.
See https://gitlab.com/tezos/tzip/-/blob/master/proposals/tzip-16/tzip-16.md
These metadata are stored in ipfs and a link of the ipfs file is stored inside a "metadata" big map in each contract
storage. Particularly, contract metadata contains the offchain views code.

To build the metadata, ech contract shall be compiled:

In the root folder of the repository:
```
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./nft/angry_teenagers_nft.py ../nft_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./nft/angry_teenagers_sale.py ../sale_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/angry_teenagers_dao.py ../dao_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/angry_teenagers_majority.py ../majority_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/angry_teenagers_opt_out.py ../opt_out_compilation
```
Contract metadata are then located in the compilation folder.
For instance for the NFT contract: ../nft_compilation/step_000_cont_0_metadata.metadata_base.json

This file shall be then copy to ipfs. The resulting ipfs CIDs is then used to build a string like:
ipfs://Qmd6MNVL72Zsgqjj5GAL2x6URfg1NW33hwVAEfcCU3Jbrc and its binary counterpart:
697066733a2f2f516d64364d4e564c37325a7367716a6a3547414c32783655526667314e573333687756414566634355334a627263

The bytes array shall be then included in the contract:
- if the contract is already deployed, the set_metadata entrypoint can be used.
- if the contract is not deployed it can be recompiled to contain the ipfs link in the storage at initialization time.

Note that metadata can be changed without changing the contract. This could be useful to improve the frontend.

## HOWTO compile

In the root folder of the repository:
```
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./nft/angry_teenagers_nft.py ../nft_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./nft/angry_teenagers_sale.py ../sale_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/angry_teenagers_dao.py ../dao_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/angry_teenagers_majority.py ../majority_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/angry_teenagers_opt_out.py ../opt_out_compilation
```
Compilation produces two main files per contract (each of them with 3 different format depending on how you deployed:
json format, tez format or py format):
- The initial storage
- The source code of the contract
Both these files are needed to deploy the contract on the blockchain network.

## HOWTO run unit/functional tests

Each contracts contains its own testing.
To run the test please do:
```
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./nft/angry_teenagers_nft.py ../nft_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./nft/angry_teenagers_sale.py ../sale_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./dao/angry_teenagers_dao.py ../dao_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./dao/angry_teenagers_majority.py ../majority_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./dao/angry_teenagers_opt_out.py ../opt_out_test
```
Optionally, you can use the "--purge" option to clean the folder before running the tests and/or the 
"--htlm" to generate htlm logs.

## HOWTO configure the initial storage of the contract at compilation time
When you compile the contracts you can make some choices using the compilation target to configure your initial
storage

### ./nft/angry_teenagers_nft.py
The compilation target is:
```
sp.add_compilation_target("AngryTeenagers",
                          AngryTeenagers(
                              administrator=sp.address("tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph"),
                              royalties_bytes=sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph": 10}}'),
                              metadata=sp.utils.metadata_of_url("ipfs://QmaSL3oE3RWCkR2mM3vK8TdRCFMmkPAfvoeQTbinsC9bLN"),
                              # TODO: This is not a valid generic image
                              generic_image_ipfs=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                              generic_image_ipfs_thumbnail=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                              # A valid project oracles is needed as it cannot be changed later on
                              project_oracles_stream=sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"),
                              what3words_file_ipfs=sp.utils.bytes_of_string("ipfs://QmUZ1Vyrxf7LLcdrTbY5f135cM2dBNkuDZngn9qK2xeNr7"),
                              total_supply=5236))
```
Fields that can updated after deployment are:
- royalties_bytes
- metadata

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- administrator (administrator can be changed but only if the first administrator is valid)
- generic_image_ipfs
- generic_image_ipfs_thumbnail
- project_oracles_stream
- what3words_file_ipfs

### ./sale/angry_teenagers_sale.py
The compilation target is:
```
sp.add_compilation_target("AngryTeenagers Crowdsale contract",
                          AngryTeenagersSale(admin=sp.address("tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph"),
                                         transfer_addresses=sp.list([sp.pair(sp.address("tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph"), sp.nat(85)),
                                                                   sp.pair(sp.address("tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph"), sp.nat(15))]),
                                         metadata=sp.utils.metadata_of_url("ipfs://QmS5kmyssuBdQaLMQt9fySvvAh1pcpjJEDQ38iMwZpxTyF")))
```
Fields that can updated after deployment are:
- transfer_addresses

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- administrator (administrator can be changed but only if the first administrator is valid)

### ./dao/angry_teenagers_dao.py
The compilation target is:
```
sp.add_compilation_target("AngryTeenagers DAO",
                          # TODO: Real addresses shall be used
                            AngryTeenagersDao(
                                admin=sp.address("tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph"),
                                # TODO: Inject the right metadata
                                # TODO: The opt out contract is not added. the majority one is not valid
                                metadata=sp.utils.metadata_of_url("ipfs://QmUM7qhTYSAjd1uy8bhRD1G6K5VWug18CV4hAtXTVRJhMP"),
                                poll_manager=sp.map(l = { VOTE_TYPE_MAJORITY : sp.record(name=sp.string("MajorityVote"), address=sp.address("tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph"))}, tkey=sp.TNat, tvalue=sp.TRecord(name=sp.TString, address=sp.TAddress))))
```
Fields that can updated after deployment are:
- metadata
- poll_manager: Voting strategies already injected cannot be changed but new can be added by the DAO

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- administrator (administrator can be changed but only if the first administrator is valid)

### ./dao/angry_teenagers_majority_voting.py
Two compilation targets are defined.
One for the main DAO component (dynamic quorum) and one for the opt out contract (fixed quorum):
```
sp.add_compilation_target("AngryTeenagersMajorityVoting",
                          # TODO: Real address shall be used
                          DaoMajorityVoting(
                              admin=sp.address("tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"),
                              current_dynamic_quorum_value=sp.nat(2000),
                              governance_parameters= sp.record(vote_delay_blocks = sp.nat(1),
                                                               vote_length_blocks = sp.nat(180),
                                                               percentage_for_supermajority = sp.nat(80),
                                                               fixed_quorum_percentage = sp.nat(25),
                                                               fixed_quorum = sp.bool(False),
                                                               quorum_cap = sp.record(lower=sp.nat(1), upper=sp.nat(5800))),
                              # TODO: Inject the right metadata
                              metadata = sp.utils.metadata_of_url("ipfs://QmNtph2DjrVcK9KXrNRsPSwMPpBpZjY7Ti6ceNcrbor45n")
                          ))
```
```
sp.add_compilation_target("AngryTeenagersOptOutMajorityVoting",
                          # TODO: Real address shall be used
                          DaoMajorityVoting(
                              admin=sp.address("tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"),
                              current_dynamic_quorum_value=sp.nat(2000),
                              governance_parameters= sp.record(vote_delay_blocks = sp.nat(1),
                                                               vote_length_blocks = sp.nat(180),
                                                               percentage_for_supermajority = sp.nat(80),
                                                               fixed_quorum_percentage = sp.nat(25),
                                                               fixed_quorum = sp.bool(True),
                                                               quorum_cap = sp.record(lower=sp.nat(1), upper=sp.nat(5800))),
                              # TODO: Inject the right metadata
                              metadata = sp.utils.metadata_of_url("ipfs://QmNtph2DjrVcK9KXrNRsPSwMPpBpZjY7Ti6ceNcrbor45n")
                          ))
```
Fields that can updated after deployment are:
- metadata
- governance_parameters but only by the DAO iself

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- administrator (administrator can be changed but only if the first administrator is valid)

### ./dao/angry_teenagers_opt_out_voting.py
The compilation target is:
```
sp.add_compilation_target("AngryTeenagersOptOutVoting",
                          # TODO: Real address shall be used
                          DaoOptOutVoting(
                              admin=sp.address("tz1QRoH2rdD8HPvWXDhe9ZhToTHGUx6Mggph"),
                              governance_parameters= sp.record(vote_delay_blocks = sp.nat(1),
                                                               vote_length_blocks = sp.nat(180),
                                                               percentage_for_objection = sp.nat(10)),
                              # TODO: Inject the right metadata
                              metadata = sp.utils.metadata_of_url("ipfs://QmUM7qhTYSAjd1uy8bhRD1G6K5VWug18CV4hAtXTVRJhMP")
                          ))
```
Fields that can updated after deployment are:
- metadata
- governance_parameters but only by the DAO iself

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- administrator (administrator can be changed but only if the first administrator is valid)

## HOWTO to deploy contracts on the Tezos blockchain

The deployment is done using the Tezos client (tezos-client v13.0).
Command looks like this:
```
tezos-client --endpoint NODE_ADDRESS originate contract NAME transferring 0 \ 
    from SENDER_ADDRESS running TEZOS_SOURCE_CODE_TZ_FILE --init 'INITIAL_STORAGE' --burn-cap MAX_XTZ_TO_SPEND
```
Where:
- **NODE_ADDRESS** is the address of the node.
- **NAME** is the name of the contract
- **SENDER_ADRESS** is the address used to deploy the contract. This is not the multisig but a dummy address.
- **TEZOS_SOURCE_CODE_TZ_FILE** is the path of the file containing the result of the compilation
- **INITIAL_STORAGE** is the initial storage defined by at the compilation time
- **MAX_XTZ_TO_SPEND** is the max amount of XTZ to spend during this deployment


### Deploy the FA2 contract (./nft/angry_teenagers_nft.py)

Contract shall be first compiled.

Example:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AngryTeenagersGhostnet1 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q") (Pair {} {})) (Pair (Pair 0x697066733a2f2f516d576b726b5a6a35363264754d47567777615574506f376948317a50744c594b423275394d3745665559424448 0x697066733a2f2f516d576b726b5a6a35363264754d47567777615574506f376948317a50744c594b423275394d3745665559424448) (Pair {} (Pair {Elt "" 0x697066733a2f2f516d59626469684c587743716b79667a6877626b654139545a78703363663778764e334673564d64616b48386237} {})))) (Pair (Pair (Pair 0 {}) (Pair {} (Pair False 0x636572616d69633a2f2f516d576b726b5a6a35363264754d47567777615574506f376948317a50744c594b423275394d3745665559414141))) (Pair (Pair 0x7b22646563696d616c73223a20322c2022736861726573223a207b2022747a3151716f624d6543595931576a656150556370686879713251354333426654453271223a2031307d7d "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q") (Pair 5236 (Pair {} 0x697066733a2f2f516d555a315679727866374c4c6364725462593566313335634d3264424e6b75445a6e676e39714b3278654e7237)))))' --burn-cap 4
```

### Deploy the sale contract (./sale/angry_teenagers_sale.py)

Contract shall be first compiled.

Example:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AngryTeenagersSaleGhostnet1 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" {}) (Pair "1970-01-01T00:00:00Z" 0)) (Pair (Pair 0 0) (Pair False (Pair {} "KT1XmD6SKw6CFoxmGseB3ttws5n8sTXYkKkq")))) (Pair (Pair (Pair {Elt "" 0x697066733a2f2f516d563433464e4a454a4d47457a70416f4d786d6270536251427633574b7434753454366e64383569743952376a} {}) (Pair 0 0)) (Pair (Pair (Pair 0 (Pair False False)) 0) (Pair 0 (Pair 0 {Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 85; Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 15})))))' --burn-cap 4
```

If needed, link the FA2 contract to the sale contract by calling the entrypoint register_fa2 of the sale contract.

### Deploy the DAO

Voting strategies shall be deployed first as there address need to be copied inside the initial storage of the main DAO contract.

#### Deploy the majority vote (./dao/angry_teenagers_majority_voting.py)

Two contracts shall be deployed. One for the main DAO component and one for the opt out strategy.

Contract shall be first compiled.

Example (majority contract with dynamic quorum for main DAO component):
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AngryTeenagersDaoMajorityGhostnet2 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 2000) (Pair (Pair 1 (Pair 180 (Pair 80 (Pair 25 (Pair False (Pair 1 5800)))))) {Elt "" 0x697066733a2f2f516d4e74706832446a7256634b394b58724e52735053774d507042705a6a593754693663654e6372626f7234356e})) (Pair (Pair {} None) (Pair None (Pair 0 0))))' --burn-cap 4
```
Set the poll_leader (the main DAO component) by calling the set_poll_leader entrypoint of the contract with the dynamic quorum.

Example (majority contract with fixed quorum for opt out voting strategy):
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AngryTeenagersDaoOptOutMajorityGhostnet1 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 2000) (Pair (Pair 1 (Pair 180 (Pair 80 (Pair 25 (Pair True (Pair 1 5800)))))) {Elt "" 0x697066733a2f2f516d4e74706832446a7256634b394b58724e52735053774d507042705a6a593754693663654e6372626f7234356e})) (Pair (Pair {} None) (Pair None (Pair 0 0))))' --burn-cap 4
```
Set the poll_leader (the opt out contract) by calling the set_poll_leader entrypoint of the contract with the fixed quorum.

#### Deploy the opt out vote (./dao/angry_teenagers_opt_out_voting.py)

Contract shall be first compiled.

Example:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AngryTeenagersDaoOptOutGhostnet1 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" (Pair 1 (Pair 180 10))) (Pair {Elt "" 0x697066733a2f2f516d586857365847614a6e38426d6e6d3262636a656b36506b6b383465534d5a7431476b4a704a35314856515875} {})) (Pair (Pair None None) (Pair None (Pair 0 0))))' --burn-cap 4
```
Set the poll_leader (the main DAO component) by calling the set_poll_leader entrypoint of this contract.

#### Deploy the main DAO contract (./dao/angry_teenagers_dao.py)

Copy the two deployed contract addresses of the majority voting strategy and opt out voting strategy for the main DAO
component into the contract storage. Then compile.

Example:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AngryTeenagersDaoGhostnet2 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" None) (Pair {Elt "" 0x697066733a2f2f516d627a36673748514755467170475645665956693539676d5a6e3845547a6657597162685a4468666b396d6361} 0)) (Pair (Pair None {}) (Pair {Elt 0 (Pair "KT1Vk3GjhwHP732NcVBRT6yNmoAxy2Jyh81G" "MajorityVote"); Elt 1 (Pair "KT1CBeoEjK9gHmifS7W71HoNddoLD9hv1HxE" "OptOutVote")} 0)))' --burn-cap 4
```

Register the FA2 contract by calling the register_angry_teenager_fa2 entrypoint of the main DAO component contract.