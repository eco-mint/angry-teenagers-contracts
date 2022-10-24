import smartpy as sp

DAO = sp.io.import_script_from_url("file:./dao/dao.py")

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
        c1 = DAO.AngryTeenagersDao(admin=admin.address,
                              metadata=sp.utils.metadata_of_url("https://example.com"),
                              poll_manager=sp.map(l = {0 : sp.record(name="One", address=simulated_voting_strategy_one.address), 1: sp.record(name="Two", address=simulated_voting_strategy_two.address)}))

        c1.set_initial_balance(sp.mutez(300000000))
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
    def start(self, total_available_voters):
        sp.set_type(total_available_voters, sp.TNat)
        self.data.start_called_times = self.data.start_called_times + 1
        self.data.total_available_voters = total_available_voters

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
        scenario.verify(~c1.data.next_admin.is_some())
        scenario.verify(c1.data.state == DAO.NONE)
        scenario.verify(c1.data.next_proposal_id == sp.nat(0))
        scenario.verify(~c1.data.angry_teenager_fa2.is_some())
        scenario.verify(~c1.data.ongoing_poll.is_some())
        scenario.verify(sp.len(c1.data.poll_manager) == 2)
        scenario.verify(c1.data.poll_manager[0] == sp.record(name="One", address=simulated_voting_strategy_one.address))
        scenario.verify(c1.data.poll_manager[1] == sp.record(name="Two", address=simulated_voting_strategy_two.address))
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

def unit_test_set_next_administrator(is_default = True):
    @sp.add_test(name="unit_test_set_next_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_next_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the set_next_administrator entrypoint. (Who: Only for the admin)")
        scenario.p("This function is used to change the administrator of the contract. This is two steps process. validate_next_admin shall be called after.")

        scenario.p("1. Check only admin can call this entrypoint (i.e only the current admin can change the admin)")
        c1.set_next_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_next_administrator(admin.address).run(valid=False, sender=bob)
        c1.set_next_administrator(bob.address).run(valid=False, sender=john)

        scenario.p("2. Check this function does not change the admin but only the next_admin field.")
        c1.set_next_administrator(alice.address).run(valid=True, sender=admin)
        scenario.verify(c1.data.admin == admin.address)
        scenario.verify(c1.data.next_admin.open_some() == alice.address)

        scenario.p("3. This function can be called several times but only by the admin.")
        c1.set_next_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_next_administrator(admin.address).run(valid=False, sender=bob)
        c1.set_next_administrator(bob.address).run(valid=False, sender=john)
        c1.set_next_administrator(bob.address).run(valid=True, sender=admin)
        scenario.verify(c1.data.admin == admin.address)
        scenario.verify(c1.data.next_admin.open_some() == bob.address)

def unit_test_validate_new_administrator(is_default = True):
    @sp.add_test(name="unit_test_validate_new_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_validate_new_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the unit_test_validate_new_administrator entrypoint.")
        scenario.p("This function is used to change the administrator of the contract. This is two steps process.")

        scenario.p("1. set_next_administrator shall be called prior to validate_next_administrator")
        c1.validate_new_administrator().run(valid=False, sender=admin)
        c1.validate_new_administrator().run(valid=False, sender=alice)
        c1.validate_new_administrator().run(valid=False, sender=bob)

        scenario.p("2. Call set_next_administrator successfully")
        c1.set_next_administrator(alice.address).run(valid=True, sender=admin)

        scenario.p("3. Only alice can call validate_next_address")
        c1.validate_new_administrator().run(valid=False, sender=admin)
        c1.validate_new_administrator().run(valid=False, sender=bob)
        c1.validate_new_administrator().run(valid=True, sender=alice)
        scenario.verify(c1.data.admin == alice.address)
        scenario.verify(~c1.data.next_admin.is_some())

        scenario.p("3. Alice is now admin. She can give the admin right to bob")
        c1.set_next_administrator(bob.address).run(valid=False, sender=bob)
        c1.set_next_administrator(bob.address).run(valid=False, sender=admin)
        c1.set_next_administrator(bob.address).run(valid=True, sender=alice)
        c1.validate_new_administrator().run(valid=False, sender=admin)
        c1.validate_new_administrator().run(valid=False, sender=alice)
        c1.validate_new_administrator().run(valid=True, sender=bob)
        scenario.verify(c1.data.admin == bob.address)
        scenario.verify(~c1.data.next_admin.is_some())

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

        scenario.h2("Test the mutez_transfer entrypoint.  (Who: Only for the DAO)")
        scenario.p("This entrypoint is called byt the admin to extract fund on the contract. Normally no funds are supposed to be held in the contract however if something bad happens or somebody makes a mistake transfer, we still want to have the ability to extract the fund.")

        scenario.p("1. Check that only the DAO can call this entrypoint")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=alice)
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=admin)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(200000000))).run(valid=False, sender=john)

        scenario.p("2. Check the function extracts the fund as expected")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=True, sender=c1.address)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(100000000))).run(valid=True, sender=c1.address)

        scenario.p("3. Check no fund are remaining")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(100000000))).run(valid=False, sender=c1.address)

def unit_test_set_delegate(is_default=True):
    @sp.add_test(name="unit_test_set_delegate", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_delegate")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(
            scenario, admin, john)

        scenario.h2("Test the set_delegate entrypoint.  (Who: Only for the DAO)")

        scenario.p("1. Check the delegate doesn't exist by default")
        scenario.verify(~c1.baker.is_some())

        scenario.p("1. Check that only the DAO can call this entrypoint")
        votings_powers = sp.map(l = {alice.public_key_hash: 10, admin.public_key_hash: 100, john.public_key_hash: 20}, tkey=sp.TKeyHash, tvalue=sp.TNat)
        c1.delegate(sp.some(alice.public_key_hash)).run(valid=False, sender=alice, voting_powers=votings_powers)
        c1.delegate(sp.some(alice.public_key_hash)).run(valid=False, sender=admin, voting_powers=votings_powers)
        c1.delegate(sp.some(alice.public_key_hash)).run(valid=False, sender=john, voting_powers=votings_powers)

        scenario.p("2. Check the entrypoint works as expected")
        c1.delegate(sp.some(alice.public_key_hash)).run(valid=True, sender=c1.address, voting_powers=votings_powers)
        scenario.verify(c1.baker.open_some() == alice.public_key_hash)
        c1.delegate(sp.some(admin.public_key_hash)).run(valid=True, sender=c1.address, voting_powers=votings_powers)
        scenario.verify(c1.baker.open_some() == admin.public_key_hash)


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
        scenario.verify(c1.data.state == DAO.NONE)
        scenario.verify(~c1.data.ongoing_poll.is_some())

        scenario.p("6. Inject a valid proposal")
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("6. Check storage is as expected")
        scenario.verify(c1.data.state == DAO.STARTING_VOTE)
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

def unit_test_propose_callback(is_default = True):
    @sp.add_test(name="unit_test_propose_callback", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_propose_callback")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        voting_id = 3
        snapshot_block = 1213
        propose_callback_params_valid = voting_id

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
        c1.propose(proposal_1).run(valid=True, sender=admin.address, level=snapshot_block)

        scenario.p("4. Only the chosen voting strategy can call the propose_callback")
        c1.propose_callback(propose_callback_params_valid).run(valid=False, sender=simulated_voting_strategy_two.address)

        scenario.p("4. Now the propose_callback can be called")
        c1.propose_callback(propose_callback_params_valid).run(valid=True, sender=simulated_voting_strategy_one.address)

        scenario.p("5. Check the storage of the contract is as expected")
        scenario.verify(c1.data.state == DAO.VOTE_ONGOING)
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
        propose_callback_params_valid = voting_id
        proposal_id = 0
        vote_value = DAO.VoteValue.YAY
        vote_param = sp.record(proposal_id=proposal_id, vote_value=vote_value)

        scenario.h2("Test the vote entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin, level=snapshot_block)

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
        scenario.verify(simulated_voting_strategy_one.data.vote_last_value == DAO.VoteValue.YAY)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_id == 3)
        scenario.verify(simulated_voting_strategy_one.data.vote_numbers == 127)

        scenario.p("8. Cannot vote with 0 voting_power")
        simulated_fa2.change_voting_power(0)
        proposal_id = 0
        vote_value_2 = DAO.VoteValue.NAY
        vote_param_2 = sp.record(proposal_id=proposal_id, vote_value=vote_value_2)
        c1.vote(vote_param_2).run(valid=False, sender=bob.address)

        scenario.p("8. Vote with valid voting_power")
        simulated_fa2.change_voting_power(1)
        c1.vote(vote_param_2).run(valid=True, sender=bob.address)

        scenario.p("8. Check the callback has been called as expected")
        scenario.verify(simulated_voting_strategy_one.data.vote_called_times == 2)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_address.is_some())
        scenario.verify(simulated_voting_strategy_one.data.vote_last_address.open_some() == bob.address)
        scenario.verify(simulated_voting_strategy_one.data.vote_last_value == DAO.VoteValue.NAY)
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
        propose_callback_params_valid = voting_id

        scenario.h2("Test the end entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin, level=snapshot_block)

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
        scenario.verify(c1.data.state == DAO.ENDING_VOTE)

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
        propose_callback_params_valid = voting_id

        end_callback_valid = sp.record(voting_id=voting_id, voting_outcome=DAO.PollOutcome.POLL_OUTCOME_PASSED)
        end_callback_invalid = sp.record(voting_id=0, voting_outcome=DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.h2("Test the end_callback entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin, level=snapshot_block)

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
        scenario.verify(c1.data.state == DAO.NONE)
        scenario.verify(c1.data.next_proposal_id == 1)
        scenario.verify(~c1.data.ongoing_poll.is_some())
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        snapshot_block_2 = 2312
        c1.propose(proposal_1).run(valid=True, sender=admin.address, level=2312)

        scenario.p("14. Call propose_callback can be called")
        propose_callback_params_valid_2 = voting_id
        c1.propose_callback(propose_callback_params_valid_2).run(valid=True, sender=simulated_voting_strategy_two.address, level=snapshot_block_2)

        scenario.p("15. Let's close the vote now")
        scenario.verify(simulated_voting_strategy_two.data.end_called_times == 0)
        c1.end(1).run(valid=True, sender=alice.address)

        scenario.p("16. Call successfully the  end_callback")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(~c1.data.outcomes.contains(1))
        end_callback_valid_2 = sp.record(voting_id=voting_id, voting_outcome=DAO.PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(end_callback_valid_2).run(valid=True, sender=simulated_voting_strategy_two.address)

        scenario.p("17. Check the storage of the contract is as expected")
        scenario.verify(c1.data.state == DAO.NONE)
        scenario.verify(c1.data.next_proposal_id == 2)
        scenario.verify(~c1.data.ongoing_poll.is_some())
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        scenario.verify(c1.data.outcomes[1].outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
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
        propose_callback_params_valid = voting_id

        end_callback_valid = sp.record(voting_id=voting_id, voting_outcome=DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.h2("Test the end_callback entrypoint.")

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin, level=snapshot_block)

        scenario.p("2. Inject a valid proposal")
        scenario.verify(c1.is_poll_in_progress() == False)
        scenario.verify(c1.get_contract_state() == DAO.NONE)
        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )
        c1.propose(proposal_1).run(valid=True, sender=admin.address)
        scenario.verify(c1.is_poll_in_progress() == True)
        scenario.verify(c1.get_contract_state() == DAO.STARTING_VOTE)

        scenario.p("3. Call propose_callback can be called")
        c1.propose_callback(propose_callback_params_valid).run(valid=True,
                                                               sender=simulated_voting_strategy_one.address)
        scenario.verify(c1.get_contract_state() == DAO.VOTE_ONGOING)

        scenario.p("4. Let's close the vote now")
        c1.end(0).run(valid=True, sender=alice.address)
        scenario.verify(c1.get_contract_state() == DAO.ENDING_VOTE)

        scenario.p("5. Call successfully the  end_callback")
        scenario.verify(c1.get_number_of_historical_outcomes() == 0)
        scenario.verify(c1.is_poll_in_progress() == True)
        c1.end_callback(end_callback_valid).run(valid=True, sender=simulated_voting_strategy_one.address)
        scenario.verify(c1.is_poll_in_progress() == False)

        scenario.p("6. Check the storage of the contract is as expected")
        scenario.verify(c1.get_number_of_historical_outcomes() == 1)
        scenario.verify(c1.get_contract_state() == DAO.NONE)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        snapshot_block_2 = 2312
        c1.propose(proposal_1).run(valid=True, sender=admin.address, level=2312)
        scenario.verify(c1.is_poll_in_progress() == True)
        scenario.verify(c1.get_contract_state() == DAO.STARTING_VOTE)

        scenario.p("8. Call propose_callback can be called")
        propose_callback_params_valid_2 = voting_id
        c1.propose_callback(propose_callback_params_valid_2).run(valid=True,
                                                                 sender=simulated_voting_strategy_two.address,
                                                                 level=snapshot_block_2)
        scenario.verify(c1.get_contract_state() == DAO.VOTE_ONGOING)

        scenario.p("9. Let's close the vote now")
        scenario.verify(simulated_voting_strategy_two.data.end_called_times == 0)
        c1.end(1).run(valid=True, sender=alice.address)
        scenario.verify(c1.get_contract_state() == DAO.ENDING_VOTE)

        scenario.p("10. Call successfully the  end_callback")
        scenario.verify(c1.is_poll_in_progress() == True)
        end_callback_valid_2 = sp.record(voting_id=voting_id, voting_outcome=DAO.PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(end_callback_valid_2).run(valid=True, sender=simulated_voting_strategy_two.address)
        scenario.verify(c1.is_poll_in_progress() == False)

        scenario.p("11. Check the storage of the contract is as expected")
        scenario.verify(c1.get_number_of_historical_outcomes() == 2)
        scenario.verify(c1.get_contract_state() == DAO.NONE)
        outcome_0 = c1.get_historical_outcome_data(0)
        outcome_1 = c1.get_historical_outcome_data(1)
        scenario.verify(outcome_0.outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        scenario.verify(outcome_1.outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
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

def unit_test_unlock_contract_start(is_default = True):
    @sp.add_test(name="unit_test_unlock_contract_start", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_unlock_contract_start")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the unlock_contract entrypoint when start is stuck.")

        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. Entrypoint can only be called when we are in STARTING_VOTE and ENDING_VOTE")
        c1.unlock_contract().run(valid=False, sender=admin.address)

        scenario.p("3. Inject a valid proposal")
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("4. Check storage is as expected")
        scenario.verify(c1.data.state == DAO.STARTING_VOTE)

        scenario.p("5. Only admin can unlock the contract")
        c1.unlock_contract().run(valid=False, sender=alice.address, level=sp.level + 11)
        c1.unlock_contract().run(valid=False, sender=bob.address, level=sp.level + 11)
        c1.unlock_contract().run(valid=False, sender=john.address, level=sp.level + 11)
        scenario.verify(c1.data.state == DAO.STARTING_VOTE)

        scenario.p("6. unlock the contract successfully")
        c1.unlock_contract().run(valid=True, sender=admin.address, level=sp.level + 11)
        scenario.verify(c1.data.state == DAO.NONE)
        scenario.verify(~c1.data.time_ref.is_some())
        scenario.verify(~c1.data.ongoing_poll.is_some())

        scenario.p("7. Inject a valid proposal")
        c1.propose(proposal_1).run(valid=True, sender=admin.address)

        scenario.p("8. Unlock can only be called when more than 10 blocks have passed")
        c1.unlock_contract().run(valid=False, sender=admin.address, level=sp.level + 10)

        scenario.p("9. Call propose_callback")
        voting_id = 3
        c1.propose_callback(voting_id).run(valid=True, sender=simulated_voting_strategy_one.address)
        scenario.verify(c1.data.state == DAO.VOTE_ONGOING)
        scenario.verify(~c1.data.time_ref.is_some())

        scenario.p("10. Unlock cannot be called anymore")
        c1.unlock_contract().run(valid=False, sender=admin.address)

def unit_test_unlock_contract_end(is_default = True):
    @sp.add_test(name="unit_test_unlock_contract_end", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_unlock_contract_end")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_voting_strategy_one, simulated_voting_strategy_two, simulated_fa2 = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test the unlock_contract entrypoint when end is stuck.")

        proposal_1 = sp.record(title="Test1",
                               description_link="link1",
                               description_hash="hash1",
                               proposal_lambda=sp.none,
                               voting_strategy=0
                               )

        scenario.p("1. Register the FA2 contract")
        c1.register_angry_teenager_fa2(simulated_fa2.address).run(valid=True, sender=admin)

        scenario.p("2. Go to ending state")
        c1.propose(proposal_1).run(valid=True, sender=admin.address)
        c1.propose_callback(3).run(valid=True, sender=simulated_voting_strategy_one.address)
        c1.end(0).run(valid=True, sender=admin.address)

        scenario.p("3. Check storage is as expected")
        scenario.verify(c1.data.state == DAO.ENDING_VOTE)

        scenario.p("4. Only admin can unlock the contract")
        c1.unlock_contract().run(valid=False, sender=alice.address, level=sp.level + 11)
        c1.unlock_contract().run(valid=False, sender=bob.address, level=sp.level + 11)
        c1.unlock_contract().run(valid=False, sender=john.address, level=sp.level + 11)
        scenario.verify(c1.data.state == DAO.ENDING_VOTE)

        scenario.p("5. unlock the contract successfully")
        c1.unlock_contract().run(valid=True, sender=admin.address, level=sp.level + 11)
        scenario.verify(c1.data.state == DAO.NONE)
        scenario.verify(~c1.data.time_ref.is_some())
        scenario.verify(~c1.data.ongoing_poll.is_some())

        scenario.p("6. Go to ending state again")
        c1.propose(proposal_1).run(valid=True, sender=admin.address)
        c1.propose_callback(3).run(valid=True, sender=simulated_voting_strategy_one.address)
        c1.end(0).run(valid=True, sender=admin.address)

        scenario.p("7. Unlock can only be called when more than 10 blocks have passed")
        c1.unlock_contract().run(valid=False, sender=admin.address, level=sp.level + 10)

        scenario.p("8. Call end_callback")
        c1.end_callback(sp.record(voting_id=3, voting_outcome=0)).run(valid=True, sender=simulated_voting_strategy_one.address)
        scenario.verify(c1.data.state == DAO.NONE)
        scenario.verify(~c1.data.time_ref.is_some())

        scenario.p("9. Unlock cannot be called anymore")
        c1.unlock_contract().run(valid=False, sender=admin.address)

unit_test_initial_storage()
unit_test_set_next_administrator()
unit_test_validate_new_administrator()
unit_test_register_angry_teenager_fa2()
unit_test_mutez_transfer()
unit_test_set_delegate()
unit_test_add_voting_strategy()
unit_test_propose()
unit_test_propose_callback()
unit_test_vote()
unit_test_end()
unit_test_end_callback()
unit_test_offchain_views()
unit_test_unlock_contract_start()
unit_test_unlock_contract_end()

