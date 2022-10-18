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
# A type recording the way an address voted.
# Params:
# - voteValue (nat): The Vote value
# - level (nat): The block level the vote was cast on.
# - votes (nat): The number of tokens voted with.
VOTE_RECORD_TYPE = sp.TRecord(
  vote_value=sp.TNat,
  level=sp.TNat,
  votes=sp.TNat,
).layout(("vote_value",
          ("level", "votes")))

# MAJORITY_POLL_DATA
# - phase_1_vote_objection: Number of votes rejecting the proposal
# - phase_1_voting_start_block: Tezos start block of the phase 1
# - phase_1_voting_end_block: Tezos end block of the phase 1
# - vote_id: Id of the vote
# - total_voters: Total number of voters
# - phase_1_objection_threshold: Numbers of voters needed to reject the proposal in phase 1
# - phase_2_needed: Record whether the phase 2 is needed or not
# - phase_2_vote_id: Vote id of the phase 2 (use the majority contract)
# - phase_1_voters: Record of the voters data in phase 1 (phase 2 is recorded in the majority contract)
MAJORITY_POLL_DATA = sp.TRecord(
    phase_1_vote_objection=sp.TNat,
    phase_1_voting_start_block=sp.TNat,
    phase_1_voting_end_block=sp.TNat,
    vote_id=sp.TNat,
    total_voters=sp.TNat,
    phase_1_objection_threshold=sp.TNat,
    phase_2_needed=sp.TBool,
    phase_2_vote_id=sp.TNat,
    phase_1_voters=sp.TMap(sp.TAddress, VOTE_RECORD_TYPE)
).layout(("phase_1_vote_objection",
          ("phase_1_voting_start_block",
           ("phase_1_voting_end_block",
            ("vote_id",
             ("total_voters",
              ("phase_1_objection_threshold",
                ("phase_2_needed",
                 ("phase_2_vote_id",
                  ("phase_1_voters"))))))))))

# GOVERNANCE_PARAMETERS_TYPE
# Governance parameters are defined when the contract is deployed and can only be changed
# by the DAO
# - vote_delay_blocks: Amount of blocks to wait to start voting after the proposal is inject
# - vote_length_blocks: Length of the vote in blocks
# - objection_threshold_pertenmill: Pertenmill that needs to be reached to reject the proposal in phase 1 and go to phase 2
GOVERNANCE_PARAMETERS_TYPE = sp.TRecord(
  vote_delay_blocks=sp.TNat,
  vote_length_blocks=sp.TNat,
  objection_threshold_pertenmill=sp.TNat
).layout(("vote_delay_blocks",
          ("vote_length_blocks", "objection_threshold_pertenmill")))

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
SCALE_PERTENMILL = 10000


################################################################
################################################################
# State Machine
################################################################
################################################################
# NONE: No vote in progress
NONE=0

# PHASE_1_OPT_OUT: Phase 1 is in progress
PHASE_1_OPT_OUT=1

# STARTING_PHASE_2: Phase 2 is starting and requested to start a majority
# vote to the majority contract. Wait for the answer.
STARTING_PHASE_2=2

# PHASE_2_MAJORITY: Phase 2 is in progress
PHASE_2_MAJORITY=3

# ENDING_PHASE_2: Phase 2 is ending. Waiting for the answer of the majority contract.
ENDING_PHASE_2=4

################################################################
################################################################
# Class
################################################################
################################################################
class DaoOptOutVoting(sp.Contract):
    def __init__(self, admin,
                 governance_parameters,
                 metadata,
                 outcomes=sp.big_map(l={}, tkey=sp.TNat, tvalue=sp.TRecord(poll_outcome=sp.TNat, poll_data=MAJORITY_POLL_DATA))):
      self.init_type(
        sp.TRecord(
            governance_parameters=GOVERNANCE_PARAMETERS_TYPE,
            poll_leader=sp.TOption(sp.TAddress),
            phase_2_majority_vote_contract=sp.TOption(sp.TAddress),
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
        poll_leader=sp.none,
        phase_2_majority_vote_contract=sp.none,
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
          "name": "Angry Teenagers DAO OptOut vote"
          ,
          "version": "1.0.5"
          , "description": (
              "Angry Teenagers Opt out strategy."
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
    @sp.entry_point(check_no_incoming_transfer=True)
    def set_metadata(self, key, value):
        sp.verify(sp.sender == self.data.admin, message=Error.ErrorMessage.unauthorized_user())
        self.data.metadata[key] = value

########################################################################################################################
# set_next_administrator
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def set_next_administrator(self, params):
        sp.verify(sp.sender == self.data.admin, message=Error.ErrorMessage.unauthorized_user())
        self.data.next_admin = sp.some(params)

########################################################################################################################
# validate_new_administrator
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def validate_new_administrator(self):
        sp.verify(self.data.next_admin.is_some(), message=Error.ErrorMessage.no_next_admin())
        sp.verify(sp.sender == self.data.next_admin.open_some(), message=Error.ErrorMessage.not_admin())
        self.data.admin = self.data.next_admin.open_some()
        self.data.next_admin = sp.none

########################################################################################################################
# set_poll_leader
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def set_poll_leader(self, address):
        # Asserts
        sp.verify(~self.data.poll_leader.is_some(), message=Error.ErrorMessage.dao_already_registered())
        sp.verify(sp.sender == self.data.admin, message=Error.ErrorMessage.unauthorized_user())

        # Set address
        self.data.poll_leader = sp.some(address)

########################################################################################################################
# set_phase_2_contract
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def set_phase_2_contract(self, address):
        # Asserts
        sp.verify(~self.data.phase_2_majority_vote_contract.is_some(), message=Error.ErrorMessage.dao_already_registered())
        sp.verify(sp.sender == self.data.admin, message=Error.ErrorMessage.unauthorized_user())

        # Set address
        self.data.phase_2_majority_vote_contract = sp.some(address)

########################################################################################################################
# start
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def start(self, total_available_voters):
        # Check type
        sp.set_type(total_available_voters, sp.TNat)

        # Asserts
        sp.verify(self.data.phase_2_majority_vote_contract.is_some(), message=Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(self.data.vote_state == NONE, message=Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(sp.sender == self.data.poll_leader.open_some(), message=Error.ErrorMessage.unauthorized_user())

        # Compute the objection threshold using the percentage and the number of possible voters
        objection_threshold = (total_available_voters * self.data.governance_parameters.objection_threshold_pertenmill) // SCALE_PERTENMILL

        # Compute the start and end block of the vote
        start_block = sp.level + self.data.governance_parameters.vote_delay_blocks
        end_block = start_block + self.data.governance_parameters.vote_length_blocks

        # Create the vote data
        self.data.poll_descriptor = sp.some(
            sp.record(
                phase_1_vote_objection=sp.nat(0),
                phase_1_voting_start_block=start_block,
                phase_1_voting_end_block=end_block,
                vote_id=self.data.vote_id,
                total_voters=total_available_voters,
                phase_1_objection_threshold=objection_threshold,
                phase_2_needed=sp.bool(False),
                phase_2_vote_id=sp.nat(0),
                phase_1_voters=sp.map(l={}, tkey=sp.TAddress, tvalue=VOTE_RECORD_TYPE)
        ))

        # Callback the poll leader
        self.callback_leader_start()

        # Change the state of the contract
        self.data.vote_state = PHASE_1_OPT_OUT

        sp.emit(self.data.vote_id, with_type=True, tag="Start a new vote")

########################################################################################################################
# vote
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def vote(self, params):
        # Check type
        sp.set_type(params, sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, vote_id=sp.TNat))

        # Asserts
        sp.verify(sp.sender == self.data.poll_leader.open_some(), message=Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.poll_descriptor.is_some(), message=Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.poll_descriptor.open_some().vote_id == params.vote_id, message=Error.ErrorMessage.dao_invalid_vote_id())

        # Call the right voting function depending of the current phase
        sp.if self.data.vote_state == PHASE_1_OPT_OUT:
            self.phase_1_vote(params)
        sp.else:
            sp.if self.data.vote_state == PHASE_2_MAJORITY:
                self.phase_2_vote(params)
            sp.else:
                sp.failwith(Error.ErrorMessage.dao_no_vote_open())

        sp.emit(params, with_type=True, tag="Vote")

########################################################################################################################
# propose_callback
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def propose_callback(self, params):
        # Check type
        sp.set_type(params, sp.TNat)

        # Asserts
        sp.verify(self.data.vote_state == STARTING_PHASE_2, message=Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.poll_descriptor.is_some(), message=Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.phase_2_majority_vote_contract.open_some() == sp.sender,
                  message=Error.ErrorMessage.dao_invalid_voting_strat())

        # Update the poll data
        new_poll = sp.local('new_poll', self.data.poll_descriptor.open_some())
        new_poll.value.phase_2_vote_id = params
        self.data.poll_descriptor = sp.some(new_poll.value)

        # Change the state of the contract
        self.data.vote_state = PHASE_2_MAJORITY

########################################################################################################################
# end
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def end(self, params):
        # Check type
        sp.set_type(params, sp.TNat)

        # Asserts
        sp.verify(sp.sender == self.data.poll_leader.open_some(), message=Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.poll_descriptor.is_some(), message=Error.ErrorMessage.dao_no_vote_open())
        sp.verify(params == self.data.poll_descriptor.open_some().vote_id, message=Error.ErrorMessage.dao_invalid_vote_id())

        # Call the right end vote function depending on the phase of the vote
        sp.if self.data.vote_state == PHASE_1_OPT_OUT:
            self.phase_1_end()
        sp.else:
            sp.if self.data.vote_state == PHASE_2_MAJORITY:
                self.phase_2_end()
            sp.else:
                sp.failwith(Error.ErrorMessage.dao_no_vote_open())

        sp.emit(params, with_type=True, tag="End vote")

########################################################################################################################
# end_callback
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def end_callback(self, params):
        # Check type
        sp.set_type(params, sp.TRecord(voting_id=sp.TNat, voting_outcome=sp.TNat))

        # Asserts
        sp.verify(self.data.vote_state == ENDING_PHASE_2, message=Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.poll_descriptor.is_some(), message=Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.phase_2_majority_vote_contract.open_some() == sp.sender,
                  message=Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(~self.data.outcomes.contains(self.data.vote_id), message=Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(params.voting_id == self.data.poll_descriptor.open_some().phase_2_vote_id, message=Error.ErrorMessage.dao_invalid_voting_strat())

        # Record the vote outcome
        self.data.outcomes[self.data.poll_descriptor.open_some().vote_id] = sp.record(
            poll_outcome=params.voting_outcome,
            poll_data=self.data.poll_descriptor.open_some())

        # Close the vote
        self.close_vote(params.voting_outcome)

########################################################################################################################
# mutez_transfer
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def mutez_transfer(self, params):
        # Check type
        sp.set_type(params.destination, sp.TAddress)
        sp.set_type(params.amount, sp.TMutez)

        # Asserts
        sp.verify(self.data.admin == sp.sender, message=Error.ErrorMessage.unauthorized_user())

        # Send mutez
        sp.send(params.destination, params.amount)


################################################################
################################################################
# Helper functions
################################################################
################################################################
    def call(self, destination, arg):
        sp.transfer(arg, sp.mutez(0), destination)

    def callback_leader_start(self):
        leaderContractHandle = sp.contract(
            sp.TNat,
            self.data.poll_leader.open_some(),
            "propose_callback"
        ).open_some("Interface mismatch")

        leaderContractArg = self.data.poll_descriptor.open_some().vote_id
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

    def call_voting_strategy_vote(self, votes, address, vote_value):
        voteContractHandle = sp.contract(
            sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, voting_id=sp.TNat),
            self.data.phase_2_majority_vote_contract.open_some(),
            "vote"
        ).open_some("Interface mismatch")

        voteContractArg = sp.record(
                votes=votes, address=address, vote_value=vote_value, voting_id=self.data.poll_descriptor.open_some().phase_2_vote_id
            )
        self.call(voteContractHandle, voteContractArg)

    def call_voting_strategy_start(self, total_available_voters):
        voteContractHandle = sp.contract(
            sp.TNat,
            self.data.phase_2_majority_vote_contract.open_some(),
            "start"
        ).open_some("Interface mismatch")

        self.call(voteContractHandle, total_available_voters)

    def phase_1_vote(self, params):
        # Asserts
        sp.verify(~self.data.poll_descriptor.open_some().phase_1_voters.contains(params.address), message=Error.ErrorMessage.dao_vote_already_received())
        sp.verify(sp.level >= self.data.poll_descriptor.open_some().phase_1_voting_start_block, message=Error.ErrorMessage.dao_no_vote_open())
        sp.verify(sp.level <= self.data.poll_descriptor.open_some().phase_1_voting_end_block, message=Error.ErrorMessage.dao_no_vote_open())

        # Record the vote in phase 1
        new_poll = sp.local('new_poll', self.data.poll_descriptor.open_some())

        sp.if params.vote_value == VoteValue.NAY:
            new_poll.value.phase_1_vote_objection = new_poll.value.phase_1_vote_objection + params.votes
        sp.else:
            sp.failwith(Error.ErrorMessage.dao_invalid_vote_value())

        new_poll.value.phase_1_voters[params.address] = sp.record(vote_value=params.vote_value, level=sp.level, votes=params.votes)
        self.data.poll_descriptor = sp.some(new_poll.value)

    def phase_2_vote(self, params):
        # Asserts
        sp.verify(self.data.phase_2_majority_vote_contract.is_some(), message=Error.ErrorMessage.dao_not_registered())

        # It is phase 2 so call the vote function of the majority contract
        self.call_voting_strategy_vote(params.votes, params.address, params.vote_value)

    def phase_1_end(self):
        # Asserts
        sp.verify(sp.level > self.data.poll_descriptor.open_some().phase_1_voting_end_block, message=Error.ErrorMessage.dao_no_vote_open())

        # Compute the outcome of the vote in phase 1
        # If the proposal is rejected, go to phase 2. If not, record the vote and close.
        sp.if self.data.poll_descriptor.open_some().phase_1_vote_objection >= self.data.poll_descriptor.open_some().phase_1_objection_threshold:
            self.data.vote_state = STARTING_PHASE_2
            sp.verify(self.data.phase_2_majority_vote_contract.is_some(), message=Error.ErrorMessage.dao_not_registered())
            new_poll = sp.local('new_poll', self.data.poll_descriptor.open_some())
            new_poll.value.phase_2_needed = sp.bool(True)
            self.data.poll_descriptor = sp.some(new_poll.value)

            # Call voting strategy to start the poll
            self.call_voting_strategy_start(self.data.poll_descriptor.open_some().total_voters)
        sp.else:
            self.data.outcomes[self.data.poll_descriptor.open_some().vote_id] = sp.record(
                poll_outcome=PollOutcome.POLL_OUTCOME_PASSED,
                poll_data=self.data.poll_descriptor.open_some())
            self.close_vote(PollOutcome.POLL_OUTCOME_PASSED)

    def phase_2_end(self):
        # Asserts
        sp.verify(self.data.phase_2_majority_vote_contract.is_some(), message=Error.ErrorMessage.dao_not_registered())

        # Change the state of the contract
        self.data.vote_state = ENDING_PHASE_2

        # Call the majority contract to end the vote in phase 2
        self.call_voting_strategy_end()

    def call_voting_strategy_end(self):
        voteContractHandle = sp.contract(
            sp.TRecord(voting_id=sp.TNat),
            self.data.phase_2_majority_vote_contract.open_some(),
            "end"
        ).open_some("Interface mismatch")

        voteContractArg = sp.record(
                voting_id=self.data.poll_descriptor.open_some().phase_2_vote_id
            )
        self.call(voteContractHandle, voteContractArg)

    def close_vote(self, result):
        self.callback_leader_end(result)
        self.data.vote_state = NONE
        self.data.poll_descriptor = sp.none
        self.data.vote_id = self.data.vote_id + 1

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
    def get_historical_outcome_data(self, outcome_id):
        """Get historical data per outcome id.
        """
        sp.result(self.data.outcomes.get(outcome_id, message=Error.ErrorMessage.dao_invalid_outcome_id()))

    @sp.offchain_view(pure=True)
    def get_current_poll_data(self):
        """Get all current poll data if it exists.
        """
        sp.verify(self.data.poll_descriptor.is_some(), message=Error.ErrorMessage.dao_no_vote_open())
        sp.result(self.data.poll_descriptor.open_some())

    @sp.offchain_view(pure=True)
    def get_contract_state(self):
        """Get contract state
        """
        sp.result(self.data.vote_state)
