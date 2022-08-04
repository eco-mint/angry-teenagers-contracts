import smartpy as sp

DAO = sp.io.import_script_from_url("file:./dao/dao.py")
Config = sp.io.import_script_from_url("file:./config/dao_config.py")

########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
########################################################################################################################
sp.add_compilation_target(Config.CONTRACT_NAME,
                            DAO.AngryTeenagersDao(
                                admin=sp.address(Config.ADMINISTRATOR_ADDRESS),
                                metadata=sp.utils.metadata_of_url(Config.CONTRACT_METADATA_IPFS_LINK),
                                poll_manager=Config.POLL_MANAGER_INIT_VALUE))
