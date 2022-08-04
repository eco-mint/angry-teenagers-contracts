import smartpy as sp

Sale = sp.io.import_script_from_url("file:./sale/sale.py")
Config = sp.io.import_script_from_url("file:./config/sale_config.py")


########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
##################################################################################################################
sp.add_compilation_target(Config.CONTRACT_NAME,
                          Sale.AngryTeenagersSale(admin=sp.address(Config.ADMINISTRATOR_ADDRESS),
                                         transfer_addresses=Config.TRANSFER_ADDRESSES,
                                         metadata=sp.utils.metadata_of_url(Config.CONTRACT_METADATA_IPFS_LINK)))

