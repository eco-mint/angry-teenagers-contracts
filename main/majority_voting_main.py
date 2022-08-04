import smartpy as sp

DAO = sp.io.import_script_from_url("file:./dao/majority_voting.py")
Config = sp.io.import_script_from_url("file:./config/majority_voting_config.py")

########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
########################################################################################################################
sp.add_compilation_target(Config.MAIN_MAJ_CONTRACT_NAME,
                          DAO.DaoMajorityVoting(
                              admin=sp.address(Config.ADMINISTRATOR_ADDRESS),
                              current_dynamic_quorum_value=sp.nat(Config.MAIN_MAJ_DYNAMIC_INIT_VALUE),
                              governance_parameters=Config.MAIN_MAJ_GOVERNANCE_PARAMETERS,
                              metadata=sp.utils.metadata_of_url(Config.CONTRACT_METADATA_IPFS_LINK)
                          ))

sp.add_compilation_target(Config.OPTOUT_MAJ_CONTRACT_NAME,
                          DAO.DaoMajorityVoting(
                              admin=sp.address(Config.ADMINISTRATOR_ADDRESS),
                              current_dynamic_quorum_value=sp.nat(Config.OPTOUT_MAJ_DYNAMIC_INIT_VALUE),
                              governance_parameters= Config.OPTOUT_MAJ_GOVERNANCE_PARAMETERS,
                              metadata = sp.utils.metadata_of_url(Config.CONTRACT_METADATA_IPFS_LINK)
                          ))
