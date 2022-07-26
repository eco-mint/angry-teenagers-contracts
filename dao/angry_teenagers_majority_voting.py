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
              "Angry Teenagers DAO (majority vote 1)."
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

########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
########################################################################################################################
sp.add_compilation_target("AngryTeenagersMajorityVoting",
                          # TODO: Real address shall be used
                          DaoMajorityVoting(
                              admin=sp.address("tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"),
                              current_dynamic_quorum_value=sp.nat(2000),
                              governance_parameters= sp.record(vote_delay_blocks = sp.nat(1),
                                                               vote_length_blocks = sp.nat(180),
                                                               percentage_for_supermajority = sp.nat(80),
                                                               fixed_quorum_percentage = sp.nat(25),
                                                               fixed_quorum = sp.bool(False),
                                                               quorum_cap = sp.record(lower=sp.nat(1), upper=sp.nat(5800))),
                              # TODO: Inject the right metadata
                              metadata = sp.utils.metadata_of_url("ipfs://QmNtph2DjrVcK9KXrNRsPSwMPpBpZjY7Ti6ceNcrbor45n")
                          ))

sp.add_compilation_target("AngryTeenagersOptOutMajorityVoting",
                          # TODO: Real address shall be used
                          DaoMajorityVoting(
                              admin=sp.address("tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"),
                              current_dynamic_quorum_value=sp.nat(2000),
                              governance_parameters= sp.record(vote_delay_blocks = sp.nat(1),
                                                               vote_length_blocks = sp.nat(180),
                                                               percentage_for_supermajority = sp.nat(80),
                                                               fixed_quorum_percentage = sp.nat(25),
                                                               fixed_quorum = sp.bool(True),
                                                               quorum_cap = sp.record(lower=sp.nat(1), upper=sp.nat(5800))),
                              # TODO: Inject the right metadata
                              metadata = sp.utils.metadata_of_url("ipfs://QmNtph2DjrVcK9KXrNRsPSwMPpBpZjY7Ti6ceNcrbor45n")
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

    def create_contracts(scenario, admin, with_fixed_quorum = False):
        if with_fixed_quorum:
            c1 = DaoMajorityVoting(admin=admin.address,
                                   current_dynamic_quorum_value=sp.nat(2000),
                                   governance_parameters=sp.record(
                                        vote_delay_blocks = sp.nat(10),
                                        vote_length_blocks = sp.nat(180),
                                        percentage_for_supermajority = sp.nat(85),
                                        fixed_quorum_percentage = sp.nat(25),
                                        fixed_quorum = sp.bool(True),
                                        quorum_cap = sp.record(lower=sp.nat(500), upper=sp.nat(4500))),
                                   metadata=sp.utils.metadata_of_url("https://example.com"))
        else:
            c1 = DaoMajorityVoting(admin=admin.address,
                                   current_dynamic_quorum_value=sp.nat(2000),
                                   governance_parameters=sp.record(
                                        vote_delay_blocks = sp.nat(10),
                                        vote_length_blocks = sp.nat(180),
                                        percentage_for_supermajority = sp.nat(85),
                                        fixed_quorum_percentage = sp.nat(25),
                                        fixed_quorum = sp.bool(False),
                                        quorum_cap = sp.record(lower=sp.nat(500), upper=sp.nat(4500))),
                                   metadata=sp.utils.metadata_of_url("https://example.com"))
        simulated_poll_leader_contract = SimulatedLeaderPoll(scenario)
        scenario += c1
        scenario += simulated_poll_leader_contract

        scenario.h2("Contracts:")
        scenario.p("c1: This contract to test (DaoMajorityVoting)")
        scenario.p("Poll Leader contract: Simulated poll leader")

        return c1, simulated_poll_leader_contract

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




# Unit tests -------------------------------------------------------------------------------------------------------
########################################################################################################################
# unit_test_initial_storage
########################################################################################################################
# Description: Test the storage is initialized as expected.
def unit_test_initial_storage(is_default = True):
    @sp.add_test(name="unit_test_initial_storage", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_initial_storage")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the storage is initialized as expected.")

        scenario.p("1. Read each entry of the storage of the c1 contract and check it is initialized as expected")
        scenario.verify(c1.data.admin == admin.address)
        scenario.verify(~c1.data.poll_leader.is_some())
        scenario.verify(c1.data.vote_id == 0)
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.vote_state == 0)
        scenario.verify(c1.data.governance_parameters.vote_delay_blocks == sp.nat(10))
        scenario.verify(c1.data.governance_parameters.vote_length_blocks == sp.nat(180))
        scenario.verify(c1.data.governance_parameters.percentage_for_supermajority == sp.nat(85))
        scenario.verify(c1.data.governance_parameters.fixed_quorum_percentage == sp.nat(25))
        scenario.verify(c1.data.governance_parameters.fixed_quorum == sp.bool(False))
        scenario.verify(c1.data.governance_parameters.quorum_cap.lower == sp.nat(500))
        scenario.verify(c1.data.governance_parameters.quorum_cap.upper == sp.nat(4500))

        scenario.verify(c1.data.current_dynamic_quorum_value == sp.nat(2000))
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

def unit_test_set_administrator(is_default = True):
    @sp.add_test(name="unit_test_set_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

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
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

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

# Description: Test the start function.
def unit_test_start_with_dynamic_quorum(is_default = True):
    @sp.add_test(name="unit_test_start_with_dynamic_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_start_with_dynamic_quorum")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the start function with a dynamic quorum.")

        total_available_voters = sp.nat(100)

        scenario.p("1. Cannot start if not poll leader contract are registered")
        c1.start(total_available_voters).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("2. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("3. Only poll_leader can start the polling")
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
        scenario.verify(c1.data.poll_descriptor.open_some().vote_nay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_yay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_abstain == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().total_votes == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().voters) == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().quorum == c1.data.current_dynamic_quorum_value)
        start_block = sp.level + c1.data.governance_parameters.vote_delay_blocks
        scenario.verify(c1.data.poll_descriptor.open_some().voting_start_block == start_block)
        scenario.verify(c1.data.poll_descriptor.open_some().voting_end_block == start_block + c1.data.governance_parameters.vote_length_blocks)
        scenario.verify(c1.data.vote_state == IN_PROGRESS)

        scenario.p("4. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_snapshot_block == start_block)

# Description: Test the start function.
def unit_test_start_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_start_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_start_with_fixed_quorum")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the start function with a fixed quorum.")

        total_available_voters = sp.nat(100)

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start with fixed quorum")
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_id == 100)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_snapshot_block == 100)
        scenario.verify(c1.data.vote_state == NONE)
        c1.start(total_available_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Check it is started")
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().vote_nay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_yay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_abstain == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().total_votes == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().voters) == 0)
        fixed_quorum = (total_available_voters * c1.data.governance_parameters.fixed_quorum_percentage) // SCALE
        scenario.verify(c1.data.poll_descriptor.open_some().quorum == fixed_quorum)
        start_block = sp.level + c1.data.governance_parameters.vote_delay_blocks
        scenario.verify(c1.data.poll_descriptor.open_some().voting_start_block == start_block)
        scenario.verify(c1.data.poll_descriptor.open_some().voting_end_block == start_block + c1.data.governance_parameters.vote_length_blocks)
        scenario.verify(c1.data.vote_state == IN_PROGRESS)

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
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the vote function.")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Cannot vote is not poll open")
        alice_vote_param_valid_yay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Only poll leader can send the vote")
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=john.address)

        scenario.p("5. Cannot vote if vote_id is invalid")
        vote_param_invalid_vote_id = sp.record(votes=sp.nat(10), address=alice.address, vote_value=VoteValue.YAY , vote_id=sp.nat(1))
        c1.vote(vote_param_invalid_vote_id).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("6. Start block shall be reached to start the vote")
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)
        start_block = c1.data.governance_parameters.vote_delay_blocks
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("7. Successfully vote yay")
        c1.vote(alice_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("8. Alice cannot vote anymore")
        c1.vote(alice_vote_param_valid_yay).run().run(valid=False, sender=simulated_poll_leader_contract.address)
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(1), address=alice.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        alice_vote_param_valid_abstain = sp.record(votes=sp.nat(2), address=alice.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=simulated_poll_leader_contract.address)
        c1.vote(alice_vote_param_valid_abstain).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("9. Chris votes yay, Gabe votes nay and Ben votes abstain")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(36), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(100), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(250), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("10. Vote value is invalid")
        bob_invalid_vote_value = sp.record(votes=sp.nat(1), address=bob.address, vote_value=3, vote_id=sp.nat(0))
        c1.vote(bob_invalid_vote_value).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("11. Admin successfull vote")
        admin_valid_vote = sp.record(votes=sp.nat(30), address=admin.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(admin_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=(start_block + 50))

        scenario.p("12. Bob successfull vote")
        bob_valid_vote = sp.record(votes=sp.nat(112), address=bob.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        end_block = start_block + c1.data.governance_parameters.vote_length_blocks
        c1.vote(bob_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block)

        scenario.p("13. Bob can only vote one time")
        c1.vote(bob_valid_vote).run().run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("14. John cannot vote anymore. It is too late.")
        john_valid_vote = sp.record(votes=sp.nat(30), address=john.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(john_valid_vote).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block + 1)
        c1.vote(john_valid_vote).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block + 30)

        scenario.p("15. Check votes are counted as expected")
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify_equal(c1.data.poll_descriptor.open_some().vote_nay, 130)
        scenario.verify_equal(c1.data.poll_descriptor.open_some().vote_yay, 46)
        scenario.verify_equal(c1.data.poll_descriptor.open_some().vote_abstain, 362)
        scenario.verify_equal(c1.data.poll_descriptor.open_some().total_votes, 538)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().voters) == 6)

# Description: Test the end function.
def unit_test_end_valid_call(is_default = True):
    @sp.add_test(name="unit_test_end_valid_call", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_valid_call")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function valid calls.")

        level_offset = 100

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin, level=level_offset)

        scenario.p("2. No poll open. Cannot close")
        c1.end(0).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("2. Poll is started but start block is not reached. Cannot close")
        c1.end(0).run(valid=False, sender=simulated_poll_leader_contract.address, level=sp.level + 30)

        scenario.p("3. Poll is started but end block is not reached. Cannot close")
        c1.end(0).run(valid=False, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks + 150)

        scenario.p("3. Only poll leader can close the vote")
        total_vote_time_level = c1.data.governance_parameters.vote_delay_blocks + c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=False, sender=admin.address, level=sp.level + total_vote_time_level)
        c1.end(0).run(valid=False, sender=bob.address, level=sp.level + total_vote_time_level)
        c1.end(0).run(valid=False, sender=john.address, level=sp.level + total_vote_time_level)
        c1.end(0).run(valid=False, sender=alice.address, level=sp.level + total_vote_time_level)

        scenario.p("5. vote_id shall be valid")
        c1.end(1).run(valid=False, sender=simulated_poll_leader_contract.address, level=sp.level + total_vote_time_level)

        scenario.p("4. End the vote")
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + total_vote_time_level)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("5. Check vote_id is incremented for the next vote")
        scenario.verify(c1.data.vote_id == 1)
        scenario.verify(c1.data.vote_state == NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())
        c1.start(1000).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.data.vote_state == IN_PROGRESS)
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 1)

def unit_test_end_passed_but_quorum_not_reached_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_passed_but_quorum_not_reached_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_passed_but_quorum_not_reached_with_fixed_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the end function by simulating a failed poll (quorum not reached) with fixed quorum.")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(1000).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(238), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(1), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(10), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. End the vote")
        scenario.verify(~c1.data.outcomes.contains(0))
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 238)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 1)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 249)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 250)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

def unit_test_end_passed_1_with_quorum_reached_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_passed_1_with_quorum_reached_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_passed_1_with_quorum_reached_with_fixed_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the end function by simulating a successfull poll with fixed quorum (1).")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(1000).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(239), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(1), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(10), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. End the vote")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 239)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 1)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 250)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 250)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

def unit_test_end_passed_2_with_quorum_reached_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_passed_2_with_quorum_reached_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_passed_2_with_quorum_reached_with_fixed_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the end function by simulating a successfull poll with fixed quorum (2).")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(85), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(15), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(0), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. End the vote")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 85)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 15)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 100)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 25)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

def unit_test_end_passed_3_with_quorum_reached_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_passed_3_with_quorum_reached_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_passed_3_with_quorum_reached_with_fixed_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the end function by simulating a successfull poll with fixed quorum (3).")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(5992).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(3648), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(644), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(1556), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. End the vote")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 3648)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 644)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 1556)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 5848)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 1498)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

def unit_test_end_not_passed_1_with_quorum_reached_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_not_passed_1_with_quorum_reached_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_not_passed_1_with_quorum_reached_with_fixed_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the end function by simulating a failed poll with fixed quorum (1).")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(1000).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(1), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(239), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(10), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. End the vote")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 1)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 239)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 250)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 250)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

def unit_test_end_not_passed_2_with_quorum_reached_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_not_passed_2_with_quorum_reached_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_not_passed_2_with_quorum_reached_with_fixed_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the end function by simulating a failed poll with fixed quorum (2).")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(84), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(16), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(0), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. End the vote")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 84)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 16)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 100)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 25)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

def unit_test_end_not_passed_3_with_quorum_reached_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_not_passed_3_with_quorum_reached_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_not_passed_3_with_quorum_reached_with_fixed_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the end function by simulating a failed poll with fixed quorum (3).")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(5992).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(3647), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(645), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(1556), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. End the vote")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("5. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 3647)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 645)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 1556)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 5848)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 1498)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

def unit_test_end_dynamic_quorum(is_default = True):
    @sp.add_test(name="unit_test_end_dynamic_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_dynamic_quorum")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the end function with dynamic quorum.")

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Check dynamic quorum value")
        scenario.verify(c1.data.current_dynamic_quorum_value == sp.nat(2000))

        scenario.p("3. Start poll")
        c1.start(10000).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(3000), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(400), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(1000), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("5. End the vote")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("6. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("7. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 3000)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 400)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 1000)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 4400)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 2000)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)

        scenario.p("8. Check new dynamic quorum is computed")
        new_quorum = ((2000 * 80) // SCALE) + ((c1.data.outcomes[0].poll_data.total_votes * 20) // SCALE)
        scenario.verify(c1.data.current_dynamic_quorum_value == new_quorum)

        scenario.p("9. Start another poll")
        c1.start(10000).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("10. Add votes")
        chris_vote_param_valid_yay_2 = sp.record(votes=sp.nat(2000), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(1))
        gabe_vote_param_valid_nay_2 = sp.record(votes=sp.nat(2500), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(1))
        ben_vote_param_valid_abstain_2 = sp.record(votes=sp.nat(500), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(1))
        c1.vote(chris_vote_param_valid_yay_2).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay_2).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain_2).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("11. End the vote again")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)

        scenario.p("12. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 2)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 2)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("13. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 3000)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 400)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 1000)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 4400)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 2000)
        scenario.verify(sp.len(c1.data.outcomes[0].poll_data.voters) == 3)
        scenario.verify(c1.data.outcomes.contains(1))
        scenario.verify(c1.data.outcomes[1].poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[1].poll_data.vote_yay == 2000)
        scenario.verify(c1.data.outcomes[1].poll_data.vote_nay == 2500)
        scenario.verify(c1.data.outcomes[1].poll_data.vote_abstain == 500)
        scenario.verify(c1.data.outcomes[1].poll_data.total_votes == 5000)
        scenario.verify(c1.data.outcomes[1].poll_data.voting_start_block == 201)
        scenario.verify(c1.data.outcomes[1].poll_data.voting_end_block == 381)
        scenario.verify(c1.data.outcomes[1].poll_data.vote_id == 1)
        scenario.verify(c1.data.outcomes[1].poll_data.quorum == new_quorum)
        scenario.verify(sp.len(c1.data.outcomes[1].poll_data.voters) == 3)

        scenario.p("14. Check new dynamic quorum is computed")
        new_quorum = ((new_quorum * 80) // SCALE) + ((c1.data.outcomes[1].poll_data.total_votes * 20) // SCALE)
        scenario.verify(c1.data.current_dynamic_quorum_value == new_quorum)

def unit_test_offchain_views(is_default = True):
    @sp.add_test(name="unit_test_offchain_views", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_offchain_views")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test all the offchain views.")

        scenario.p("1. Register poll_leader contract")
        scenario.verify(c1.get_contract_state() == NONE)
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(10000).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == IN_PROGRESS)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(3000), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(400), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(1000), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Get and check poll data")
        poll_data_0 = c1.get_current_poll_data()
        scenario.verify(poll_data_0.vote_yay == 3000)
        scenario.verify(poll_data_0.vote_nay == 400)
        scenario.verify(poll_data_0.vote_abstain == 1000)
        scenario.verify(poll_data_0.total_votes == 4400)
        scenario.verify(poll_data_0.voting_start_block == 10)
        scenario.verify(poll_data_0.voting_end_block == 190)
        scenario.verify(poll_data_0.vote_id == 0)
        scenario.verify(poll_data_0.quorum == 2000)
        scenario.verify(sp.len(poll_data_0.voters) == 3)

        scenario.p("5. End the vote")
        scenario.verify(c1.get_contract_state() == IN_PROGRESS)
        scenario.verify(c1.get_number_of_historical_outcomes() == 0)
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)
        scenario.verify(c1.get_contract_state() == NONE)

        scenario.p("6. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 1)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.poll_outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(outcome_0.poll_data.vote_yay == 3000)
        scenario.verify(outcome_0.poll_data.vote_nay == 400)
        scenario.verify(outcome_0.poll_data.vote_abstain == 1000)
        scenario.verify(outcome_0.poll_data.total_votes == 4400)
        scenario.verify(outcome_0.poll_data.voting_start_block == 10)
        scenario.verify(outcome_0.poll_data.voting_end_block == 190)
        scenario.verify(outcome_0.poll_data.vote_id == 0)
        scenario.verify(outcome_0.poll_data.quorum == 2000)
        scenario.verify(sp.len(outcome_0.poll_data.voters) == 3)
        scenario.verify(c1.get_contract_state() == NONE)

        scenario.p("7. Start another poll")
        c1.start(10000).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == IN_PROGRESS)

        scenario.p("8. Add votes")
        chris_vote_param_valid_yay_2 = sp.record(votes=sp.nat(2000), address=chris.address, vote_value=VoteValue.YAY, vote_id=sp.nat(1))
        gabe_vote_param_valid_nay_2 = sp.record(votes=sp.nat(2500), address=gabe.address, vote_value=VoteValue.NAY, vote_id=sp.nat(1))
        ben_vote_param_valid_abstain_2 = sp.record(votes=sp.nat(500), address=ben.address, vote_value=VoteValue.ABSTAIN, vote_id=sp.nat(1))
        c1.vote(chris_vote_param_valid_yay_2).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay_2).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain_2).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == IN_PROGRESS)

        scenario.p("9. End the vote again")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)
        scenario.verify(c1.get_contract_state() == NONE)

        scenario.p("10. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 2)
        outcome_1 = c1.get_historical_outcome_data(1)
        scenario.verify(outcome_1.poll_outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(outcome_1.poll_data.vote_yay == 2000)
        scenario.verify(outcome_1.poll_data.vote_nay == 2500)
        scenario.verify(outcome_1.poll_data.vote_abstain == 500)
        scenario.verify(outcome_1.poll_data.total_votes == 5000)
        scenario.verify(outcome_1.poll_data.voting_start_block == 201)
        scenario.verify(outcome_1.poll_data.voting_end_block == 381)
        scenario.verify(outcome_1.poll_data.vote_id == 1)

def unit_test_mutez_transfer(is_default=True):
    @sp.add_test(name="unit_test_mutez_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mutez_transfer")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, john)

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


unit_test_initial_storage()
unit_test_set_administrator()
unit_test_set_poll_leader()
unit_test_start_with_dynamic_quorum()
unit_test_start_with_fixed_quorum()
unit_test_vote()
unit_test_end_valid_call()
unit_test_end_passed_but_quorum_not_reached_with_fixed_quorum()
unit_test_end_passed_1_with_quorum_reached_with_fixed_quorum()
unit_test_end_passed_2_with_quorum_reached_with_fixed_quorum()
unit_test_end_passed_3_with_quorum_reached_with_fixed_quorum()
unit_test_end_not_passed_1_with_quorum_reached_with_fixed_quorum()
unit_test_end_not_passed_2_with_quorum_reached_with_fixed_quorum()
unit_test_end_not_passed_3_with_quorum_reached_with_fixed_quorum()
unit_test_end_dynamic_quorum()
unit_test_offchain_views()
unit_test_mutez_transfer()