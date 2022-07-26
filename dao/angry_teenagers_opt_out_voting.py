import smartpy as sp

Error = sp.io.import_script_from_url("file:angry_teenagers_errors.py")
VoteValue = sp.io.import_script_from_url("file:dao/helper/angry_teenagers_dao_vote_value.py")
PollOutcome = sp.io.import_script_from_url("file:dao/helper/angry_teenagers_dao_poll_outcome.py")

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
  vote_value = sp.TNat,
  level = sp.TNat,
  votes = sp.TNat,
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
# - phase_2_voting_start_block: Tezos start block of the phase 2
# - phase_1_voters: Record of the voters data in phase 1 (phase 2 is recorded in the majority contract)
MAJORITY_POLL_DATA = sp.TRecord(
    phase_1_vote_objection = sp.TNat,
    phase_1_voting_start_block = sp.TNat,
    phase_1_voting_end_block = sp.TNat,
    vote_id = sp.TNat,
    total_voters = sp.TNat,
    phase_1_objection_threshold=sp.TNat,
    phase_2_needed = sp.TBool,
    phase_2_vote_id = sp.TNat,
    phase_2_voting_start_block = sp.TNat,
    phase_1_voters = sp.TMap(sp.TAddress, VOTE_RECORD_TYPE)
).layout(("phase_1_vote_objection",
          ("phase_1_voting_start_block",
           ("phase_1_voting_end_block",
            ("vote_id",
             ("total_voters",
              ("phase_1_objection_threshold",
                ("phase_2_needed",
                 ("phase_2_vote_id",
                  ("phase_2_voting_start_block", "phase_1_voters"))))))))))

# GOVERNANCE_PARAMETERS_TYPE
# Governance parameters are defined when the contract is deployed and can only be changed
# by the DAO
# - vote_delay_blocks: Amount of blocks to wait to start voting after the proposal is inject
# - vote_length_blocks: Length of the vote in blocks
# - percentage_for_objection: Percentage that needs to be reached to reject the proposal in phase 1 and go to phase 2
GOVERNANCE_PARAMETERS_TYPE = sp.TRecord(
  vote_delay_blocks = sp.TNat,
  vote_length_blocks = sp.TNat,
  percentage_for_objection = sp.TNat
).layout(("vote_delay_blocks",
          ("vote_length_blocks", "percentage_for_objection")))

# OUTCOMES_TYPE
# - poll_outcome: Outcome of the poll (PASSED or FAILED)
# - poll_data: See MAJORITY_POLL_DATA
OUTCOMES_TYPE = sp.TBigMap(sp.TNat, sp.TRecord(poll_outcome=sp.TNat, poll_data=MAJORITY_POLL_DATA))

PROPOSE_CALLBACK_TYPE = sp.TRecord(id=sp.TNat, snapshot_block=sp.TNat)

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
          "version": "1.0"
          , "description": (
              "Angry Teenagers DAO (opt out vote 1)."
          )
          , "interfaces": ["TZIP-016"]
          , "authors": [
              "EcoMint LTD"
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
# set_metadata
########################################################################################################################
    @sp.entry_point
    def set_administrator(self, params):
        sp.verify(sp.sender == self.data.admin, message=Error.ErrorMessage.unauthorized_user())
        self.data.admin = params

########################################################################################################################
# set_poll_leader
########################################################################################################################
    @sp.entry_point
    def set_poll_leader(self, address):
        # Asserts
        sp.verify(~self.data.poll_leader.is_some(), Error.ErrorMessage.dao_already_registered())
        sp.verify(sp.sender == self.data.admin, Error.ErrorMessage.unauthorized_user())

        # Set address
        self.data.poll_leader = sp.some(address)

########################################################################################################################
# set_phase_2_contract
########################################################################################################################
    @sp.entry_point
    def set_phase_2_contract(self, address):
        # Asserts
        sp.verify(~self.data.phase_2_majority_vote_contract.is_some(), Error.ErrorMessage.dao_already_registered())
        sp.verify(sp.sender == self.data.admin, Error.ErrorMessage.unauthorized_user())

        # Set address
        self.data.phase_2_majority_vote_contract = sp.some(address)

########################################################################################################################
# start
########################################################################################################################
    @sp.entry_point
    def start(self, total_available_voters):
        # Check type
        sp.set_type(total_available_voters, sp.TNat)

        # Asserts
        sp.verify(self.data.phase_2_majority_vote_contract.is_some(), Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(self.data.vote_state == NONE, Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(sp.sender == self.data.poll_leader.open_some(), Error.ErrorMessage.unauthorized_user())

        # Compute the objection threshold using the percentage and the number of possible voters
        objection_threshold = (total_available_voters * self.data.governance_parameters.percentage_for_objection) // SCALE

        # Compute the start and end block of the vote
        start_block = sp.level + self.data.governance_parameters.vote_delay_blocks
        end_block = start_block + self.data.governance_parameters.vote_length_blocks

        # Create the vote data
        self.data.poll_descriptor = sp.some(
            sp.record(
                phase_1_vote_objection = sp.nat(0),
                phase_1_voting_start_block = start_block,
                phase_1_voting_end_block = end_block,
                vote_id = self.data.vote_id,
                total_voters = total_available_voters,
                phase_1_objection_threshold = objection_threshold,
                phase_2_needed=sp.bool(False),
                phase_2_vote_id=sp.nat(0),
                phase_2_voting_start_block=sp.nat(0),
                phase_1_voters=sp.map(l={}, tkey=sp.TAddress, tvalue=VOTE_RECORD_TYPE)
        ))

        # Callback the poll leader
        self.callback_leader_start()

        # Change the state of the contract
        self.data.vote_state = PHASE_1_OPT_OUT

########################################################################################################################
# vote
########################################################################################################################
    @sp.entry_point
    def vote(self, params):
        # Check type
        sp.set_type(params, sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, vote_id=sp.TNat))

        # Asserts
        sp.verify(sp.sender == self.data.poll_leader.open_some(), Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.poll_descriptor.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.poll_descriptor.open_some().vote_id == params.vote_id, Error.ErrorMessage.dao_invalid_vote_id())

        # Call the right voting function depending of the current phase
        sp.if self.data.vote_state == PHASE_1_OPT_OUT:
            self.phase_1_vote(params)
        sp.else:
            sp.if self.data.vote_state == PHASE_2_MAJORITY:
                self.phase_2_vote(params)
            sp.else:
                sp.failwith(Error.ErrorMessage.dao_no_vote_open())

########################################################################################################################
# propose_callback
########################################################################################################################
    @sp.entry_point
    def propose_callback(self, params):
        # Check type
        sp.set_type(params, PROPOSE_CALLBACK_TYPE)

        # Asserts
        sp.verify(self.data.vote_state == STARTING_PHASE_2, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.poll_descriptor.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.phase_2_majority_vote_contract.open_some() == sp.sender,
                  Error.ErrorMessage.dao_invalid_voting_strat())

        # Update the poll data
        new_poll = sp.local('new_poll', self.data.poll_descriptor.open_some())
        new_poll.value.phase_2_vote_id = params.id
        new_poll.value.phase_2_voting_start_block = params.snapshot_block
        self.data.poll_descriptor = sp.some(new_poll.value)

        # Change the state of the contract
        self.data.vote_state = PHASE_2_MAJORITY

########################################################################################################################
# end
########################################################################################################################
    @sp.entry_point
    def end(self, params):
        # Check type
        sp.set_type(params, sp.TNat)

        # Asserts
        sp.verify(sp.sender == self.data.poll_leader.open_some(), Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.poll_descriptor.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(params == self.data.poll_descriptor.open_some().vote_id, Error.ErrorMessage.dao_invalid_vote_id())

        # Call the right end vote function depending on the phase of the vote
        sp.if self.data.vote_state == PHASE_1_OPT_OUT:
            self.phase_1_end()
        sp.else:
            sp.if self.data.vote_state == PHASE_2_MAJORITY:
                self.phase_2_end()
            sp.else:
                sp.failwith(Error.ErrorMessage.dao_no_vote_open())

########################################################################################################################
# end_callback
########################################################################################################################
    @sp.entry_point
    def end_callback(self, params):
        # Check type
        sp.set_type(params, sp.TRecord(voting_id=sp.TNat, voting_outcome=sp.TNat))

        # Asserts
        sp.verify(self.data.vote_state == ENDING_PHASE_2, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.poll_descriptor.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.phase_2_majority_vote_contract.open_some() == sp.sender,
                  Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(~self.data.outcomes.contains(self.data.vote_id), Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(params.voting_id == self.data.poll_descriptor.open_some().phase_2_vote_id, Error.ErrorMessage.dao_invalid_voting_strat())

        # Record the vote outcome
        self.data.outcomes[self.data.poll_descriptor.open_some().vote_id] = sp.record(
            poll_outcome=params.voting_outcome,
            poll_data=self.data.poll_descriptor.open_some())

        # Close the vote
        self.close_vote(params.voting_outcome)

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
            snapshot_block=self.data.poll_descriptor.open_some().phase_1_voting_start_block
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
            sp.TRecord (total_available_voters=sp.TNat),
            self.data.phase_2_majority_vote_contract.open_some(),
            "start"
        ).open_some("Interface mismatch")

        voteContractArg = sp.record(total_available_voters=total_available_voters)
        self.call(voteContractHandle, voteContractArg)

    def phase_1_vote(self, params):
        # Asserts
        sp.verify(~self.data.poll_descriptor.open_some().phase_1_voters.contains(params.address), Error.ErrorMessage.dao_vote_already_received())
        sp.verify(sp.level >= self.data.poll_descriptor.open_some().phase_1_voting_start_block, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(sp.level <= self.data.poll_descriptor.open_some().phase_1_voting_end_block, Error.ErrorMessage.dao_no_vote_open())

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
        sp.verify(self.data.phase_2_majority_vote_contract.is_some(), Error.ErrorMessage.dao_not_registered())

        # It is phase 2 so call the vote function of the majority contract
        self.call_voting_strategy_vote(params.votes, params.address, params.vote_value)

    def phase_1_end(self):
        # Asserts
        sp.verify(sp.level > self.data.poll_descriptor.open_some().phase_1_voting_end_block, Error.ErrorMessage.dao_no_vote_open())

        # Compute the outcome of the vote in phase 1
        # If the proposal is rejected, go to phase 2. If not, record the vote and close.
        sp.if self.data.poll_descriptor.open_some().phase_1_vote_objection >= self.data.poll_descriptor.open_some().phase_1_objection_threshold:
            self.data.vote_state = STARTING_PHASE_2
            sp.verify(self.data.phase_2_majority_vote_contract.is_some(), Error.ErrorMessage.dao_not_registered())
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
        sp.verify(self.data.phase_2_majority_vote_contract.is_some(), Error.ErrorMessage.dao_not_registered())

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

########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
########################################################################################################################
sp.add_compilation_target("AngryTeenagersOptOutVoting",
                          # TODO: Real address shall be used
                          DaoOptOutVoting(
                              admin=sp.address("tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"),
                              governance_parameters= sp.record(vote_delay_blocks = sp.nat(1),
                                                               vote_length_blocks = sp.nat(180),
                                                               percentage_for_objection = sp.nat(10)),
                              # TODO: Inject the right metadata
                              metadata = sp.utils.metadata_of_url("ipfs://QmXhW6XGaJn8Bmnm2bcjek6Pkk84eSMZt1GkJpJ51HVQXu")
                          ))

########################################################################################################################
########################################################################################################################
# Testing
########################################################################################################################
##################################################################################################################
# Unit Test ------------------------------------------------------------------------------------------------------------
########################################################################################################################
# Helper class for unit testing
########################################################################################################################
class TestHelper():
    def create_scenario(name):
        scenario = sp.test_scenario()
        scenario.h1(name)
        scenario.table_of_contents()
        return scenario

    def create_contracts(scenario, admin):
        c1 = DaoOptOutVoting(admin=admin.address,
                            governance_parameters=sp.record(vote_delay_blocks=sp.nat(10),
                                                             vote_length_blocks=sp.nat(180),
                                                             percentage_for_objection=sp.nat(10)),
                            metadata=sp.utils.metadata_of_url("https://example.com"))

        simulated_poll_leader_contract = SimulatedLeaderPoll(scenario)
        simulated_phase2_voting_contract = SimulatedPhase2Voting(scenario)
        scenario += c1
        scenario += simulated_poll_leader_contract
        scenario += simulated_phase2_voting_contract

        scenario.h2("Contracts:")
        scenario.p("c1: This contract to test (DaoMajorityVoting)")
        scenario.p("Poll Leader contract: Simulated poll leader")
        scenario.p("Phase 2 voting contract: Simulated phase 2 voting contract")

        return c1, simulated_poll_leader_contract, simulated_phase2_voting_contract

    def create_account(scenario):
        admin = sp.test_account("admin")
        alice = sp.test_account("alice")
        bob = sp.test_account("bob")
        john = sp.test_account("john")
        scenario.h2("Accounts:")
        scenario.show([admin, alice, bob, john])
        return admin, alice, bob, john

    def create_more_account(scenario):
        admin = sp.test_account("admin")
        alice = sp.test_account("alice")
        bob = sp.test_account("bob")
        john = sp.test_account("john")
        nat = sp.test_account("nat")
        ben = sp.test_account("ben")
        gabe = sp.test_account("gabe")
        gaston = sp.test_account("gaston")
        chris = sp.test_account("chris")
        scenario.h2("Accounts")
        scenario.show([admin, alice, bob, john])
        return admin, alice, bob, john, nat, ben, gabe, gaston, chris

class SimulatedLeaderPoll(sp.Contract):
    def __init__(self, scenario):
        self.init(
            propose_callback_called_times = sp.nat(0),
            propose_callback_id = sp.nat(100),
            propose_callback_snapshot_block = sp.nat(100),
            end_callback_called_times = sp.nat(0),
            end_callback_voting_id = sp.nat(100),
            end_callback_voting_outcome = sp.nat(100)
        )
        self.scenario = scenario

    @sp.entry_point()
    def propose_callback(self, params):
        sp.set_type(params, sp.TRecord(id=sp.TNat, snapshot_block=sp.TNat))
        self.data.propose_callback_called_times = self.data.propose_callback_called_times + 1
        self.data.propose_callback_id = params.id
        self.data.propose_callback_snapshot_block = params.snapshot_block

    @sp.entry_point()
    def end_callback(self, params):
        sp.set_type(params, sp.TRecord(voting_id=sp.TNat, voting_outcome=sp.TNat))
        self.data.end_callback_called_times = self.data.end_callback_called_times + 1
        self.data.end_callback_voting_id = params.voting_id
        self.data.end_callback_voting_outcome = params.voting_outcome


class SimulatedPhase2Voting(sp.Contract):
    def __init__(self, scenario):
        self.init_type(
            sp.TRecord(
                start_called_times=sp.TNat,
                total_available_voters=sp.TNat,
                vote_called_times=sp.TNat,
                last_votes=sp.TNat,
                last_address=sp.TOption(sp.TAddress),
                last_vote_value=sp.TNat,
                last_vote_id=sp.TNat,
                end_called_times = sp.TNat,
                end_vote_id = sp.TNat
            )
        )

        self.init(
            start_called_times = sp.nat(0),
            total_available_voters = sp.nat(100),
            vote_called_times = sp.nat(0),
            last_votes = sp.nat(0),
            last_address = sp.none,
            last_vote_value = sp.nat(100),
            last_vote_id = sp.nat(100),
            end_called_times = sp.nat(0),
            end_vote_id = sp.nat(0)
        )

        self.scenario = scenario

    @sp.entry_point()
    def start(self, params):
        sp.set_type(params, sp.TRecord(total_available_voters=sp.TNat))
        self.data.start_called_times = self.data.start_called_times + 1
        self.data.total_available_voters = params.total_available_voters

    @sp.entry_point()
    def vote(self, params):
        sp.set_type(params, sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, voting_id=sp.TNat))
        self.data.vote_called_times = self.data.vote_called_times + 1
        self.data.last_votes = params.votes
        self.data.last_address = sp.some(params.address)
        self.data.last_vote_value = params.vote_value
        self.data.last_vote_id = params.voting_id

    @sp.entry_point()
    def end(self, params):
        sp.set_type(params, sp.TRecord(voting_id=sp.TNat))
        self.data.end_called_times = self.data.end_called_times + 1
        self.data.end_vote_id = params.voting_id


# Unit tests -------------------------------------------------------------------------------------------------------
########################################################################################################################
# unit_test_initial_storage
########################################################################################################################
def unit_test_mutez_transfer(is_default=True):
    @sp.add_test(name="unit_test_mutez_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mutez_transfer")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the mutez_transfer entrypoint.  (Who: Only for the admin)")
        scenario.p("This entrypoint is called byt the admin to extract fund on the contract. Normally no funds are supposed to be held in the contract however if something bad happens or somebody makes a mistake transfer, we still want to have the ability to extract the fund.")

        scenario.p("1. Add fund to the contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin, amount=sp.mutez(300000000))

        scenario.p("2. Check that only the admin can call this entrypoint")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=alice)
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=bob)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(200000000))).run(valid=False, sender=john)

        scenario.p("3. Check the function extracts the fund as expected")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=True, sender=admin)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(100000000))).run(valid=True, sender=admin)

        scenario.p("3. Check no fund are remaining")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(100000000))).run(valid=False, sender=admin)

# Description: Test the storage is initialized as expected.
def unit_test_initial_storage(is_default = True):
    @sp.add_test(name="unit_test_initial_storage", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_initial_storage")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the storage is initialized as expected.")

        scenario.p("1. Read each entry of the storage of the c1 contract and check it is initialized as expected")
        scenario.verify(c1.data.admin == admin.address)
        scenario.verify(c1.data.vote_id == 0)
        scenario.verify(c1.data.vote_state == NONE)
        scenario.verify(~c1.data.phase_2_majority_vote_contract.is_some())
        scenario.verify(~c1.data.poll_leader.is_some())
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.governance_parameters.vote_delay_blocks == sp.nat(10))
        scenario.verify(c1.data.governance_parameters.vote_length_blocks == sp.nat(180))
        scenario.verify(c1.data.governance_parameters.percentage_for_objection == sp.nat(10))
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

def unit_test_set_administrator(is_default = True):
    @sp.add_test(name="unit_test_set_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the set_administrator entrypoint. (Who: Only for the admin)")
        scenario.p("This function is used to change the administrator of the contract.")

        scenario.p("1. Check only admin can call this entrypoint (i.e only the current admin can change the admin)")
        c1.set_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_administrator(admin.address).run(valid=False, sender=bob)
        c1.set_administrator(bob.address).run(valid=False, sender=john)

        scenario.p("2. Check admin remains admin if he gives the admin right to himself.")
        c1.set_administrator(admin.address).run(valid=True, sender=admin)
        c1.set_administrator(alice.address).run(valid=False, sender=bob)
        c1.set_administrator(admin.address).run(valid=False, sender=john)
        c1.set_administrator(bob.address).run(valid=False, sender=alice)

        scenario.p("3. Check admin is not admin if he gives admin right to Alice. Check Alice is then admin.")
        c1.set_administrator(alice.address).run(valid=True, sender=admin)

        scenario.p("4. Check Alice is now admin.")
        c1.set_administrator(admin.address).run(valid=False, sender=admin)
        c1.set_administrator(bob.address).run(valid=False, sender=admin)

        scenario.p("5. Check Alice can give admin rights to Bob and Bob is then admin.")
        c1.set_administrator(bob.address).run(valid=True, sender=alice)
        scenario.verify(c1.data.admin == bob.address)

def unit_test_set_poll_leader(is_default = True):
    @sp.add_test(name="unit_test_set_poll_leader", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_poll_leader")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the set_poll_leader entrypoint.")

        scenario.p("1. Only admin can set the entrypoint")
        scenario.verify(~c1.data.poll_leader.is_some())
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=False, sender=bob)
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=False, sender=alice)
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=False, sender=john)
        scenario.verify(~c1.data.poll_leader.is_some())
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        scenario.verify(c1.data.poll_leader.open_some() == simulated_poll_leader_contract.address)

        scenario.p("2. Address can be set only one time")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=False, sender=admin)

def unit_test_set_phase_2_contract(is_default = True):
    @sp.add_test(name="unit_test_set_phase_2_contract", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_phase_2_contract")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the set_phase_2_contract entrypoint.")

        scenario.p("1. Only admin can set the entrypoint")
        scenario.verify(~c1.data.poll_leader.is_some())
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=False, sender=bob)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=False, sender=alice)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=False, sender=john)
        scenario.verify(~c1.data.poll_leader.is_some())
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)
        scenario.verify(c1.data.phase_2_majority_vote_contract.open_some() == simulated_phase2_voting_contract.address)

        scenario.p("2. Address can be set only one time")
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=False, sender=admin)

# Description: Test the start function.
def unit_test_start(is_default = True):
    @sp.add_test(name="unit_test_start", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_start")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the start function.")

        total_available_voters = sp.nat(5233)

        scenario.p("1. Cannot start if no phase 2 contract is registered")
        c1.start(total_available_voters).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("2. Register phase2 contract")
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("3. Cannot start if no poll leader contract is registered")
        c1.start(total_available_voters).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("5. Only poll_leader can start the polling")
        c1.start(total_available_voters).run(valid=False, sender=alice)

        scenario.p("3. Finally start")
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_id == 100)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_snapshot_block == 100)
        scenario.verify(c1.data.vote_state == NONE)
        c1.start(total_available_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Check it is started")
        scenario.verify(c1.data.poll_descriptor.is_some())
        start_block = sp.level + c1.data.governance_parameters.vote_delay_blocks
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_start_block == start_block)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_end_block == start_block + c1.data.governance_parameters.vote_length_blocks)
        phase_1_objection_threshold = (total_available_voters * c1.data.governance_parameters.percentage_for_objection) // SCALE
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_objection_threshold == phase_1_objection_threshold)
        scenario.verify(c1.data.poll_descriptor.open_some().total_voters == total_available_voters)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_needed == sp.bool(False))
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_voting_start_block == 0)
        scenario.verify(c1.data.vote_state == PHASE_1_OPT_OUT)

        scenario.p("4. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_snapshot_block == start_block)

# Description: Test the vote function.
def unit_test_vote(is_default = True):
    @sp.add_test(name="unit_test_vote", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_vote")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the vote function.")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Cannot vote is not poll open")
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Only poll leader can send the vote")
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=john.address)

        scenario.p("5. Cannot vote if vote_id is invalid")
        vote_param_invalid_vote_id = sp.record(votes=sp.nat(10), address=alice.address, vote_value=VoteValue.YAY , vote_id=sp.nat(1))
        c1.vote(vote_param_invalid_vote_id).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("6. Start block shall be reached to start the vote")
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=simulated_poll_leader_contract.address)
        start_block = c1.data.governance_parameters.vote_delay_blocks
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("7. Successfully vote nay")
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("8. Alice cannot vote anymore")
        c1.vote(alice_vote_param_valid_nay).run().run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("9. Only nay votes are accepted in phase 1")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(36), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        chris_vote_param_valid_nay = sp.record(votes=sp.nat(36), address=chris.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(100), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(250), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        ben_vote_param_valid_nay = sp.record(votes=sp.nat(250), address=ben.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)
        c1.vote(chris_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=False, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("10. Vote value is invalid")
        bob_invalid_vote_value = sp.record(votes=sp.nat(1), address=bob.address, vote_value=3, vote_id=sp.nat(0))
        c1.vote(bob_invalid_vote_value).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("11. Admin successfull vote")
        admin_valid_vote = sp.record(votes=sp.nat(30), address=admin.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(admin_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=(start_block + 50))

        scenario.p("12. Bob successfull vote")
        bob_valid_vote = sp.record(votes=sp.nat(112), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        end_block = start_block + c1.data.governance_parameters.vote_length_blocks
        c1.vote(bob_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block)

        scenario.p("13. Bob can only vote one time")
        c1.vote(bob_valid_vote).run().run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("14. John cannot vote anymore. It is too late.")
        john_valid_vote = sp.record(votes=sp.nat(30), address=john.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(john_valid_vote).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block + 1)
        c1.vote(john_valid_vote).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block + 30)

        scenario.p("15. Check votes are counted as expected")
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 538)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 6)

# Description: Test the end function.
def unit_test_end_phase1_ok_1(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_ok_1", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_ok_1")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with successful phase 1 (1).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Cannot close when time is not elapsed")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block)

        scenario.p("5. Only poll_leader can close")
        c1.end(0).run(valid=False, sender=admin.address, level=end_block + 1)

        scenario.p("6. Let's close now")
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("7. Poll is closed")
        scenario.verify(c1.data.vote_state == NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("8. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("9. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_vote_objection == 9)
        scenario.verify(c1.data.outcomes[0].poll_data.total_voters == 100)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_objection_threshold == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_needed == sp.bool(False))
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.phase_1_voters) == 2)

def unit_test_end_phase1_ok_2(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_ok_2", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_ok_2")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with successful phase 1 (2).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(100000).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7999), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2000), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("8. Poll is closed")
        scenario.verify(c1.data.vote_state == NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("9. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("10. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_vote_objection == 9999)
        scenario.verify(c1.data.outcomes[0].poll_data.total_voters == 100000)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_objection_threshold == 10000)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_needed == sp.bool(False))
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.phase_1_voters) == 2)

def unit_test_end_phase1_ok_3(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_ok_3", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_ok_3")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with successful phase 1 (3).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(5233).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(520), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("8. Poll is closed")
        scenario.verify(c1.data.vote_state == NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("9. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("10. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_vote_objection == 522)
        scenario.verify(c1.data.outcomes[0].poll_data.total_voters == 5233)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_objection_threshold == 523)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_needed == sp.bool(False))
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.phase_1_voters) == 2)

def unit_test_end_phase1_ok_4(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_ok_4", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_ok_4")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with successful phase 1 (4).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(5233).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(27), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(38), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("8. Poll is closed")
        scenario.verify(c1.data.vote_state == NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("9. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("10. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_vote_objection == 65)
        scenario.verify(c1.data.outcomes[0].poll_data.total_voters == 5233)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_objection_threshold == 523)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_needed == sp.bool(False))
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.phase_1_voters) == 2)

def unit_test_end_phase1_nok_1(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_nok_1", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_nok_1")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with not passed phase 1 (1).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        total_voters = 100
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(3), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("5. Check the expected callback has been called")
        scenario.p("The end callback is not called as we transition to phase 2")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.start_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.total_available_voters == total_voters)

        scenario.p("6. Poll is still opened and has transitioned to phase 2")
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.vote_state == STARTING_PHASE_2)
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 10)
        scenario.verify(c1.data.poll_descriptor.open_some().total_voters == total_voters)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_start_block == 10)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_end_block == 190)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_objection_threshold == 10)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 2)

def unit_test_end_phase1_nok_2(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_nok_2", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_nok_2")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with not passed phase 1 (2).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        total_voters = 100000
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7999), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2001), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("5. Check the expected callback has been called")
        scenario.p("The end callback is not called as we transition to phase 2")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.start_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.total_available_voters == total_voters)

        scenario.p("6. Poll is still opened and has transitioned to phase 2")
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.vote_state == STARTING_PHASE_2)
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 10000)
        scenario.verify(c1.data.poll_descriptor.open_some().total_voters == total_voters)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_start_block == 10)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_end_block == 190)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_objection_threshold == 10000)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 2)

def unit_test_end_phase1_nok_3(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_nok_3", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_nok_3")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with not passed phase 1 (3).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        total_voters = 5233
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(521), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("5. Check the expected callback has been called")
        scenario.p("The end callback is not called as we transition to phase 2")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.start_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.total_available_voters == total_voters)

        scenario.p("6. Poll is still opened and has transitioned to phase 2")
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.vote_state == STARTING_PHASE_2)
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 523)
        scenario.verify(c1.data.poll_descriptor.open_some().total_voters == total_voters)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_start_block == 10)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_end_block == 190)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_objection_threshold == 523)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 2)

def unit_test_end_phase1_nok_4(is_default = True):
    @sp.add_test(name="unit_test_end_phase1_nok_4", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase1_nok_4")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with not passed phase 1 (3).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        total_voters = 5233
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(1238), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(521), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("5. Check the expected callback has been called")
        scenario.p("The end callback is not called as we transition to phase 2")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.start_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.total_available_voters == total_voters)

        scenario.p("6. Poll is still opened and has transitioned to phase 2")
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.vote_state == STARTING_PHASE_2)
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 1759)
        scenario.verify(c1.data.poll_descriptor.open_some().total_voters == total_voters)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_start_block == 10)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_end_block == 190)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_objection_threshold == 523)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 2)

def unit_test_end_phase2_vote(is_default = True):
    @sp.add_test(name="unit_test_end_phase2_vote", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase2_vote")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the phase2 of the poll (vote).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. propose_callback can only be called when in state STARTING_PHASE_2")
        param_propose_callback_1 = sp.record(id=1, snapshot_block=sp.level)
        c1.propose_callback(param_propose_callback_1).run(valid=False, sender=simulated_phase2_voting_contract.address)

        scenario.p("3. Start poll")
        total_voters = 5233
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(1238), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(521), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("5. propose_callback can only be called when in state STARTING_PHASE_2")
        param_propose_callback_2 = sp.record(id=1, snapshot_block=sp.level)
        c1.propose_callback(param_propose_callback_2).run(valid=False, sender=simulated_phase2_voting_contract.address)

        scenario.p("6. Let's close now and start phase 2")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)
        scenario.verify(c1.data.vote_state == STARTING_PHASE_2)

        scenario.p("7. Cannot vote when the propose_callback has not been called")
        alice_vote_param_valid_yay = sp.record(votes=sp.nat(1238), address=alice.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("8. Only the phase 2 contract can call the propose_callback.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=False, sender=admin.address)

        scenario.p("9. The majority voting contract will call the propose_callback. Let's simulate this call.")
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.data.vote_state == PHASE_2_MAJORITY)

        scenario.p("10. Verify poll_descriptor data are as expected")
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 1759)
        scenario.verify(c1.data.poll_descriptor.open_some().total_voters == total_voters)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_start_block == 10)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_end_block == 190)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_objection_threshold == 523)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_vote_id == 1)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_voting_start_block == snapshot_block)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 2)

        scenario.p("11. Vote")
        alice_vote_param_valid_yay = sp.record(votes=sp.nat(200), address=alice.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=snapshot_block)

        scenario.p("12. Verify callback calls")
        scenario.verify(simulated_phase2_voting_contract.data.vote_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.last_votes == 200)
        scenario.verify(simulated_phase2_voting_contract.data.last_address.open_some() == alice.address)
        scenario.verify(simulated_phase2_voting_contract.data.last_vote_id == 1)
        scenario.verify(simulated_phase2_voting_contract.data.last_vote_value == VoteValue.YAY)

def unit_test_end_phase2_end_ok(is_default = True):
    @sp.add_test(name="unit_test_end_phase2_end_ok", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase2_end_ok")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the phase2 of the poll (end -- Ok).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("3. Start phase2")
        total_voters = 100
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("4. The majority voting contract will call the propose_callback. Let's simulate this call.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.data.vote_state == PHASE_2_MAJORITY)

        scenario.p("5. end_callback cann only be called in state ENDING_PHASE_2.")
        params_end_callback = sp.record(voting_id=sp.nat(1), voting_outcome=PollOutcome.POLL_OUTCOME_PASSED)
        c1.end_callback(params_end_callback).run(valid=False, sender=simulated_phase2_voting_contract.address)

        scenario.p("6. Simulate end of phase with successful outcome")
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.data.vote_state == ENDING_PHASE_2)

        scenario.p("7. Check expected callbacks are called")
        scenario.verify(simulated_phase2_voting_contract.data.end_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.end_vote_id == 1)

        scenario.p("8. Only the phase2 contract can call the end_callback.")
        c1.end_callback(params_end_callback).run(valid=False, sender=admin.address)

        scenario.p("9. end_callback can only be called with valid id.")
        params_end_callback_invalid_id = sp.record(voting_id=sp.nat(0), voting_outcome=PollOutcome.POLL_OUTCOME_PASSED)
        c1.end_callback(params_end_callback_invalid_id).run(valid=False, sender=admin.address)

        scenario.p("10. In return the majority contract will call back this contract to give the result. Let's simulate this.")
        c1.end_callback(params_end_callback).run(valid=True, sender=simulated_phase2_voting_contract.address)

        scenario.p("7. Check expected callbacks are called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("8. Check outcome of this contract")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_vote_objection == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.total_voters == 100)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_objection_threshold == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_vote_id == 1)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_voting_start_block == snapshot_block)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.phase_1_voters) == 1)
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.vote_state == NONE)

        scenario.p("9. Start a new poll")
        c1.start(5233).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("10. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks + sp.level
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(27), address=alice.address, vote_value=VoteValue.NAY,
                                               vote_id=sp.nat(1))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address,
                                                level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(38), address=bob.address, vote_value=VoteValue.NAY,
                                             vote_id=sp.nat(1))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address,
                                              level=start_block)

        scenario.p("11. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("12. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_vote_objection == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.total_voters == 100)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_objection_threshold == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_vote_id == 1)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.phase_1_voters) == 1)
        scenario.verify(c1.data.outcomes.contains(1))
        scenario.verify(c1.data.outcomes[1].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[1].poll_data.phase_1_vote_objection == 65)
        scenario.verify(c1.data.outcomes[1].poll_data.total_voters == 5233)
        scenario.verify(c1.data.outcomes[1].poll_data.vote_id == 1)
        scenario.verify(c1.data.outcomes[1].poll_data.phase_1_objection_threshold == 523)
        scenario.verify(c1.data.outcomes[1].poll_data.phase_2_needed == sp.bool(False))
        scenario.verify(c1.data.outcomes[1].poll_data.phase_2_vote_id == 0)
        scenario.verify(c1.data.outcomes[1].poll_data.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(c1.data.outcomes[1].poll_data.phase_1_voters) == 2)

def unit_test_end_phase2_end_nok(is_default = True):
    @sp.add_test(name="unit_test_end_phase2_end_nok", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_phase2_end_nok")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the phase2 of the poll (end -- Ok).")

        scenario.p("1. Register poll_leader and phase2 contracts")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("3. Start phase2")
        total_voters = 100
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("4. The majority voting contract will call the propose_callback. Let's simulate this call.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.data.vote_state == PHASE_2_MAJORITY)

        scenario.p("5. end_callback cann only be called in state ENDING_PHASE_2.")
        params_end_callback = sp.record(voting_id=sp.nat(1), voting_outcome=PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(params_end_callback).run(valid=False, sender=simulated_phase2_voting_contract.address)

        scenario.p("6. Simulate end of phase with successful outcome")
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.data.vote_state == ENDING_PHASE_2)

        scenario.p("7. In return the majority contract will call back this contract to give the result. Let's simulate this.")
        c1.end_callback(params_end_callback).run(valid=True, sender=simulated_phase2_voting_contract.address)

        scenario.p("8. Check outcome of this contract")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_vote_objection == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.total_voters == 100)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_1_objection_threshold == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_needed == sp.bool(True))
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_vote_id == 1)
        scenario.verify(c1.data.outcomes[0].poll_data.phase_2_voting_start_block == snapshot_block)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.phase_1_voters) == 1)
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.vote_state == NONE)

def unit_test_offchain_views(is_default = True):
    @sp.add_test(name="unit_test_offchain_views", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_offchain_views")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test all the offchain views.")

        scenario.p("1. Register poll_leader and phase2 contracts")
        scenario.verify(c1.get_contract_state() == NONE)
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == PHASE_1_OPT_OUT)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=bob.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Get and check poll data")
        poll_data_0 = c1.get_current_poll_data()
        scenario.verify(poll_data_0.phase_1_vote_objection == 9)
        scenario.verify(poll_data_0.total_voters == 100)
        scenario.verify(poll_data_0.phase_1_voting_start_block == 10)
        scenario.verify(poll_data_0.phase_1_voting_end_block == 190)
        scenario.verify(poll_data_0.vote_id == 0)
        scenario.verify(poll_data_0.phase_1_objection_threshold == 10)
        scenario.verify(poll_data_0.phase_2_needed == sp.bool(False))
        scenario.verify(poll_data_0.phase_2_vote_id == 0)
        scenario.verify(poll_data_0.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(poll_data_0.phase_1_voters) == 2)

        scenario.p("5. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        scenario.verify(c1.get_contract_state() == PHASE_1_OPT_OUT)
        scenario.verify(c1.get_number_of_historical_outcomes() == 0)
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)
        scenario.verify(c1.get_contract_state() == NONE)

        scenario.p("7. Poll is closed")
        scenario.verify(c1.data.vote_state == NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("8. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 1)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(outcome_0.poll_data.phase_1_vote_objection == 9)
        scenario.verify(outcome_0.poll_data.total_voters == 100)
        scenario.verify(outcome_0.poll_data.phase_1_voting_start_block == 10)
        scenario.verify(outcome_0.poll_data.phase_1_voting_end_block == 190)
        scenario.verify(outcome_0.poll_data.vote_id == 0)
        scenario.verify(outcome_0.poll_data.phase_1_objection_threshold == 10)
        scenario.verify(outcome_0.poll_data.phase_2_needed == sp.bool(False))
        scenario.verify(outcome_0.poll_data.phase_2_vote_id == 0)
        scenario.verify(outcome_0.poll_data.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(outcome_0.poll_data.phase_1_voters) == 2)

        scenario.p("9. Start poll with phase 2 this time")
        total_voters = 100
        c1.start(total_voters).run(valid=True, sender=simulated_poll_leader_contract.address)
        start_block = c1.data.governance_parameters.vote_delay_blocks + sp.level
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(1))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("10. The majority voting contract will call the propose_callback. Let's simulate this call.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.get_contract_state() == PHASE_2_MAJORITY)

        scenario.p("11. Simulate end of phase with successful outcome")
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == ENDING_PHASE_2)

        scenario.p("12. In return the majority contract will call back this contract to give the result. Let's simulate this.")
        params_end_callback = sp.record(voting_id=sp.nat(1), voting_outcome=PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(params_end_callback).run(valid=True, sender=simulated_phase2_voting_contract.address)

        scenario.p("13. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 2)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(outcome_0.poll_data.phase_1_vote_objection == 9)
        scenario.verify(outcome_0.poll_data.total_voters == 100)
        scenario.verify(outcome_0.poll_data.phase_1_voting_start_block == 10)
        scenario.verify(outcome_0.poll_data.phase_1_voting_end_block == 190)
        scenario.verify(outcome_0.poll_data.vote_id == 0)
        scenario.verify(outcome_0.poll_data.phase_1_objection_threshold == 10)
        scenario.verify(outcome_0.poll_data.phase_2_needed == sp.bool(False))
        scenario.verify(outcome_0.poll_data.phase_2_vote_id == 0)
        scenario.verify(outcome_0.poll_data.phase_2_voting_start_block == 0)
        scenario.verify(sp.len(outcome_0.poll_data.phase_1_voters) == 2)

        outcome_1 = c1.get_historical_outcome_data(1)
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(outcome_1.poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(outcome_1.poll_data.phase_1_vote_objection == 10)
        scenario.verify(outcome_1.poll_data.total_voters == 100)
        scenario.verify(outcome_1.poll_data.vote_id == 1)
        scenario.verify(outcome_1.poll_data.phase_1_objection_threshold == 10)
        scenario.verify(outcome_1.poll_data.phase_2_needed == sp.bool(True))
        scenario.verify(outcome_1.poll_data.phase_2_vote_id == 1)
        scenario.verify(sp.len(outcome_1.poll_data.phase_1_voters) == 1)
        scenario.verify(c1.get_contract_state() == NONE)


unit_test_initial_storage()
unit_test_set_administrator()
unit_test_set_poll_leader()
unit_test_set_phase_2_contract()
unit_test_start()
unit_test_vote()
unit_test_end_phase1_ok_1()
unit_test_end_phase1_ok_2()
unit_test_end_phase1_ok_3()
unit_test_end_phase1_ok_4()
unit_test_end_phase1_nok_1()
unit_test_end_phase1_nok_2()
unit_test_end_phase1_nok_3()
unit_test_end_phase1_nok_4()
unit_test_end_phase2_vote()
unit_test_end_phase2_end_ok()
unit_test_end_phase2_end_nok()
unit_test_offchain_views()