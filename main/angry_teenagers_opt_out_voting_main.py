import smartpy as sp

DAO = sp.io.import_script_from_url("file:./dao/angry_teenagers_opt_out_voting.py")
Config = sp.io.import_script_from_url("file:./config/angry_teenagers_opt_out_voting_config.py")

########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
########################################################################################################################
sp.add_compilation_target(Config.CONTRACT_NAME,
                          DAO.DaoOptOutVoting(
                              admin=sp.address(Config.ADMINISTRATOR_ADDRESS),
                              governance_parameters= Config.GOVERNANCE_PARAMETERS,
                              metadata = sp.utils.metadata_of_url(Config.CONTRACT_METADATA_IPFS_LINK)
                          ))
