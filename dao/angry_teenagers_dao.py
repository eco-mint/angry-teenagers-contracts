import smartpy as sp

Error = sp.io.import_script_from_url("file:angry_teenagers_errors.py")
Proposal = sp.io.import_script_from_url("file:dao/helper/angry_teenagers_dao_proposal.py")
VoteValue = sp.io.import_script_from_url("file:dao/helper/angry_teenagers_dao_vote_value.py")
PollOutcome = sp.io.import_script_from_url("file:dao/helper/angry_teenagers_dao_poll_outcome.py")
PollType = sp.io.import_script_from_url("file:dao/helper/angry_teenagers_dao_poll_type.py")

################################################################
################################################################
# Local types: type onoly used by this contract
################################################################
################################################################

PROPOSE_CALLBACK_TYPE = sp.TRecord(id=sp.TNat, snapshot_block=sp.TNat)
POLL_MANAGER_TYPE = sp.TMap(sp.TNat, sp.TRecord(name=sp.TString, address=sp.TAddress))
OUTCOMES_TYPE = sp.TBigMap(sp.TNat, PollOutcome.HISTORICAL_OUTCOME_TYPE)

################################################################
################################################################
# Constants
################################################################
################################################################

# Voting strategy called "majority". Works with a configurable quorum
# and a supermajority thresold.
VOTE_TYPE_MAJORITY=0
# Voting strategy called "opt out". Mainly used to unblock ATs funds.
VOTE_TYPE_OPT_OUT=1

################################################################
################################################################
# State Machine
################################################################
################################################################

# NONE: No vote in progress.
NONE=0
# STARTING_VOTE: The contract requested to start to the appropriate
# voting strategy and wait for the answer.
STARTING_VOTE=1
# VOTE_ONGOING: Vote is started.
VOTE_ONGOING=2
# ENDING_VOTE: The contract requested to end the vote to the appropriate
# voting strategy and wait for the answer.
ENDING_VOTE=3

################################################################
################################################################
# Class
################################################################
################################################################
class AngryTeenagersDao(sp.Contract):
    def __init__(self,
                 admin,
                 metadata,
                 poll_manager,
                 outcomes=sp.big_map(l={}, tkey=sp.TNat, tvalue=PollOutcome.HISTORICAL_OUTCOME_TYPE)):
      self.init_type(
          sp.TRecord(
              state = sp.TNat,
              ongoing_poll = sp.TOption(PollType.POLL_TYPE),
              angry_teenager_fa2 = sp.TOption(sp.TAddress),
              poll_manager = POLL_MANAGER_TYPE,
              next_proposal_id = sp.TNat,
              admin = sp.TAddress,
              outcomes = OUTCOMES_TYPE,
              metadata= sp.TBigMap(sp.TString, sp.TBytes)
          )
      )

      self.init(
          state = sp.nat(NONE),
          ongoing_poll = sp.none,
          angry_teenager_fa2 = sp.none,
          poll_manager = poll_manager,
          next_proposal_id = sp.nat(0),
          admin = admin,
          outcomes = outcomes,
          metadata = metadata
      )

      list_of_views = [
          self.get_number_of_historical_outcomes
          , self.get_historical_outcome_data
          , self.is_poll_in_progress
          , self.get_current_poll_data
          , self.get_contract_state
      ]

      metadata_base = {
          "version": "1.0"
          , "description": (
              "Angry Teenagers DAO."
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
        sp.verify(sp.sender == self.data.admin, message = Error.ErrorMessage.unauthorized_user())
        self.data.metadata[k] = v

########################################################################################################################
# set_metadata
########################################################################################################################
    @sp.entry_point
    def set_administrator(self, params):
        sp.verify(sp.sender == self.data.admin, message = Error.ErrorMessage.unauthorized_user())
        self.data.admin = params

########################################################################################################################
# add_voting_strategy
########################################################################################################################
    @sp.entry_point
    def add_voting_strategy(self, params):
        sp.verify(self.data.state == NONE, Error.ErrorMessage.dao_vote_in_progress())
        sp.verify((sp.self_address == sp.sender) | (self.data.admin == sp.sender), Error.ErrorMessage.unauthorized_user())
        sp.set_type(params, sp.TRecord(id=sp.TNat, name=sp.TString, address=sp.TAddress))
        sp.verify(~self.data.poll_manager.contains(params.id), Error.ErrorMessage.dao_already_registered())
        self.data.poll_manager[params.id] = sp.record(name=params.name, address=params.address)

########################################################################################################################
# register_angry_teenager_fa2
########################################################################################################################
    @sp.entry_point
    def register_angry_teenager_fa2(self, address):
        sp.verify(self.data.admin == sp.sender, Error.ErrorMessage.unauthorized_user())
        sp.verify(~self.data.angry_teenager_fa2.is_some(), Error.ErrorMessage.dao_already_registered())
        self.data.angry_teenager_fa2 = sp.some(address)

########################################################################################################################
# propose: Inject a new proposal
########################################################################################################################
    @sp.entry_point
    def propose(self, proposal):
        # Check the type
        sp.set_type(proposal, Proposal.PROPOSAL_TYPE)

        # Asserts
        sp.verify(sp.sender == self.data.admin, Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.state == NONE, Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(self.data.angry_teenager_fa2.is_some(), Error.ErrorMessage.dao_not_registered())
        sp.verify(~self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(self.data.poll_manager.contains(proposal.voting_strategy), Error.ErrorMessage.dao_invalid_voting_strat())

        # Create the poll with the proposal
        self.data.ongoing_poll = sp.some(
            sp.record(
                proposal=proposal,
                proposal_id=self.data.next_proposal_id,
                author=sp.sender,
                voting_strategy_address=self.data.poll_manager[proposal.voting_strategy].address,
                voting_id=sp.nat(0),
                snapshot_block=sp.nat(0)
            )
        )

        # Get the total voting power in the ATs collection at the moment
        total_available_voters = sp.view("get_total_voting_power",
                               self.data.angry_teenager_fa2.open_some(Error.ErrorMessage.dao_not_registered()),
                               sp.unit,
                               t=sp.TNat).open_some(Error.ErrorMessage.dao_invalid_token_view())
        sp.verify(total_available_voters > 0, Error.ErrorMessage.dao_no_voting_power())

        # Change the state of the contract accordingly
        self.data.state = STARTING_VOTE

        # Call voting strategy to start the poll
        self.call_voting_strategy_start(total_available_voters)

########################################################################################################################
# propose_callback
########################################################################################################################
    @sp.entry_point
    def propose_callback(self, params):
        # Check the type
        sp.set_type(params, PROPOSE_CALLBACK_TYPE)

        # Asserts
        sp.verify(self.data.state == STARTING_VOTE, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.open_some().voting_strategy_address == sp.sender, Error.ErrorMessage.dao_invalid_voting_strat())

        # Update the poll data
        self.data.ongoing_poll = sp.some(
            sp.record(
                proposal=self.data.ongoing_poll.open_some().proposal,
                proposal_id=self.data.ongoing_poll.open_some().proposal_id,
                author=self.data.ongoing_poll.open_some().author,
                voting_strategy_address=self.data.ongoing_poll.open_some().voting_strategy_address,
                voting_id=params.id,
                snapshot_block=params.snapshot_block
            )
        )

        # Change the state of the contract accordingly
        self.data.state = VOTE_ONGOING

########################################################################################################################
# vote: Send
########################################################################################################################
    @sp.entry_point
    def vote(self, params):
        # Check type
        sp.set_type(params, VoteValue.VOTE_VALUE)

        # Asserts
        sp.verify(self.data.state == VOTE_ONGOING, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(params.proposal_id == self.data.ongoing_poll.open_some().proposal_id, Error.ErrorMessage.dao_no_invalid_proposal())

        # Find the user voting power before sending the votes
        voting_power = sp.view("get_voting_power",
                               self.data.angry_teenager_fa2.open_some(Error.ErrorMessage.dao_not_registered()),
                               sp.pair(sp.sender, self.data.ongoing_poll.open_some().snapshot_block),
                               t=sp.TNat).open_some(Error.ErrorMessage.dao_invalid_token_view())
        sp.verify(voting_power > 0, Error.ErrorMessage.dao_no_voting_power())

        # Call the appropriate voting strategy
        self.call_voting_strategy_vote(voting_power, sp.sender, params.vote_value)

########################################################################################################################
# end
########################################################################################################################
    @sp.entry_point
    def end(self, proposal_id):
        # Check type
        sp.set_type(proposal_id, sp.TNat)

        # Asserts
        # Everybody can call this function to avoid a vote been blocked by the admin or anybody else
        sp.verify(self.data.state == VOTE_ONGOING, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.open_some().proposal_id == proposal_id, Error.ErrorMessage.dao_no_invalid_proposal())

        # Change the state of contract
        self.data.state = ENDING_VOTE

        # Call the appropriate voting strategy
        self.call_voting_strategy_end()

########################################################################################################################
# end_callback
########################################################################################################################
    @sp.entry_point
    def end_callback(self, params):
        # Check type
        sp.set_type(params, sp.TRecord(voting_id=sp.TNat, voting_outcome=sp.TNat))

        # Asserts
        sp.verify(self.data.state == ENDING_VOTE, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.open_some().voting_strategy_address == sp.sender, Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(~self.data.outcomes.contains(self.data.next_proposal_id), Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(params.voting_id == self.data.ongoing_poll.open_some().voting_id, Error.ErrorMessage.dao_invalid_voting_strat())

        # Execute the lambda if the vote is passed and the lambda exists
        sp.if (params.voting_outcome == PollOutcome.POLL_OUTCOME_PASSED) & (self.data.ongoing_poll.open_some().proposal.proposal_lambda.is_some()):
            operations = self.data.ongoing_poll.open_some().proposal.proposal_lambda.open_some()(sp.unit)
            sp.set_type(operations, sp.TList(sp.TOperation))
            sp.add_operations(operations)

        # Change the state of contract
        self.data.state = NONE

        # Record the result of the vote
        self.data.outcomes[self.data.next_proposal_id] = sp.record(outcome = params.voting_outcome, poll_data = self.data.ongoing_poll.open_some())

        # Close the vote
        self.data.ongoing_poll = sp.none
        self.data.next_proposal_id = self.data.next_proposal_id + 1

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

    def call_voting_strategy_start(self, total_available_voters):
        voteContractHandle = sp.contract(
            sp.TRecord (total_available_voters=sp.TNat),
            self.data.ongoing_poll.open_some().voting_strategy_address,
            "start"
        ).open_some("Interface mismatch")

        voteContractArg = sp.record(total_available_voters=total_available_voters)
        self.call(voteContractHandle, voteContractArg)

    def call_voting_strategy_vote(self, votes, address, vote_value):
        voteContractHandle = sp.contract(
            sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, voting_id=sp.TNat),
            self.data.ongoing_poll.open_some().voting_strategy_address,
            "vote"
        ).open_some("Interface mismatch")

        voteContractArg = sp.record(
                votes=votes, address=address, vote_value=vote_value, voting_id=self.data.ongoing_poll.open_some().voting_id
            )
        self.call(voteContractHandle, voteContractArg)

    def call_voting_strategy_end(self):
        voteContractHandle = sp.contract(
            sp.TNat,
            self.data.ongoing_poll.open_some().voting_strategy_address,
            "end"
        ).open_some("Interface mismatch")

        voteContractArg = self.data.ongoing_poll.open_some().voting_id
        self.call(voteContractHandle, voteContractArg)

########################################################################################################################
########################################################################################################################
# Offchain views
########################################################################################################################
########################################################################################################################
    @sp.offchain_view(pure=True)
    def get_number_of_historical_outcomes(self):
        """Get how many historical outcomes are stored in the DAO.
        """
        sp.result(self.data.next_proposal_id)

    @sp.offchain_view(pure=True)
    def get_historical_outcome_data(self, id):
        """Get all historical outcomes ids.
        """
        sp.verify(self.data.outcomes.contains(id), Error.ErrorMessage.dao_invalid_outcome_id())
        sp.result(self.data.outcomes[id])

    @sp.offchain_view(pure=True)
    def is_poll_in_progress(self):
        """Is there a poll ins progress ?
        """
        sp.result(self.data.ongoing_poll.is_some())

    @sp.offchain_view(pure=True)
    def get_current_poll_data(self):
        """Get all current poll data if it exists.
        """
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.result(self.data.ongoing_poll.open_some())

    @sp.offchain_view(pure=True)
    def get_contract_state(self):
        """Get contract state
        """
        sp.result(self.data.state)


########################################################################################################################
########################################################################################################################
# Compilation target
########################################################################################################################
########################################################################################################################
sp.add_compilation_target("AngryTeenagers DAO",
                          # TODO: Real addresses shall be used
                            AngryTeenagersDao(
                                admin=sp.address("tz1QqobMeCYY1WjeaPUcphhyq2Q5C3BfTE2q"),
                                # TODO: Inject the right metadata
                                # TODO: The opt out contract is not added. the majority one is not valid
                                metadata=sp.utils.metadata_of_url("ipfs://Qmbz6g7HQGUFqpGVEfYVi59gmZn8ETzfWYqbhZDhfk9mca"),
                                poll_manager=sp.map(l = { VOTE_TYPE_MAJORITY : sp.record(name=sp.string("MajorityVote"), address=sp.address("KT1Vk3GjhwHP732NcVBRT6yNmoAxy2Jyh81G")),
                                                          VOTE_TYPE_OPT_OUT: sp.record(name=sp.string("OptOutVote"), address=sp.address("KT1CBeoEjK9gHmifS7W71HoNddoLD9hv1HxE"))}, tkey=sp.TNat, tvalue=sp.TRecord(name=sp.TString, address=sp.TAddress))))

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
        simulated_voting_strategy_one = SimulatedVotingStrategy(scenario)
        simulated_voting_strategy_two = SimulatedVotingStrategy(scenario)
        simulated_fa2 = SimulatedFA2(scenario)
        scenario += simulated_voting_strategy_one
        scenario += simulated_voting_strategy_two
        c1 = AngryTeenagersDao(admin=admin.address,
                              metadata=sp.utils.metadata_of_url("https://example.com"),
                              poll_manager=sp.map(l = {0 : sp.record(name="One", address=simulated_voting_strategy_one.address), 1: sp.record(name="Two", address=simulated_voting_strategy_two.address)}))

        scenario += c1
        scenario += simulated_fa2

        scenario.h2("Contracts:")
        scenario.p("c1: This contract to test (AngryTeenagersDao)")

        return c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2

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

class SimulatedFA2(sp.Contract):
    def __init__(self, scenario):
        self.init_type(
            sp.TRecord(
                total_voting_power=sp.TNat,
                get_voting_power_called_with_address=sp.TOption(sp.TAddress),
                get_voting_power_snapshot_block=sp.TNat,
                address_voting_power=sp.TNat
            )
        )

        self.init(
            total_voting_power=sp.nat(1000),
            get_voting_power_called_with_address=sp.none,
            get_voting_power_snapshot_block=sp.nat(1000),
            address_voting_power=sp.nat(100)
        )
        self.scenario = scenario

    @sp.onchain_view()
    def get_total_voting_power(self):
        """Get how many tokens was in this FA2 contract onchain.
        """
        sp.result(self.data.total_voting_power)

    @sp.entry_point()
    def change_voting_power(self, params):
        sp.set_type(params, sp.TNat)
        self.data.address_voting_power = params

    @sp.onchain_view()
    def get_voting_power(self, params):
        sp.set_type(params, sp.TPair(sp.TAddress, sp.TNat))
        self.data.get_voting_power_called_with_address = sp.some(sp.fst(params))
        self.data.get_voting_power_snapshot_block = sp.snd(params)
        sp.result(self.data.address_voting_power)

class SimulatedVotingStrategy(sp.Contract):
    def __init__(self, scenario):
        self.init_type(
            sp.TRecord(
                start_called_times = sp.TNat,
                end_called_times = sp.TNat,
                end_vote_id = sp.TNat,
                vote_called_times = sp.TNat,
                total_available_voters = sp.TNat,
                vote_last_address = sp.TOption(sp.TAddress),
                vote_last_value = sp.TNat,
                vote_last_id = sp.TNat,
                vote_numbers = sp.TNat
            )
        )

        self.init(
            start_called_times = sp.nat(0),
            end_called_times = sp.nat(0),
            end_vote_id=sp.nat(100),
            vote_called_times = sp.nat(0),
            total_available_voters = sp.nat(0),
            vote_last_address = sp.none,
            vote_last_value = sp.nat(1000),
            vote_last_id = sp.nat(1000),
            vote_numbers = sp.nat(0)
        )
        self.scenario = scenario

    @sp.entry_point()
    def start(self, params):
        sp.set_type(params, sp.TRecord(total_available_voters=sp.TNat))
        self.data.start_called_times = self.data.start_called_times + 1
        self.data.total_available_voters = params.total_available_voters

    @sp.entry_point()
    def end(self, params):
        sp.set_type(params, sp.TNat)
        self.data.end_called_times = self.data.end_called_times + 1
        self.data.end_vote_id = params

    @sp.entry_point
    def vote(self, params):
        sp.set_type(params, sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, voting_id=sp.TNat))
        self.data.vote_called_times = self.data.vote_called_times + 1
        self.data.vote_last_address = sp.some(params.address)
        self.data.vote_last_value = params.vote_value
        self.data.vote_last_id = params.voting_id
        self.data.vote_numbers = params.votes


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
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the storage is initialized as expected.")

        scenario.p("1. Read each entry of the storage of the c1 contract and check it is initialized as expected")
        scenario.verify(c1.data.admin == admin.address)
        scenario.verify(c1.data.state == NONE)
        scenario.verify(c1.data.next_proposal_id == sp.nat(0))
        scenario.verify(~c1.data.angry_teenager_fa2.is_some())
        scenario.verify(~c1.data.ongoing_poll.is_some())
        scenario.verify(sp.len(c1.data.poll_manager) == 2)
        scenario.verify(c1.data.poll_manager[0] == sp.record(name="One", address=simulated_voting_strategy_one.address))
        scenario.verify(c1.data.poll_manager[1] == sp.record(name="Two", address=simulated_voting_strategy_two.address))
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

def unit_test_set_administrator(is_default = True):
    @sp.add_test(name="unit_test_set_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

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

def unit_test_register_angry_teenager_fa2(is_default = True):
    @sp.add_test(name="unit_test_register_angry_teenager_fa2", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_register_angry_teenager_fa2")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the register_angry_teenager_fa2 entrypoint.")

        scenario.p("1. Only admin can set the entrypoint")
        scenario.verify(~c1.data.angry_teenager_fa2.is_some())
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=False, sender=bob)
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=False, sender=alice)
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=False, sender=john)
        scenario.verify(~c1.data.angry_teenager_fa2.is_some())
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)
        scenario.verify(c1.data.angry_teenager_fa2.open_some() == simulated_fa2.address)

        scenario.p("2. Address can be set only one time")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=False, sender=admin)

def unit_test_mutez_transfer(is_default=True):
    @sp.add_test(name="unit_test_mutez_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mutez_transfer")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the mutez_transfer entrypoint.  (Who: Only for the admin)")
        scenario.p("This entrypoint is called byt the admin to extract fund on the contract. Normally no funds are supposed to be held in the contract however if something bad happens or somebody makes a mistake transfer, we still want to have the ability to extract the fund.")

        scenario.p("1. Add fund to the contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin, amount=sp.mutez(300000000))

        scenario.p("2. Check that only the admin can call this entrypoint")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=alice)
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=bob)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(200000000))).run(valid=False, sender=john)

        scenario.p("3. Check the function extracts the fund as expected")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=True, sender=admin)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(100000000))).run(valid=True, sender=admin)

        scenario.p("3. Check no fund are remaining")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(100000000))).run(valid=False, sender=admin)

def unit_test_add_voting_strategy(is_default = True):
    @sp.add_test(name="unit_test_add_voting_strategy", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_add_voting_strategy")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the add_voting_strategy entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. Only the DAO or the admin can add a voting strategy")
        voting_strategy_1_john_invalid = sp.record(id=sp.nat(2), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        voting_strategy_1_bob_invalid = sp.record(id=sp.nat(2), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        voting_strategy_1_dao_valid = sp.record(id=sp.nat(2), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        voting_strategy_1_admin_valid = sp.record(id=sp.nat(10), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)

        c1.add_voting_strategy(voting_strategy_1_john_invalid).run(valid=False, sender=john)
        c1.add_voting_strategy(voting_strategy_1_bob_invalid).run(valid=False, sender=bob)
        c1.add_voting_strategy(voting_strategy_1_dao_valid).run(valid=True, sender=c1.address)
        c1.add_voting_strategy(voting_strategy_1_admin_valid).run(valid=True, sender=c1.address)

        scenario.p("3. Existing voting strategies cannot be replaced")
        voting_strategy_0_dao_invalid = sp.record(id=sp.nat(0), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        voting_strategy_1_dao_invalid = sp.record(id=sp.nat(1), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        voting_strategy_2_dao_invalid = sp.record(id=sp.nat(2), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        voting_strategy_3_dao_valid = sp.record(id=sp.nat(3), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        c1.add_voting_strategy(voting_strategy_0_dao_invalid).run(valid=False, sender=c1.address)
        c1.add_voting_strategy(voting_strategy_1_dao_invalid).run(valid=False, sender=c1.address)
        c1.add_voting_strategy(voting_strategy_2_dao_invalid).run(valid=False, sender=c1.address)
        c1.add_voting_strategy(voting_strategy_3_dao_valid).run(valid=True, sender=c1.address)

        scenario.p("4. Voting strategies can only be added in state NONE")
        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)
        voting_strategy_4_dao_valid = sp.record(id=sp.nat(4), name=sp.string('voting_strategy_1'), address=simulated_voting_strategy_one.address)
        c1.add_voting_strategy(voting_strategy_4_dao_valid).run(valid=False, sender=c1.address)


def unit_test_propose(is_default = True):
    @sp.add_test(name="unit_test_propose", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_propose")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the propose entrypoint.")

        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )

        proposal_2_invalid = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=2
                               )

        scenario.p("1. A FA2 contract must be registered")
        c1.propose(proposal_1).run(valid=False, sender=admin.address)

        scenario.p("2. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("3. Only admin can inject a proposal")
        c1.propose(proposal_1).run(valid=False, sender=alice.address)

        scenario.p("4. Voting strategy must exist")
        c1.propose(proposal_2_invalid).run(valid=False, sender=admin.address)

        scenario.p("5. Check storage is still as expected")
        scenario.verify(c1.data.state == NONE)
        scenario.verify(~c1.data.ongoing_poll.is_some())

        scenario.p("6. Inject a valid proposal")
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("6. Check storage is as expected")
        scenario.verify(c1.data.state == STARTING_VOTE)
        scenario.verify(c1.data.ongoing_poll.is_some())
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.title == "Test1")
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.description_link == "link1")
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.description_hash == "hash1")
        scenario.verify(~c1.data.ongoing_poll.open_some().proposal.proposal_lambda.is_some())
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.voting_strategy == 0)
        scenario.verify(c1.data.ongoing_poll.open_some().proposal_id == 0)
        scenario.verify(c1.data.ongoing_poll.open_some().author == admin.address)
        scenario.verify(c1.data.poll_manager[0].address == simulated_voting_strategy_one.address)
        scenario.verify(c1.data.ongoing_poll.open_some().voting_id == sp.nat(0))
        scenario.verify(c1.data.ongoing_poll.open_some().snapshot_block == sp.nat(0))

        scenario.p("7. Check callbacks are called as expected")
        scenario.verify(simulated_voting_strategy_one.data.start_called_times == 1)
        scenario.verify(simulated_voting_strategy_one.data.total_available_voters == simulated_fa2.data.total_voting_power)
        scenario.verify(simulated_voting_strategy_two.data.start_called_times == 0)
        scenario.verify(simulated_voting_strategy_two.data.total_available_voters == 0)

        scenario.p("6. A proposal cannot be injected while another is in progress")
        c1.propose(proposal_1).run(valid=False, sender=admin.address)

    @sp.entry_point
    def propose_callback(self, params):
        sp.set_type(params, PROPOSE_CALLBACK_TYPE)
        sp.verify(self.data.state == STARTING_VOTE, Errors.ERROR_NO_POLL_OPEN)
        sp.verify(self.data.ongoing_poll.is_some(), Errors.ERROR_NO_POLL_OPEN)
        sp.verify(self.data.ongoing_poll.open_some().voting_strategy_address == sp.sender, Errors.ERROR_INVALID_VOTING_STRATEGY)
        self.data.ongoing_poll = sp.some(
            sp.record(
                proposal=self.data.ongoing_poll.open_some().proposal,
                proposal_id=self.data.ongoing_poll.open_some().proposal_id,
                author=self.data.ongoing_poll.open_some().author,
                voting_strategy_address=self.data.ongoing_poll.open_some().voting_strategy_address,
                voting_id=params.id,
                snapshot_block=params.snapshot_block
            )
        )
        self.data.state = VOTE_ONGOING

def unit_test_propose_callback(is_default = True):
    @sp.add_test(name="unit_test_propose_callback", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_propose_callback")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        voting_id = 3
        snapshot_block = 1213
        propose_callback_params_valid = sp.record(id=3, snapshot_block=1213)

        scenario.h2("Test the propose_callback entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. Contract shall be in the right state")
        c1.propose_callback(propose_callback_params_valid).run(valid=False, sender=simulated_voting_strategy_one.address)

        scenario.p("3. Inject a valid proposal")
        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("4. Only the chosen voting strategy can call the propose_callback")
        c1.propose_callback(propose_callback_params_valid).run(valid=False, sender=simulated_voting_strategy_two.address)

        scenario.p("4. Now the propose_callback can be called")
        c1.propose_callback(propose_callback_params_valid).run(valid=True, sender=simulated_voting_strategy_one.address)

        scenario.p("5. Check the storage of the contract is as expected")
        scenario.verify(c1.data.state == VOTE_ONGOING)
        scenario.verify(c1.data.ongoing_poll.is_some())
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.title == "Test1")
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.description_link == "link1")
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.description_hash == "hash1")
        scenario.verify(~c1.data.ongoing_poll.open_some().proposal.proposal_lambda.is_some())
        scenario.verify(c1.data.ongoing_poll.open_some().proposal.voting_strategy == 0)
        scenario.verify(c1.data.ongoing_poll.open_some().proposal_id == 0)
        scenario.verify(c1.data.ongoing_poll.open_some().author == admin.address)
        scenario.verify(c1.data.poll_manager[0].address == simulated_voting_strategy_one.address)
        scenario.verify(c1.data.ongoing_poll.open_some().voting_id == voting_id)
        scenario.verify(c1.data.ongoing_poll.open_some().snapshot_block == snapshot_block)

def unit_test_vote(is_default = True):
    @sp.add_test(name="unit_test_vote", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_vote")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        voting_id = 3
        snapshot_block = 1213
        propose_callback_params_valid = sp.record(id=voting_id, snapshot_block=snapshot_block)
        proposal_id = 0
        vote_value = VoteValue.YAY
        vote_param = sp.record(proposal_id=proposal_id, vote_value=vote_value)

        scenario.h2("Test the vote entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. Vote can only be called when a vote is ongoing")
        c1.vote(vote_param).run(valid=False, sender=alice.address)

        scenario.p("3. Inject a valid proposal")
        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("4. Vote can only be called when a vote is ongoing")
        c1.vote(vote_param).run(valid=False, sender=alice.address)

        scenario.p("5. Call propose_callback can be called")
        c1.propose_callback(propose_callback_params_valid).run(valid=True, sender=simulated_voting_strategy_one.address)

        scenario.p("6. Let's send the vote now")
        simulated_fa2.change_voting_power(127)
        c1.vote(vote_param).run(valid=True, sender=alice.address)

        scenario.p("7. Check the callback has been called as expected")
        scenario.verify(simulated_voting_strategy_one.data.vote_called_times == 1)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_address.is_some())
        scenario.verify(simulated_voting_strategy_one.data.vote_last_address.open_some() == alice.address)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_value == VoteValue.YAY)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_id == 3)
        scenario.verify(simulated_voting_strategy_one.data.vote_numbers == 127)

        scenario.p("8. Cannot vote with 0 voting_power")
        simulated_fa2.change_voting_power(0)
        proposal_id = 0
        vote_value_2 = VoteValue.NAY
        vote_param_2 = sp.record(proposal_id=proposal_id, vote_value=vote_value_2)
        c1.vote(vote_param_2).run(valid=False, sender=bob.address)

        scenario.p("8. Vote with valid voting_power")
        simulated_fa2.change_voting_power(1)
        c1.vote(vote_param_2).run(valid=True, sender=bob.address)

        scenario.p("8. Check the callback has been called as expected")
        scenario.verify(simulated_voting_strategy_one.data.vote_called_times == 2)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_address.is_some())
        scenario.verify(simulated_voting_strategy_one.data.vote_last_address.open_some() == bob.address)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_value == VoteValue.NAY)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_id == 3)
        scenario.verify(simulated_voting_strategy_one.data.vote_numbers == 1)

def unit_test_end(is_default = True):
    @sp.add_test(name="unit_test_end", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        voting_id = 3
        snapshot_block = 1213
        propose_callback_params_valid = sp.record(id=voting_id, snapshot_block=snapshot_block)

        scenario.h2("Test the end entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. You can only end a vote when one is in progress")
        c1.end(0).run(valid=False, sender=alice.address)

        scenario.p("3. Inject a valid proposal")
        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("4. Vote can only be ended a when a vote is ongoing")
        c1.end(0).run(valid=False, sender=alice.address)

        scenario.p("5. Call propose_callback can be called")
        c1.propose_callback(propose_callback_params_valid).run(valid=True, sender=simulated_voting_strategy_one.address)

        scenario.p("6. Vote can only be ended using the right proposal_id")
        c1.end(1).run(valid=False, sender=alice.address)

        scenario.p("7. Let's close the vote now")
        scenario.verify(simulated_voting_strategy_one.data.end_called_times == 0)
        c1.end(0).run(valid=True, sender=alice.address)

        scenario.p("8. Check the storage of the contract is as expected")
        scenario.verify(c1.data.state == ENDING_VOTE)

        scenario.p("9. Check the callback has been called as expected")
        scenario.verify(simulated_voting_strategy_one.data.end_called_times == 1)
        scenario.verify(simulated_voting_strategy_one.data.end_vote_id == 3)

def unit_test_end_callback(is_default = True):
    @sp.add_test(name="unit_test_end_callback", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_end_callback")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        voting_id = 3
        snapshot_block = 1213
        propose_callback_params_valid = sp.record(id=voting_id, snapshot_block=snapshot_block)

        end_callback_valid = sp.record(voting_id=voting_id, voting_outcome=PollOutcome.POLL_OUTCOME_PASSED)
        end_callback_invalid = sp.record(voting_id=0, voting_outcome=PollOutcome.POLL_OUTCOME_PASSED)

        scenario.h2("Test the end_callback entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. end_callback can only be called when the contract is in the right state")
        c1.end_callback(end_callback_valid).run(valid=False, sender=simulated_voting_strategy_one.address)

        scenario.p("3. Inject a valid proposal")
        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("4. end_callback can only be called when the contract is in the right state")
        c1.end_callback(end_callback_valid).run(valid=False, sender=simulated_voting_strategy_one.address)

        scenario.p("5. Call propose_callback can be called")
        c1.propose_callback(propose_callback_params_valid).run(valid=True, sender=simulated_voting_strategy_one.address)

        scenario.p("6. end_callback can only be called when the contract is in the right state")
        c1.end_callback(end_callback_valid).run(valid=False, sender=simulated_voting_strategy_one.address)

        scenario.p("7. Let's close the vote now")
        scenario.verify(simulated_voting_strategy_one.data.end_called_times == 0)
        c1.end(0).run(valid=True, sender=alice.address)

        scenario.p("8. end_callback can only be called by the voting contract")
        c1.end_callback(end_callback_valid).run(valid=False, sender=alice.address)

        scenario.p("9. end_callback can only be called with the correct voting_id")
        c1.end_callback(end_callback_invalid).run(valid=False, sender=simulated_voting_strategy_one.address)

        scenario.p("10. Call successfully the  end_callback")
        scenario.verify(~c1.data.outcomes.contains(0))
        c1.end_callback(end_callback_valid).run(valid=True, sender=simulated_voting_strategy_one.address)

        scenario.p("11. Check the storage of the contract is as expected")
        scenario.verify(c1.data.state == NONE)
        scenario.verify(c1.data.next_proposal_id == 1)
        scenario.verify(~c1.data.ongoing_poll.is_some())
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.title == sp.string("Test1"))
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.description_link == sp.string("link1"))
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.description_hash == sp.string("hash1"))
        scenario.verify(~c1.data.outcomes[0].poll_data.proposal.proposal_lambda.is_some())
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.voting_strategy == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.proposal_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.author == admin.address)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_strategy_address == simulated_voting_strategy_one.address)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_id == 3)
        scenario.verify(c1.data.outcomes[0].poll_data.snapshot_block == 1213)

        scenario.p("13. Inject another valid proposal")
        proposal_1 = sp.record(title="Test2",
                               description_link="link2",
                               description_hash="hash2",
                               proposal_lambda=sp.none,
                               voting_strategy=1
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("14. Call propose_callback can be called")
        snapshot_block_2 = 2312
        propose_callback_params_valid_2 = sp.record(id=voting_id, snapshot_block=snapshot_block_2)
        c1.propose_callback(propose_callback_params_valid_2).run(valid=True, sender=simulated_voting_strategy_two.address)

        scenario.p("15. Let's close the vote now")
        scenario.verify(simulated_voting_strategy_two.data.end_called_times == 0)
        c1.end(1).run(valid=True, sender=alice.address)

        scenario.p("16. Call successfully the  end_callback")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(~c1.data.outcomes.contains(1))
        end_callback_valid_2 = sp.record(voting_id=voting_id, voting_outcome=PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(end_callback_valid_2).run(valid=True, sender=simulated_voting_strategy_two.address)

        scenario.p("17. Check the storage of the contract is as expected")
        scenario.verify(c1.data.state == NONE)
        scenario.verify(c1.data.next_proposal_id == 2)
        scenario.verify(~c1.data.ongoing_poll.is_some())
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.title == sp.string("Test1"))
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.description_link == sp.string("link1"))
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.description_hash == sp.string("hash1"))
        scenario.verify(~c1.data.outcomes[0].poll_data.proposal.proposal_lambda.is_some())
        scenario.verify(c1.data.outcomes[0].poll_data.proposal.voting_strategy == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.proposal_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.author == admin.address)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_strategy_address == simulated_voting_strategy_one.address)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_id == 3)
        scenario.verify(c1.data.outcomes[0].poll_data.snapshot_block == 1213)
        scenario.verify(c1.data.outcomes[1].outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[1].poll_data.proposal.title == sp.string("Test2"))
        scenario.verify(c1.data.outcomes[1].poll_data.proposal.description_link == sp.string("link2"))
        scenario.verify(c1.data.outcomes[1].poll_data.proposal.description_hash == sp.string("hash2"))
        scenario.verify(~c1.data.outcomes[1].poll_data.proposal.proposal_lambda.is_some())
        scenario.verify(c1.data.outcomes[1].poll_data.proposal.voting_strategy == 1)
        scenario.verify(c1.data.outcomes[1].poll_data.proposal_id == 1)
        scenario.verify(c1.data.outcomes[1].poll_data.author == admin.address)
        scenario.verify(c1.data.outcomes[1].poll_data.voting_strategy_address == simulated_voting_strategy_two.address)
        scenario.verify(c1.data.outcomes[1].poll_data.voting_id == 3)
        scenario.verify(c1.data.outcomes[1].poll_data.snapshot_block == 2312)

def unit_test_offchain_views(is_default=True):
    @sp.add_test(name="unit_test_offchain_views", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_offchain_views")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(
            scenario, admin)

        voting_id = 3
        snapshot_block = 1213
        propose_callback_params_valid = sp.record(id=voting_id, snapshot_block=snapshot_block)

        end_callback_valid = sp.record(voting_id=voting_id, voting_outcome=PollOutcome.POLL_OUTCOME_PASSED)

        scenario.h2("Test the end_callback entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. Inject a valid proposal")
        scenario.verify(c1.is_poll_in_progress() == False)
        scenario.verify(c1.get_contract_state() == NONE)
        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)
        scenario.verify(c1.is_poll_in_progress() == True)
        scenario.verify(c1.get_contract_state() == STARTING_VOTE)

        scenario.p("3. Call propose_callback can be called")
        c1.propose_callback(propose_callback_params_valid).run(valid=True,
                                                               sender=simulated_voting_strategy_one.address)
        scenario.verify(c1.get_contract_state() == VOTE_ONGOING)

        scenario.p("4. Let's close the vote now")
        c1.end(0).run(valid=True, sender=alice.address)
        scenario.verify(c1.get_contract_state() == ENDING_VOTE)

        scenario.p("5. Call successfully the  end_callback")
        scenario.verify(c1.get_number_of_historical_outcomes() == 0)
        scenario.verify(c1.is_poll_in_progress() == True)
        c1.end_callback(end_callback_valid).run(valid=True, sender=simulated_voting_strategy_one.address)
        scenario.verify(c1.is_poll_in_progress() == False)

        scenario.p("6. Check the storage of the contract is as expected")
        scenario.verify(c1.get_number_of_historical_outcomes() == 1)
        scenario.verify(c1.get_contract_state() == NONE)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(outcome_0.poll_data.proposal.title == sp.string("Test1"))
        scenario.verify(outcome_0.poll_data.proposal.description_link == sp.string("link1"))
        scenario.verify(outcome_0.poll_data.proposal.description_hash == sp.string("hash1"))
        scenario.verify(~outcome_0.poll_data.proposal.proposal_lambda.is_some())
        scenario.verify(outcome_0.poll_data.proposal.voting_strategy == 0)
        scenario.verify(outcome_0.poll_data.proposal_id == 0)
        scenario.verify(outcome_0.poll_data.author == admin.address)
        scenario.verify(
            outcome_0.poll_data.voting_strategy_address == simulated_voting_strategy_one.address)
        scenario.verify(outcome_0.poll_data.voting_id == 3)
        scenario.verify(outcome_0.poll_data.snapshot_block == 1213)

        scenario.p("7. Inject another valid proposal")
        proposal_1 = sp.record(title="Test2",
                               description_link="link2",
                               description_hash="hash2",
                               proposal_lambda=sp.none,
                               voting_strategy=1
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)
        scenario.verify(c1.is_poll_in_progress() == True)
        scenario.verify(c1.get_contract_state() == STARTING_VOTE)

        scenario.p("8. Call propose_callback can be called")
        snapshot_block_2 = 2312
        propose_callback_params_valid_2 = sp.record(id=voting_id, snapshot_block=snapshot_block_2)
        c1.propose_callback(propose_callback_params_valid_2).run(valid=True,
                                                                 sender=simulated_voting_strategy_two.address)
        scenario.verify(c1.get_contract_state() == VOTE_ONGOING)

        scenario.p("9. Let's close the vote now")
        scenario.verify(simulated_voting_strategy_two.data.end_called_times == 0)
        c1.end(1).run(valid=True, sender=alice.address)
        scenario.verify(c1.get_contract_state() == ENDING_VOTE)

        scenario.p("10. Call successfully the  end_callback")
        scenario.verify(c1.is_poll_in_progress() == True)
        end_callback_valid_2 = sp.record(voting_id=voting_id, voting_outcome=PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(end_callback_valid_2).run(valid=True, sender=simulated_voting_strategy_two.address)
        scenario.verify(c1.is_poll_in_progress() == False)

        scenario.p("11. Check the storage of the contract is as expected")
        scenario.verify(c1.get_number_of_historical_outcomes() == 2)
        scenario.verify(c1.get_contract_state() == NONE)
        outcome_0 = c1.get_historical_outcome_data(0)
        outcome_1 = c1.get_historical_outcome_data(1)
        scenario.verify(outcome_0.outcome == PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(outcome_0.poll_data.proposal.title == sp.string("Test1"))
        scenario.verify(outcome_0.poll_data.proposal.description_link == sp.string("link1"))
        scenario.verify(outcome_0.poll_data.proposal.description_hash == sp.string("hash1"))
        scenario.verify(~outcome_0.poll_data.proposal.proposal_lambda.is_some())
        scenario.verify(outcome_0.poll_data.proposal.voting_strategy == 0)
        scenario.verify(outcome_0.poll_data.proposal_id == 0)
        scenario.verify(outcome_0.poll_data.author == admin.address)
        scenario.verify(
            outcome_0.poll_data.voting_strategy_address == simulated_voting_strategy_one.address)
        scenario.verify(outcome_0.poll_data.voting_id == 3)
        scenario.verify(outcome_0.poll_data.snapshot_block == 1213)
        scenario.verify(outcome_1.outcome == PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(outcome_1.poll_data.proposal.title == sp.string("Test2"))
        scenario.verify(outcome_1.poll_data.proposal.description_link == sp.string("link2"))
        scenario.verify(outcome_1.poll_data.proposal.description_hash == sp.string("hash2"))
        scenario.verify(~outcome_1.poll_data.proposal.proposal_lambda.is_some())
        scenario.verify(outcome_1.poll_data.proposal.voting_strategy == 1)
        scenario.verify(outcome_1.poll_data.proposal_id == 1)
        scenario.verify(outcome_1.poll_data.author == admin.address)
        scenario.verify(
            outcome_1.poll_data.voting_strategy_address == simulated_voting_strategy_two.address)
        scenario.verify(outcome_1.poll_data.voting_id == 3)
        scenario.verify(outcome_1.poll_data.snapshot_block == 2312)


unit_test_initial_storage()
unit_test_set_administrator()
unit_test_register_angry_teenager_fa2()
unit_test_mutez_transfer()
unit_test_add_voting_strategy()
unit_test_propose()
unit_test_propose_callback()
unit_test_vote()
unit_test_end()
unit_test_end_callback()
unit_test_offchain_views()
