import smartpy as sp

DAO = sp.io.import_script_from_url("file:./dao/majority_voting.py")


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
            c1 = DAO.DaoMajorityVoting(admin=admin.address,
                                   current_dynamic_quorum_value_pertenmill=sp.nat(3000),
                                   governance_parameters=sp.record(
                                        vote_delay_blocks = sp.nat(10),
                                        vote_length_blocks = sp.nat(180),
                                        supermajority_pertenmill = sp.nat(8500),
                                        fixed_quorum_pertenmill = sp.nat(2500),
                                        fixed_quorum = sp.bool(True),
                                        quorum_cap_pertenmill = sp.record(lower=sp.nat(1000), upper=sp.nat(9000))),
                                   metadata=sp.utils.metadata_of_url("https://example.com"))
        else:
            c1 = DAO.DaoMajorityVoting(admin=admin.address,
                                   current_dynamic_quorum_value_pertenmill=sp.nat(3000),
                                   governance_parameters=sp.record(
                                        vote_delay_blocks = sp.nat(10),
                                        vote_length_blocks = sp.nat(180),
                                        supermajority_pertenmill = sp.nat(8500),
                                        fixed_quorum_pertenmill= sp.nat(2500),
                                        fixed_quorum = sp.bool(False),
                                        quorum_cap_pertenmill = sp.record(lower=sp.nat(1000), upper=sp.nat(9000))),
                                   metadata=sp.utils.metadata_of_url("https://example.com"))
        simulated_poll_leader_contract = SimulatedLeaderPoll(scenario)
        c1.set_initial_balance(sp.mutez(300000000))
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
            end_callback_called_times = sp.nat(0),
            end_callback_voting_id = sp.nat(100),
            end_callback_voting_outcome = sp.nat(100)
        )
        self.scenario = scenario

    @sp.entry_point()
    def propose_callback(self, params):
        sp.set_type(params, sp.TNat)
        self.data.propose_callback_called_times = self.data.propose_callback_called_times + 1
        self.data.propose_callback_id = params

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
        scenario.verify(c1.data.next_admin == sp.none)
        scenario.verify(~c1.data.poll_leader.is_some())
        scenario.verify(c1.data.vote_id == 0)
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.vote_state == 0)
        scenario.verify(c1.data.governance_parameters.vote_delay_blocks == sp.nat(10))
        scenario.verify(c1.data.governance_parameters.vote_length_blocks == sp.nat(180))
        scenario.verify(c1.data.governance_parameters.supermajority_pertenmill == sp.nat(8500))
        scenario.verify(c1.data.governance_parameters.fixed_quorum_pertenmill == sp.nat(2500))
        scenario.verify(c1.data.governance_parameters.fixed_quorum == sp.bool(False))
        scenario.verify(c1.data.governance_parameters.quorum_cap_pertenmill.lower == sp.nat(1000))
        scenario.verify(c1.data.governance_parameters.quorum_cap_pertenmill.upper == sp.nat(9000))

        scenario.verify(c1.data.current_dynamic_quorum_value_pertenmill == sp.nat(3000))
        scenario.verify(~c1.data.outcomes.contains(0))
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

def unit_test_set_next_administrator(is_default = True):
    @sp.add_test(name="unit_test_set_next_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_next_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

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
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

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

        total_available_voters = sp.nat(10000)

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
        scenario.verify(c1.data.vote_state == DAO.NONE)
        c1.start(total_available_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Check it is started")
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().vote_nay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_yay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_abstain == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().total_votes == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().quorum == (c1.data.current_dynamic_quorum_value_pertenmill * total_available_voters) // DAO.SCALE_PERTENMILL)
        start_block = sp.level + c1.data.governance_parameters.vote_delay_blocks
        scenario.verify(c1.data.poll_descriptor.open_some().voting_start_block == start_block)
        scenario.verify(c1.data.poll_descriptor.open_some().voting_end_block == start_block + c1.data.governance_parameters.vote_length_blocks)
        scenario.verify(c1.data.vote_state == DAO.IN_PROGRESS)

        scenario.p("4. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_id == 0)

# Description: Test the start function.
def unit_test_start_with_fixed_quorum(is_default = True):
    @sp.add_test(name="unit_test_start_with_fixed_quorum", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_start_with_fixed_quorum")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, with_fixed_quorum=True)

        scenario.h2("Test the start function with a fixed quorum.")

        total_available_voters = sp.nat(10000)

        scenario.p("1. Register poll_leader contract")
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start with fixed quorum")
        scenario.verify(~c1.data.poll_descriptor.is_some())
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_id == 100)
        scenario.verify(c1.data.vote_state == DAO.NONE)
        c1.start(total_available_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Check it is started")
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify(c1.data.poll_descriptor.open_some().vote_nay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_yay == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_abstain == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().total_votes == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        fixed_quorum = (total_available_voters * c1.data.governance_parameters.fixed_quorum_pertenmill) // DAO.SCALE_PERTENMILL
        scenario.verify(c1.data.poll_descriptor.open_some().quorum == fixed_quorum)
        start_block = sp.level + c1.data.governance_parameters.vote_delay_blocks
        scenario.verify(c1.data.poll_descriptor.open_some().voting_start_block == start_block)
        scenario.verify(c1.data.poll_descriptor.open_some().voting_end_block == start_block + c1.data.governance_parameters.vote_length_blocks)
        scenario.verify(c1.data.vote_state == DAO.IN_PROGRESS)

        scenario.p("4. Check the expected callback is called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 0)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_id == 0)

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
        alice_vote_param_valid_yay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Only poll leader can send the vote")
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=john.address)

        scenario.p("5. Cannot vote if vote_id is invalid")
        vote_param_invalid_vote_id = sp.record(votes=sp.nat(10), address=alice.address, vote_value=DAO.VoteValue.YAY , vote_id=sp.nat(1))
        c1.vote(vote_param_invalid_vote_id).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("6. Start block shall be reached to start the vote")
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)
        start_block = c1.data.governance_parameters.vote_delay_blocks
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("7. Successfully vote yay")
        c1.vote(alice_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("8. Alice cannot vote anymore")
        c1.vote(alice_vote_param_valid_yay).run().run(valid=False, sender=simulated_poll_leader_contract.address)
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(1), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        alice_vote_param_valid_abstain = sp.record(votes=sp.nat(2), address=alice.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=simulated_poll_leader_contract.address)
        c1.vote(alice_vote_param_valid_abstain).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("9. Chris votes yay, Gabe votes nay and Ben votes abstain")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(36), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(100), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(250), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("10. Vote value is invalid")
        bob_invalid_vote_value = sp.record(votes=sp.nat(1), address=bob.address, vote_value=3, vote_id=sp.nat(0))
        c1.vote(bob_invalid_vote_value).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("11. Admin successfull vote")
        admin_valid_vote = sp.record(votes=sp.nat(30), address=admin.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(admin_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=(start_block + 50))

        scenario.p("12. Bob successfull vote")
        bob_valid_vote = sp.record(votes=sp.nat(112), address=bob.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
        end_block = start_block + c1.data.governance_parameters.vote_length_blocks
        c1.vote(bob_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block)

        scenario.p("13. Bob can only vote one time")
        c1.vote(bob_valid_vote).run().run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("14. John cannot vote anymore. It is too late.")
        john_valid_vote = sp.record(votes=sp.nat(30), address=john.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(john_valid_vote).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block + 1)
        c1.vote(john_valid_vote).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block + 30)

        scenario.p("15. Check votes are counted as expected")
        scenario.verify(c1.data.poll_descriptor.is_some())
        scenario.verify_equal(c1.data.poll_descriptor.open_some().vote_nay, 130)
        scenario.verify_equal(c1.data.poll_descriptor.open_some().vote_yay, 46)
        scenario.verify_equal(c1.data.poll_descriptor.open_some().vote_abstain, 362)
        scenario.verify_equal(c1.data.poll_descriptor.open_some().total_votes, 538)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)

        # Bob
        scenario.verify(c1.data.voters_history.get(sp.record(address=bob.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.ABSTAIN)
        scenario.verify(c1.data.voters_history.get(sp.record(address=bob.address, vote_id=0), message="No voters").votes == 112)
        scenario.verify(c1.data.voters_history.get(sp.record(address=bob.address, vote_id=0), message="No voters").level == end_block)

        # Admin
        scenario.verify(c1.data.voters_history.get(sp.record(address=admin.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.NAY)
        scenario.verify(c1.data.voters_history.get(sp.record(address=admin.address, vote_id=0), message="No voters").votes == 30)
        scenario.verify(c1.data.voters_history.get(sp.record(address=admin.address, vote_id=0), message="No voters").level == start_block + 50)

        # Chris
        scenario.verify(c1.data.voters_history.get(sp.record(address=chris.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.YAY)
        scenario.verify(c1.data.voters_history.get(sp.record(address=chris.address, vote_id=0), message="No voters").votes == 36)
        scenario.verify(c1.data.voters_history.get(sp.record(address=chris.address, vote_id=0), message="No voters").level == start_block)

        # Gabe
        scenario.verify(c1.data.voters_history.get(sp.record(address=gabe.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.NAY)
        scenario.verify(c1.data.voters_history.get(sp.record(address=gabe.address, vote_id=0), message="No voters").votes == 100)
        scenario.verify(c1.data.voters_history.get(sp.record(address=gabe.address, vote_id=0), message="No voters").level == start_block)

        # Ben
        scenario.verify(c1.data.voters_history.get(sp.record(address=ben.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.ABSTAIN)
        scenario.verify(c1.data.voters_history.get(sp.record(address=ben.address, vote_id=0), message="No voters").votes == 250)
        scenario.verify(c1.data.voters_history.get(sp.record(address=ben.address, vote_id=0), message="No voters").level == start_block)

        # Alice
        scenario.verify(c1.data.voters_history.get(sp.record(address=alice.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.YAY)
        scenario.verify(c1.data.voters_history.get(sp.record(address=alice.address, vote_id=0), message="No voters").votes == 10)
        scenario.verify(c1.data.voters_history.get(sp.record(address=alice.address, vote_id=0), message="No voters").level == start_block)

        scenario.verify(~c1.data.voters_history.contains(sp.record(address=john.address, vote_id=0)))

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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("5. Check vote_id is incremented for the next vote")
        scenario.verify(c1.data.vote_id == 1)
        scenario.verify(c1.data.vote_state == DAO.NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())
        c1.start(1000).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.data.vote_state == DAO.IN_PROGRESS)
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
        c1.start(11999).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(2909), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(79), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(10), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 2909)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 79)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 2998)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 2999)

        # Chris
        scenario.verify(c1.data.voters_history.get(sp.record(address=chris.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.YAY)
        scenario.verify(c1.data.voters_history.get(sp.record(address=chris.address, vote_id=0), message="No voters").votes == 2909)

        # Gabe
        scenario.verify(c1.data.voters_history.get(sp.record(address=gabe.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.NAY)
        scenario.verify(c1.data.voters_history.get(sp.record(address=gabe.address, vote_id=0), message="No voters").votes == 79)

        # Ben
        scenario.verify(c1.data.voters_history.get(sp.record(address=ben.address, vote_id=0), message="No voters").vote_value == DAO.VoteValue.ABSTAIN)
        scenario.verify(c1.data.voters_history.get(sp.record(address=ben
                                                             .address, vote_id=0), message="No voters").votes == 10)

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
        c1.start(11999).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(2909), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(79), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(11), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 2909)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 79)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 11)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 2999)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 2999)

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
        c1.start(11999).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(8573), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(1514), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(0), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 8573)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 1514)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 10087)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 2999)

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
        c1.start(20000).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(12000), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(750), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(250), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 12000)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 750)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 250)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 13000)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 5000)

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
        c1.start(11999).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(3314), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(586), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(99), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 3314)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 586)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 99)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 3999)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 2999)

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
        c1.start(11999).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(314), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(586), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(3099), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)

        scenario.p("6. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 314)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 586)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 3099)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 3999)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 2999)

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
        scenario.verify(c1.data.current_dynamic_quorum_value_pertenmill == sp.nat(3000))

        scenario.p("3. Start poll")
        c1.start(37689).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(13000), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(2000), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(7089), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("7. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_yay == 13000)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_nay == 2000)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_abstain == 7089)
        scenario.verify(c1.data.outcomes[0].poll_data.total_votes == 22089)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_start_block == 10)
        scenario.verify(c1.data.outcomes[0].poll_data.voting_end_block == 190)
        scenario.verify(c1.data.outcomes[0].poll_data.vote_id == 0)
        scenario.verify(c1.data.outcomes[0].poll_data.quorum == 11306)

        scenario.p("8. Check new dynamic quorum is computed")
        new_quorum = ((11306 * 8000) // DAO.SCALE_PERTENMILL) + ((c1.data.outcomes[0].poll_data.total_votes * 2000) // DAO.SCALE_PERTENMILL)
        new_quorum = (new_quorum * DAO.SCALE_PERTENMILL) // 37689
        scenario.verify(c1.data.current_dynamic_quorum_value_pertenmill == new_quorum)

def unit_test_offchain_views(is_default = True):
    @sp.add_test(name="unit_test_offchain_views", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_offchain_views")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test all the offchain views.")

        scenario.p("1. Register poll_leader contract")
        scenario.verify(c1.get_contract_state() == DAO.NONE)
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(10000).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == DAO.IN_PROGRESS)

        scenario.p("3. Add votes")
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(3000), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(400), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(1000), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
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
        scenario.verify(poll_data_0.quorum == 3000)

        scenario.p("5. End the vote")
        scenario.verify(c1.get_contract_state() == DAO.IN_PROGRESS)
        scenario.verify(c1.get_number_of_historical_outcomes() == 0)
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)
        scenario.verify(c1.get_contract_state() == DAO.NONE)

        scenario.p("6. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 1)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
        scenario.verify(outcome_0.poll_data.vote_yay == 3000)
        scenario.verify(outcome_0.poll_data.vote_nay == 400)
        scenario.verify(outcome_0.poll_data.vote_abstain == 1000)
        scenario.verify(outcome_0.poll_data.total_votes == 4400)
        scenario.verify(outcome_0.poll_data.voting_start_block == 10)
        scenario.verify(outcome_0.poll_data.voting_end_block == 190)
        scenario.verify(outcome_0.poll_data.vote_id == 0)
        scenario.verify(outcome_0.poll_data.quorum == 3000)
        scenario.verify(c1.get_contract_state() == DAO.NONE)

        scenario.p("7. Check get_voter_history")
        chris_vote_history = c1.get_voter_history(sp.record(address=chris.address, vote_id=0))
        scenario.verify(chris_vote_history.vote_value == DAO.VoteValue.YAY)
        scenario.verify(chris_vote_history.votes == 3000)

        ben_vote_history = c1.get_voter_history(sp.record(address=ben.address, vote_id=0))
        scenario.verify(ben_vote_history.vote_value == DAO.VoteValue.ABSTAIN)
        scenario.verify(ben_vote_history.votes == 1000)

        gabe_vote_history = c1.get_voter_history(sp.record(address=gabe.address, vote_id=0))
        scenario.verify(gabe_vote_history.vote_value == DAO.VoteValue.NAY)
        scenario.verify(gabe_vote_history.votes == 400)

        scenario.p("8. Start another poll")
        c1.start(10000).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == DAO.IN_PROGRESS)

        scenario.p("9. Add votes")
        chris_vote_param_valid_yay_2 = sp.record(votes=sp.nat(2000), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(1))
        gabe_vote_param_valid_nay_2 = sp.record(votes=sp.nat(2500), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(1))
        ben_vote_param_valid_abstain_2 = sp.record(votes=sp.nat(500), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(1))
        c1.vote(chris_vote_param_valid_yay_2).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + c1.data.governance_parameters.vote_delay_blocks)
        c1.vote(gabe_vote_param_valid_nay_2).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain_2).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == DAO.IN_PROGRESS)

        scenario.p("10. End the vote again")
        skip_vote_period = c1.data.governance_parameters.vote_length_blocks + 1
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address, level=sp.level + skip_vote_period)
        scenario.verify(c1.get_contract_state() == DAO.NONE)

        scenario.p("11. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 2)
        outcome_1 = c1.get_historical_outcome_data(1)
        scenario.verify(outcome_1.poll_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(outcome_1.poll_data.vote_yay == 2000)
        scenario.verify(outcome_1.poll_data.vote_nay == 2500)
        scenario.verify(outcome_1.poll_data.vote_abstain == 500)
        scenario.verify(outcome_1.poll_data.total_votes == 5000)
        scenario.verify(outcome_1.poll_data.voting_start_block == 201)
        scenario.verify(outcome_1.poll_data.voting_end_block == 381)
        scenario.verify(outcome_1.poll_data.vote_id == 1)

        scenario.p("12. Check get_voter_history")
        chris_vote_history_0 = c1.get_voter_history(sp.record(address=chris.address, vote_id=0))
        scenario.verify(chris_vote_history_0.vote_value == DAO.VoteValue.YAY)
        scenario.verify(chris_vote_history_0.votes == 3000)

        ben_vote_history_0 = c1.get_voter_history(sp.record(address=ben.address, vote_id=0))
        scenario.verify(ben_vote_history_0.vote_value == DAO.VoteValue.ABSTAIN)
        scenario.verify(ben_vote_history_0.votes == 1000)

        gabe_vote_history_0 = c1.get_voter_history(sp.record(address=gabe.address, vote_id=0))
        scenario.verify(gabe_vote_history_0.vote_value == DAO.VoteValue.NAY)
        scenario.verify(gabe_vote_history_0.votes == 400)

        chris_vote_history_1 = c1.get_voter_history(sp.record(address=chris.address, vote_id=1))
        scenario.verify(chris_vote_history_1.vote_value == DAO.VoteValue.YAY)
        scenario.verify(chris_vote_history_1.votes == 2000)

        ben_vote_history_1 = c1.get_voter_history(sp.record(address=ben.address, vote_id=1))
        scenario.verify(ben_vote_history_1.vote_value == DAO.VoteValue.ABSTAIN)
        scenario.verify(ben_vote_history_1.votes == 500)

        gabe_vote_history_1 = c1.get_voter_history(sp.record(address=gabe.address, vote_id=1))
        scenario.verify(gabe_vote_history_1.vote_value == DAO.VoteValue.NAY)
        scenario.verify(gabe_vote_history_1.votes == 2500)

def unit_test_mutez_transfer(is_default=True):
    @sp.add_test(name="unit_test_mutez_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mutez_transfer")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the mutez_transfer entrypoint.  (Who: Only for the admin)")
        scenario.p("This entrypoint is called byt the admin to extract fund on the contract. Normally no funds are supposed to be held in the contract however if something bad happens or somebody makes a mistake transfer, we still want to have the ability to extract the fund.")

        scenario.p("1. Check that only the admin can call this entrypoint")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=alice)
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=bob)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(200000000))).run(valid=False, sender=john)

        scenario.p("2. Check the function extracts the fund as expected")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=True, sender=admin)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(100000000))).run(valid=True, sender=admin)

        scenario.p("3. Check no fund are remaining")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(100000000))).run(valid=False, sender=admin)


unit_test_initial_storage()
unit_test_set_next_administrator()
unit_test_validate_new_administrator()
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
unit_test_end_dynamic_quorum()
unit_test_offchain_views()
unit_test_mutez_transfer()
