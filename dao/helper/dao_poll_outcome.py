import smartpy as sp

PollType = sp.io.import_script_from_url("file:dao/helper/dao_poll_type.py")

# A historical result of a vote.
# Params:
# - outcome (nat): The outcome of the poll
# - poll (Poll.POLL_TYPE): The poll and the results.
HISTORICAL_OUTCOME_TYPE = sp.TRecord(
  outcome = sp.TNat,
  poll_data = PollType.POLL_TYPE
).layout(("outcome", "poll_data"))

POLL_OUTCOME_INPROGRESS = 0
POLL_OUTCOME_FAILED = 1       # Did not pass voting
POLL_OUTCOME_PASSED = 2       # Did pass voting