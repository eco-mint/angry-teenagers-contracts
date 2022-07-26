import smartpy as sp

Proposal = sp.io.import_script_from_url("file:dao/helper/angry_teenagers_dao_proposal.py")

# POLL_TYPE
# The proposal information
# - proposal: See Proposal.PROPOSAL_TYPE
# - proposal_id: Id of the proposal
# - author: Address of the author
# - voting_strategy_address: Address of the voting contract
# - voting_id: Id of the vote
# - snapshot_block: Block used to get the get the voting power
POLL_TYPE = sp.TRecord(
                proposal=Proposal.PROPOSAL_TYPE,
                proposal_id=sp.TNat,
                author=sp.TAddress,
                voting_strategy_address=sp.TAddress,
                voting_id=sp.TNat,
                snapshot_block=sp.TNat
).layout(("proposal",
          ("proposal_id",
           ("author",
            ("voting_strategy_address",
             ("voting_id", "snapshot_block"))))))