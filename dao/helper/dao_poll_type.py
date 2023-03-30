import smartpy as sp

Proposal = sp.io.import_script_from_url("file:dao/helper/dao_proposal.py")

# POLL_ERROR
# Link to the description (in IPFS for instance) ad hash of the description
# of the error that occurs with the lambda inside the proposal
POLL_LAMBDA_ERROR=sp.TRecord(description_link=sp.TString, hash_description=sp.TString)

# POLL_TYPE
# The proposal information
# - proposal: See Proposal.PROPOSAL_TYPE
# - proposal_id: Id of the proposal
# - author: Address of the author
# - voting_strategy_address: Address of the voting contract
# - voting_id: Id of the vote
# - snapshot_block: Block used to get the get the voting power
# - error: Error information if the proposal is rejected by the admin
POLL_TYPE = sp.TRecord(
                proposal=Proposal.PROPOSAL_TYPE,
                proposal_id=sp.TNat,
                author=sp.TAddress,
                voting_strategy_address=sp.TAddress,
                voting_id=sp.TNat,
                snapshot_block=sp.TNat,
                lambda_error=sp.TOption(POLL_LAMBDA_ERROR)
).layout(("proposal",
          ("proposal_id",
           ("author",
            ("voting_strategy_address",
             ("voting_id", 
              ("snapshot_block", 
               ("lambda_error"))))))))