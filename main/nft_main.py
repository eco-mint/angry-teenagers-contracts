import smartpy as sp

NFT = sp.io.import_script_from_url("file:./nft/nft.py")
Config = sp.io.import_script_from_url("file:./config/nft_config.py")

########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
########################################################################################################################
sp.add_compilation_target(Config.CONTRACT_NAME,
                          NFT.AngryTeenagers(
                              administrator=sp.address(Config.ADMINISTRATOR_ADDRESS),
                              metadata=sp.utils.metadata_of_url(Config.CONTRACT_METADATA_IPFS_LINK),
                              generic_ipfs=sp.utils.bytes_of_string(Config.GENERIC_ARTWORK_IPFS_LINK),
                              project_oracles_stream=sp.utils.bytes_of_string(Config.PROJECT_ORACLES_STREAM_LINK),
                              what3words_file_ipfs=sp.utils.bytes_of_string(Config.WHAT3WORDS_FILE_IPFS_LINK),
                              total_supply=Config.TOTAL_SUPPLY))
