import smartpy as sp

# Constants for Proposal based interactions.

# The type of a lambda that will be executed with a proposal.
PROPOSAL_LAMBDA_TYPE = sp.TOption(sp.TLambda(sp.TUnit, sp.TList(sp.TOperation)))

# The type of a proposal.
# Params:
# - title (string): The title of the proposal
# - descriptionLink (string): A link to the proposals description.
# - descriptionHash (string): A digest of the content at subscription link.
# - proposal (PROPOSAL_LAMBDA_TYPE): The code to execute.
# - Voting type: Right it is either a majority vote or a opt out vote
PROPOSAL_TYPE = sp.TRecord(
  title=sp.TString,
  description_link=sp.TString,
  description_hash=sp.TString,
  proposal_lambda=PROPOSAL_LAMBDA_TYPE,
  voting_strategy=sp.TNat
).layout(("title", ("description_link", ("description_hash", ("proposal_lambda", "voting_strategy")))))