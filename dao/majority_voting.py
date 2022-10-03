import smartpy as sp

Error = sp.io.import_script_from_url("file:./helper/errors.py")
VoteValue = sp.io.import_script_from_url("file:dao/helper/dao_vote_value.py")
PollOutcome = sp.io.import_script_from_url("file:dao/helper/dao_poll_outcome.py")

################################################################
################################################################
# Types
################################################################
################################################################
# VOTE_RECORD_TYPE
# Structured used to record the vote
# - vote_value: Vote value (Yay, Nay or Abstain)
# - level: Tezos block when the vote is sent
# - votes: Number of votes for this voter
VOTE_RECORD_TYPE = sp.TRecord(
  vote_value = sp.TNat,
  level = sp.TNat,
  votes = sp.TNat,
).layout(("vote_value", ("level", "votes")))

# MAJORITY_POLL_DATA
# Description of a vote currently in progress
# - vote_yay: Number of Yay votes
# - vote_nay: Number of Nay votes
# - vote_abstain: Number of abstain votes
# - total_votes: Total number of votes
# - voting_start_block: Tezos block when the vote started
# - voting_end_block: Tezos block when the vote ending
# - vote_id: Id of the vote
# - quorum: Quorum in number of votes for this vote
# - voters: Records who voted and what
MAJORITY_POLL_DATA = sp.TRecord(
    vote_yay=sp.TNat,
    vote_nay=sp.TNat,
    vote_abstain=sp.TNat,
    total_votes=sp.TNat,
    voting_start_block=sp.TNat,
    voting_end_block=sp.TNat,
    vote_id=sp.TNat,
    quorum = sp.TNat,
    voters = sp.TMap(sp.TAddress, VOTE_RECORD_TYPE)
).layout(("vote_yay", ("vote_nay", ("vote_abstain", ("total_votes", ("voting_start_block", ("voting_end_block", ("vote_id", ("quorum", "voters")))))))))

# QUORUM_CAP_TYPE
# - lower: Lowest possible value of the quorum percentage
# - upper: Biggest possible value of the quorum percentage
QUORUM_CAP_TYPE = sp.TRecord(
    lower = sp.TNat,
    upper = sp.TNat
)

# GOVERNANCE_PARAMETERS_TYPE
# These parameters are defined when the contract is deployed.
# Only the DAO can change these parameters.
# - vote_delay_blocks: Amount of blocks to wait to start voting after the proposal is inject
# - vote_length_blocks: Length of the vote in blocks
# - percentage_for_supermajority: Supermajority percentage
# - fixed_quorum_percentage: Quorum percentage when fixed quorum is used (i.e the percentage always remains the same)
# - fixed_quorum: Define whether the quorum is fixed or not
# - quorum_cap: See QUORUM_CAP_TYPE
GOVERNANCE_PARAMETERS_TYPE = sp.TRecord(
  vote_delay_blocks = sp.TNat,
  vote_length_blocks = sp.TNat,
  percentage_for_supermajority = sp.TNat,
  fixed_quorum_percentage = sp.TNat,
  fixed_quorum = sp.TBool,
  quorum_cap = QUORUM_CAP_TYPE
).layout(("vote_delay_blocks", ("vote_length_blocks", ("percentage_for_supermajority", ("fixed_quorum_percentage", ("fixed_quorum", "quorum_cap"))))))

# OUTCOMES_TYPE
# - poll_outcome: Outcome of the poll (PASSED or FAILED)
# - poll_data: See MAJORITY_POLL_DATA
OUTCOMES_TYPE = sp.TBigMap(sp.TNat, sp.TRecord(poll_outcome=sp.TNat, poll_data=MAJORITY_POLL_DATA))

################################################################
################################################################
# Constants
################################################################
################################################################

# Scale is the precision with which numbers are measured.
# For instance, a scale of 100 means the number 1.23 is represented
# as 123.
SCALE = 100

################################################################
################################################################
# State Machine
################################################################
################################################################


# NONE: Not vote in progress
NONE=0

# IN_PROGRESS: A vote is in progress
IN_PROGRESS=1

################################################################
################################################################
# Class
################################################################
################################################################
class DaoMajorityVoting(sp.Contract):
    def __init__(self, admin,
                 current_dynamic_quorum_value,
                 governance_parameters,
                 metadata,
                 outcomes=sp.big_map(l={}, tkey=sp.TNat, tvalue=sp.TRecord(poll_outcome=sp.TNat, poll_data=MAJORITY_POLL_DATA))):
      self.init_type(
        sp.TRecord(
            governance_parameters=GOVERNANCE_PARAMETERS_TYPE,
            current_dynamic_quorum_value = sp.TNat,
            poll_leader=sp.TOption(sp.TAddress),
            admin=sp.TAddress,
            next_admin=sp.TOption(sp.TAddress),
            vote_state=sp.TNat,
            poll_descriptor=sp.TOption(MAJORITY_POLL_DATA),
            vote_id=sp.TNat,
            outcomes=OUTCOMES_TYPE,
            metadata=sp.TBigMap(sp.TString, sp.TBytes)
        )
      )

      self.init(
        governance_parameters=governance_parameters,
        current_dynamic_quorum_value=current_dynamic_quorum_value,
        poll_leader=sp.none,
        admin=admin,
        next_admin=sp.none,
        vote_state=sp.nat(NONE),
        poll_descriptor=sp.none,
        vote_id=sp.nat(0),
        outcomes=outcomes,
        metadata=metadata
      )

      list_of_views = [
          self.get_historical_outcome_data
          , self.get_number_of_historical_outcomes
          , self.get_contract_state
          , self.get_current_poll_data
      ]

      metadata_base = {
          "name": "Angry Teenagers DAO Majority vote"
          ,
          "version": "1.0.5"
          , "description": (
              "Angry Teenagers Majority voting strategy."
          )
          , "interfaces": ["TZIP-016"]
          , "authors": [
              "EcoMint LTD <www.angryteenagers.xyz>"
          ]
          , "homepage": "https://www.angryteenagers.xyz"
          , "views": list_of_views
      }
      self.init_metadata("metadata_base", metadata_base)

################################################################
################################################################
# Interface
################################################################
################################################################
########################################################################################################################
# set_metadata
########################################################################################################################
    @sp.entry_point
    def set_metadata(self, k, v):
        sp.verify(sp.sender == self.data.admin, message=Error.ErrorMessage.unauthorized_user())
        self.data.metadata[k] = v

########################################################################################################################
# set_next_administrator
########################################################################################################################
    @sp.entry_point
    def set_next_administrator(self, params):
        sp.verify(sp.sender == self.data.admin, message = Error.ErrorMessage.unauthorized_user())
        self.data.next_admin = sp.some(params)

########################################################################################################################
# validate_new_administrator
########################################################################################################################
    @sp.entry_point
    def validate_new_administrator(self):
        sp.verify(self.data.next_admin.is_some(), message = Error.ErrorMessage.no_next_admin())
        sp.verify(sp.sender == self.data.next_admin.open_some(), message = Error.ErrorMessage.not_admin())
        self.data.admin = self.data.next_admin.open_some()
        self.data.next_admin = sp.none

########################################################################################################################
# set_poll_leader
########################################################################################################################
    @sp.entry_point
    def set_poll_leader(self, address):
        # Asserts
        sp.verify(~self.data.poll_leader.is_some(), Error.ErrorMessage.dao_already_registered())
        sp.verify(sp.sender == self.data.admin, Error.ErrorMessage.unauthorized_user())

        # Set the poll leader contract address
        self.data.poll_leader = sp.some(address)

########################################################################################################################
# start
########################################################################################################################
    @sp.entry_point
    def start(self, total_available_voters):
        # Check type
        sp.set_type(total_available_voters, sp.TNat)

        # Asserts
        sp.verify(self.data.vote_state == NONE, Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(sp.sender == self.data.poll_leader.open_some(), Error.ErrorMessage.unauthorized_user())

        # Define the quorum depending on how it is configured in the governance parameters
        new_quorum = sp.local('', self.data.current_dynamic_quorum_value)
        sp.if self.data.governance_parameters.fixed_quorum:
            new_quorum.value = (total_available_voters * self.data.governance_parameters.fixed_quorum_percentage) // SCALE

        # Compute when the vote starts and when it ends
        start_block = sp.level + self.data.governance_parameters.vote_delay_blocks
        end_block = start_block + self.data.governance_parameters.vote_length_blocks

        # Create the poll data for this vote
        self.data.poll_descriptor = sp.some(
            sp.record(
                vote_nay = sp.nat(0),
                vote_yay = sp.nat(0),
                vote_abstain = sp.nat(0),
                total_votes = sp.nat(0),
                voting_start_block = start_block,
                voting_end_block = end_block,
                vote_id = self.data.vote_id,
                quorum = new_quorum.value,
                voters=sp.map(l={}, tkey=sp.TAddress, tvalue=VOTE_RECORD_TYPE)
        ))

        # Callback the poll leader
        self.callback_leader_start()

        # Change the state of the contract
        self.data.vote_state = IN_PROGRESS

        sp.emit(self.data.vote_id, with_type=True, tag="Start a new vote")

########################################################################################################################
# vote
########################################################################################################################
    @sp.entry_point
    def vote(self, params):
        # Check type
        sp.set_type(params, sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, vote_id=sp.TNat))

        # Asserts
        sp.verify(sp.sender == self.data.poll_leader.open_some(), Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.vote_state == IN_PROGRESS, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.poll_descriptor.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(~self.data.poll_descriptor.open_some().voters.contains(params.address), Error.ErrorMessage.dao_vote_already_received())
        sp.verify(self.data.poll_descriptor.open_some().vote_id == params.vote_id, Error.ErrorMessage.dao_invalid_vote_id())
        sp.verify(sp.level >= self.data.poll_descriptor.open_some().voting_start_block, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(sp.level <= self.data.poll_descriptor.open_some().voting_end_block, Error.ErrorMessage.dao_no_vote_open())

        # Register new vote
        new_poll = sp.local('new_poll', self.data.poll_descriptor.open_some())

        sp.if params.vote_value == VoteValue.ABSTAIN:
            new_poll.value.vote_abstain = new_poll.value.vote_abstain + params.votes
        sp.else:
            sp.if params.vote_value == VoteValue.YAY:
                new_poll.value.vote_yay = new_poll.value.vote_yay + params.votes
            sp.else:
                sp.if params.vote_value == VoteValue.NAY:
                    new_poll.value.vote_nay = new_poll.value.vote_nay + params.votes
                sp.else:
                    sp.failwith(Error.ErrorMessage.dao_invalid_vote_value())

        new_poll.value.total_votes = new_poll.value.total_votes + params.votes
        new_poll.value.voters[params.address] = sp.record(vote_value=params.vote_value, level=sp.level, votes=params.votes)
        self.data.poll_descriptor = sp.some(new_poll.value)

        sp.emit(params, with_type=True, tag="Vote")

########################################################################################################################
# end
########################################################################################################################
    @sp.entry_point
    def end(self, params):
        # Check type
        sp.set_type(params, sp.TNat)

        # Asserts
        sp.verify(self.data.vote_state == IN_PROGRESS, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(sp.sender == self.data.poll_leader.open_some(), Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.poll_descriptor.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(params == self.data.poll_descriptor.open_some().vote_id, Error.ErrorMessage.dao_invalid_vote_id())
        sp.verify(sp.level > self.data.poll_descriptor.open_some().voting_end_block, Error.ErrorMessage.dao_no_vote_open())

        # Calculate whether voting thresholds were met.
        total_opinionated_votes = self.data.poll_descriptor.open_some().vote_yay + self.data.poll_descriptor.open_some().vote_nay
        yay_votes_needed_for_superMajority = (total_opinionated_votes * self.data.governance_parameters.percentage_for_supermajority) // SCALE

        # Define the vote outcome and sed the result to the poll leader
        sp.if (self.data.poll_descriptor.open_some().vote_yay >= yay_votes_needed_for_superMajority) & (self.data.poll_descriptor.open_some().total_votes >= self.data.poll_descriptor.open_some().quorum):
            self.data.outcomes[self.data.poll_descriptor.open_some().vote_id] =  sp.record(
                poll_outcome=PollOutcome.POLL_OUTCOME_PASSED,
                poll_data=self.data.poll_descriptor.open_some())
            self.callback_leader_end(PollOutcome.POLL_OUTCOME_PASSED)
        sp.else:
            self.data.outcomes[self.data.poll_descriptor.open_some().vote_id] = sp.record(
                poll_outcome=PollOutcome.POLL_OUTCOME_FAILED,
                poll_data=self.data.poll_descriptor.open_some())
            self.callback_leader_end(PollOutcome.POLL_OUTCOME_FAILED)

        # If the quorum is not fixed, compute the new quorum
        sp.if ~self.data.governance_parameters.fixed_quorum:
            self.update_quorum()

        # Close the vote
        self.data.poll_descriptor = sp.none
        self.data.vote_id = self.data.vote_id + 1
        self.data.vote_state = NONE

        sp.emit(params, with_type=True, tag="End vote")

########################################################################################################################
# mutez_transfer
########################################################################################################################
    @sp.entry_point
    def mutez_transfer(self, params):
        # Check type
        sp.set_type(params.destination, sp.TAddress)
        sp.set_type(params.amount, sp.TMutez)

        # Asserts
        sp.verify(self.data.admin == sp.sender, Error.ErrorMessage.unauthorized_user())

        # Send mutez
        sp.send(params.destination, params.amount)

################################################################
################################################################
# Helper functions
################################################################
################################################################
    def call(self, c, x):
        sp.transfer(x, sp.mutez(0), c)

    def update_quorum(self):
        last_weight = (self.data.poll_descriptor.open_some().quorum * 80) // SCALE  # 80% weight
        new_participation = (self.data.poll_descriptor.open_some().total_votes * 20) // SCALE  # 20% weight
        new_quorum = sp.local('newQuorum', new_participation + last_weight)

        # Bound upper and lower quorum.
        sp.if new_quorum.value < self.data.governance_parameters.quorum_cap.lower:
            new_quorum.value = self.data.governance_parameters.quorum_cap.lower

        sp.if new_quorum.value > self.data.governance_parameters.quorum_cap.upper:
            new_quorum.value = self.data.governance_parameters.quorum_cap.upper

        # Update quorum.
        self.data.current_dynamic_quorum_value = new_quorum.value

    def callback_leader_start(self):
        leaderContractHandle = sp.contract(
            sp.TRecord(
                id=sp.TNat,
                snapshot_block=sp.TNat
            ),
            self.data.poll_leader.open_some(),
            "propose_callback"
        ).open_some("Interface mismatch")

        leaderContractArg = sp.record(
            id=self.data.poll_descriptor.open_some().vote_id,
            snapshot_block=self.data.poll_descriptor.open_some().voting_start_block
        )
        self.call(leaderContractHandle, leaderContractArg)

    def callback_leader_end(self, result):
        leaderContractHandle = sp.contract(
            sp.TRecord(
                voting_id=sp.TNat,
                voting_outcome=sp.TNat
            ),
            self.data.poll_leader.open_some(),
            "end_callback"
        ).open_some("Interface mismatch")

        leaderContractArg = sp.record(
            voting_id=self.data.poll_descriptor.open_some().vote_id,
            voting_outcome=result
        )
        self.call(leaderContractHandle, leaderContractArg)

########################################################################################################################
########################################################################################################################
# Offchain views
########################################################################################################################
########################################################################################################################
    @sp.offchain_view(pure=True)
    def get_number_of_historical_outcomes(self):
        """Get how many historical outcome are stored in the DAO.
        """
        sp.result(self.data.vote_id)

    @sp.offchain_view(pure=True)
    def get_historical_outcome_data(self, id):
        """Get all historical outcomes ids.
        """
        sp.verify(self.data.outcomes.contains(id), Error.ErrorMessage.dao_invalid_outcome_id())
        sp.result(self.data.outcomes[id])

    @sp.offchain_view(pure=True)
    def get_current_poll_data(self):
        """Get all current poll data if it exists.
        """
        sp.verify(self.data.poll_descriptor.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.result(self.data.poll_descriptor.open_some())

    @sp.offchain_view(pure=True)
    def get_contract_state(self):
        """Get contract state
        """
        sp.result(self.data.vote_state)
