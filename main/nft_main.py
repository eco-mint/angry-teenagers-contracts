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
                              royalties_bytes=sp.utils.bytes_of_string(Config.ROYALTIES_BYTES),
                              metadata=sp.utils.metadata_of_url(Config.CONTRACT_METADATA_IPFS_LINK),
                              generic_image_ipfs=sp.utils.bytes_of_string(Config.GENERIC_ARTWORK_IPFS_LINK),
                              generic_image_ipfs_thumbnail=sp.utils.bytes_of_string(Config.GENERIC_THUMBNAIL_ARTWORK_IPFS_LINK),
                              project_oracles_stream=sp.utils.bytes_of_string(Config.PROJECT_ORACLES_STREAM_LINK),
                              what3words_file_ipfs=sp.utils.bytes_of_string(Config.WHAT3WORDS_FILE_IPFS_LINK),
                              total_supply=Config.TOTAL_SUPPLY,
                              artifact_file_type=Config.ARTIFACT_FILE_TYPE,
                              artifact_file_size=Config.ARTIFACT_FILE_SIZE,
                              artifact_file_name=Config.ARTIFACT_FILE_NAME,
                              artifact_dimensions=Config.ARTIFACT_DIMENSIONS,
                              artifact_file_unit=Config.ARTIFACT_FILE_UNIT,
                              display_file_type=Config.DISPLAY_FILE_TYPE,
                              display_file_size=Config.DISPLAY_FILE_SIZE,
                              display_file_name=Config.DISPLAY_FILE_NAME,
                              display_dimensions=Config.DISPLAY_DIMENSIONS,
                              display_file_unit=Config.DISPLAY_FILE_UNIT,
                              thumbnail_file_type=Config.THUMBNAIL_FILE_TYPE,
                              thumbnail_file_size=Config.THUMBNAIL_FILE_SIZE,
                              thumbnail_file_name=Config.THUMBNAIL_FILE_NAME,
                              thumbnail_dimensions=Config.THUMBNAIL_DIMENSIONS,
                              thumbnail_file_unit=Config.THUMBNAIL_FILE_UNIT,
                              name_prefix=Config.NAME_PREFIX,
                              symbol=Config.SYMBOL,
                              description=Config.DESCRIPTION,
                              language=Config.LANGUAGE,
                              attributes_generic=Config.ATTRIBUTES_GENERIC,
                              rights=Config.RIGHTS,
                              creators=Config.CREATORS,
                              project_name=Config.PROJECTNAME))
