# README

This folder contains all the contracts code for the Angry Teenagers NFTs (https://www.angryteenagers.xyz/).
Code is developed, compiled and unit tested for the Tezos blockchain using SmartPy v0.11.1 (https://smartpy.io/)

The Angry Teenagers project contains:
- A FA2 contract to hold the NFT collection (./nft/nft.py see https://gitlab.com/tezos/tzip/-/blob/master/proposals/tzip-12/tzip-12.md)
- A sale contract to sell the NFTs (./sale/sale.py)
- A DAO with a main component (./dao/dao.py) and two voting strategies (./dao/majority.py and ./dao/opt_out.py)

Each of these files are unit/functional tested using SmartPY. 
Tests are located in the test folder.

## HOWTO Generate the contract metadata

Each contract contains metadata.
See https://gitlab.com/tezos/tzip/-/blob/master/proposals/tzip-16/tzip-16.md
These metadata are stored in ipfs and a link of the ipfs file is stored inside a "metadata" big map in each contract
storage. Particularly, contract metadata contains the offchain views code.

To build the metadata, ech contract shall be compiled:

In the root folder of the repository:
```
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./nft/nft.py ../nft_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./nft/sale.py ../sale_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/dao.py ../dao_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/majority.py ../majority_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./dao/opt_out.py ../opt_out_compilation
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

Current version of the contracts metadata are stored in the metadata folder.

## HOWTO compile

In the root folder of the repository:
```
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./main/nft_main.py ../nft_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./main/sale_main.py ../sale_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./main/dao_main.py ../dao_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./main/majority_main.py ../majority_compilation
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh compile ./main/opt_out_main.py ../opt_out_compilation
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
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./test/nft_test.py ../nft_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./test/sale_test.py ../sale_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./test/dao_test.py ../dao_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./test/majority_test.py ../majority_test
% SMARTPY_INSTALLATION_FOLDER/SmartPy.sh test ./test/opt_out_test.py ../opt_out_test
```
Optionally, you can use the "--purge" option to clean the folder before running the tests and/or the 
"--htlm" to generate htlm logs.

## HOWTO configure the initial storage of the contract at compilation time
When you compile the contracts you can make some choices using the compilation target to configure your initial
storage

### NFT

See ./config/nft_config.py

Fields that can updated after deployment are:
- ROYALTIES_BYTES
- CONTRACT_METADATA_IPFS_LINK

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- ADMINISTRATOR_ADDRESS (administrator can be changed but only if the first administrator is valid)
- GENERIC_ARTWORK_IPFS_LINK
- GENERIC_DISPLAY_ARTWORK_IPFS_LINK
- GENERIC_THUMBNAIL_ARTWORK_IPFS_LINK
- PROJECT_ORACLES_STREAM_LINK
- WHAT3WORDS_FILE_IPFS_LINK
- TOTAL_SUPPLY
- ARTIFACT_FILE_TYPE
- ARTIFACT_FILE_SIZE
- ARTIFACT_FILE_NAME
- ARTIFACT_DIMENSIONS
- ARTIFACT_FILE_UNIT
- DISPLAY_FILE_TYPE
- DISPLAY_FILE_SIZE
- DISPLAY_FILE_NAME
- DISPLAY_DIMENSIONS
- DISPLAY_FILE_UNIT
- THUMBNAIL_FILE_TYPE
- THUMBNAIL_FILE_SIZE
- THUMBNAIL_FILE_NAME
- THUMBNAIL_DIMENSIONS
- THUMBNAIL_FILE_UNIT
- NAME_PREFIX
- SYMBOL
- DESCRIPTION
- LANGUAGE
- ATTRIBUTES_GENERIC
- RIGHTS
- CREATORS
- PROJECTNAME


### Sale

See ./config/sale_config.py 

Fields that can updated after deployment are:
- TRANSFER_ADDRESSES
- CONTRACT_METADATA_IPFS_LINK

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- ADMINISTRATOR_ADDRESS (administrator can be changed but only if the first administrator is valid)

### DAO

See ./config/dao_config.py

Fields that can updated after deployment are:
- CONTRACT_METADATA_IPFS_LINK
- POLL_MANAGER_INIT_VALUE: Voting strategies already injected cannot be changed but new can be added by the DAO

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- ADMINISTRATOR_ADDRESS (administrator can be changed but only if the first administrator is valid)

### Majority voting
Two configs are defined. One for the main DAO component (dynamic quorum) and one for the opt out contract (fixed quorum):

See ./config/majority_voting_config.py

Fields that can updated after deployment are:
- CONTRACT_METADATA_IPFS_LINK

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- ADMINISTRATOR_ADDRESS (administrator can be changed but only if the first administrator is valid)
- GOVERNANCE_PARAMETERS

### Opt out voting

See ./config/opt_out_voting_config.py 

Fields that can updated after deployment are:
- CONTRACT_METADATA_IPFS_LINK

A particular care shall be taken to set to correct values to the following fields before deployment as they cannot
be changed anymore:
- ADMINISTRATOR_ADDRESS (administrator can be changed but only if the first administrator is valid)
- GOVERNANCE_PARAMETERS

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


### Deploy the FA2 contract (./nft/nft.py)

Contract shall be first compiled.

Example -- WARNING: The storage may have to be updated:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AT_Nft_GhostNet_CR001_1 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q") (Pair {} 0x697066733a2f2f516d576b726b5a6a35363264754d47567777615574506f376948317a50744c594b423275394d3745665559424448)) (Pair (Pair 0x697066733a2f2f516d576b726b5a6a35363264754d47567777615574506f376948317a50744c594b423275394d3745665559424448 {}) (Pair {Elt "" 0x697066733a2f2f516d566e536e31517764714759414466583143466b7973346f78787a375050336e6a425138587239343572677366} 0))) (Pair (Pair (Pair {} False) (Pair 0x636572616d69633a2f2f516d576b726b5a6a35363264754d47567777615574506f376948317a50744c594b423275394d3745665559414141 0x7b22646563696d616c73223a20322c2022736861726573223a207b2022747a3151716f624d6543595931576a656150556370686879713251354333426654453271223a2031307d7d)) (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" {}) (Pair 5236 (Pair {} 0x697066733a2f2f516d555a315679727866374c4c6364725462593566313335634d3264424e6b75445a6e676e39714b3278654e7237)))))' --burn-cap 4
```
The FA2 contract administrator needs to be set accordingly by calling the entrypoint set_artwork_administrator and set_sale_contract_administrator.

### Deploy the sale contract (./sale/sale.py)

Contract shall be first compiled.

Example -- WARNING: The storage may have to be updated:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AT_Sale_GhostNet_CR001_1 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" {}) (Pair "1970-01-01T00:00:00Z" 0)) (Pair (Pair 0 0) (Pair False (Pair {} "KT1XmD6SKw6CFoxmGseB3ttws5n8sTXYkKkq")))) (Pair (Pair (Pair {Elt "" 0x697066733a2f2f516d563433464e4a454a4d47457a70416f4d786d6270536251427633574b7434753454366e64383569743952376a} {}) (Pair 0 0)) (Pair (Pair (Pair 0 (Pair False False)) 0) (Pair 0 (Pair 0 {Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 85; Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 15})))))' --burn-cap 4
```

If needed, link the FA2 contract to the sale contract by calling the entrypoint register_fa2 of the sale contract.

### Deploy the DAO

Voting strategies shall be deployed first as there address need to be copied inside the initial storage of the main DAO contract.

#### Deploy the majority vote (./dao/majority_voting.py)

Two contracts shall be deployed. One for the main DAO component and one for the opt out strategy.

Contract shall be first compiled.

Example (majority contract with dynamic quorum for main DAO component) -- WARNING: The storage may have to be updated:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AT_Dao_Maj_GhostNet_CR001_2 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 2000) (Pair (Pair 1 (Pair 180 (Pair 80 (Pair 25 (Pair False (Pair 1 5800)))))) {Elt "" 0x697066733a2f2f516d4e74706832446a7256634b394b58724e52735053774d507042705a6a593754693663654e6372626f7234356e})) (Pair (Pair {} None) (Pair None (Pair 0 0))))' --burn-cap 4
```
Set the poll_leader (the main DAO component) by calling the set_poll_leader entrypoint of the contract with the dynamic quorum.

Example (majority contract with fixed quorum for opt out voting strategy) -- WARNING: The storage may have to be updated:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AT_Dao_OtpOutMaj_GhostNet_CR001_2 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" 2000) (Pair (Pair 1 (Pair 180 (Pair 80 (Pair 25 (Pair True (Pair 1 5800)))))) {Elt "" 0x697066733a2f2f516d4e74706832446a7256634b394b58724e52735053774d507042705a6a593754693663654e6372626f7234356e})) (Pair (Pair {} None) (Pair None (Pair 0 0))))' --burn-cap 4
```
Set the poll_leader (the opt out contract) by calling the set_poll_leader entrypoint of the contract with the fixed quorum.

#### Deploy the opt out vote (./dao/opt_out_voting.py)

Contract shall be first compiled.

Example -- WARNING: The storage may have to be updated:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AT_Dao_OptOut_GhostNet_CR001_2 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" (Pair 1 (Pair 180 10))) (Pair {Elt "" 0x697066733a2f2f516d586857365847614a6e38426d6e6d3262636a656b36506b6b383465534d5a7431476b4a704a35314856515875} {})) (Pair (Pair None None) (Pair None (Pair 0 0))))' --burn-cap 4
```
Set the poll_leader (the main DAO component) by calling the set_poll_leader entrypoint of this contract.

#### Deploy the main DAO contract (./dao/dao.py)

Copy the two deployed contract addresses of the majority voting strategy and opt out voting strategy for the main DAO
component into the contract storage. Then compile.

Example -- WARNING: The storage may have to be updated:
```
tezos-client --endpoint https://rpc.ghostnet.teztnets.xyz/ originate contract AT_Dao_GhostNet_CR001_2 transferring 0 from tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q running ./step_000_cont_0_contract.tz --init '(Pair (Pair (Pair "tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q" None) (Pair {Elt "" 0x697066733a2f2f516d627a36673748514755467170475645665956693539676d5a6e3845547a6657597162685a4468666b396d6361} 0)) (Pair (Pair None {}) (Pair {Elt 0 (Pair "KT1DBK9hSKnLeG9W6UDfJBC8bDPDXLovJWjY" "MajorityVote"); Elt 1 (Pair "KT1Ccajj5Sw2PeKTSDhnCGpNUp1nsMhe3iHw" "OptOutVote")} 0)))' --burn-cap 4
```

Register the FA2 contract by calling the register_angry_teenager_fa2 entrypoint of the main DAO component contract.

#### Verify metadata
Contract and token metadata can be checked using https://tzcomet.io