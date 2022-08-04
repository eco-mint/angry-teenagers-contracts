import smartpy as sp

DAO = sp.io.import_script_from_url("file:./dao/angry_teenagers_opt_out_voting.py")


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
        c1 = DAO.DaoOptOutVoting(admin=admin.address,
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
        scenario.verify(c1.data.vote_state == DAO.NONE)
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
        scenario.verify(c1.data.vote_state == DAO.NONE)
        c1.start(total_available_voters).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Check it is started")
        scenario.verify(c1.data.poll_descriptor.is_some())
        start_block = sp.level + c1.data.governance_parameters.vote_delay_blocks
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_vote_objection == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_start_block == start_block)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_voting_end_block == start_block + c1.data.governance_parameters.vote_length_blocks)
        phase_1_objection_threshold = (total_available_voters * c1.data.governance_parameters.percentage_for_objection) // DAO.SCALE
        scenario.verify(c1.data.poll_descriptor.open_some().phase_1_objection_threshold == phase_1_objection_threshold)
        scenario.verify(c1.data.poll_descriptor.open_some().total_voters == total_available_voters)
        scenario.verify(c1.data.poll_descriptor.open_some().vote_id == 0)
        scenario.verify(sp.len(c1.data.poll_descriptor.open_some().phase_1_voters) == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_needed == sp.bool(False))
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_vote_id == 0)
        scenario.verify(c1.data.poll_descriptor.open_some().phase_2_voting_start_block == 0)
        scenario.verify(c1.data.vote_state == DAO.PHASE_1_OPT_OUT)

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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("3. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("4. Only poll leader can send the vote")
        c1.vote(alice_vote_param_valid_nay).run(valid=False, sender=john.address)

        scenario.p("5. Cannot vote if vote_id is invalid")
        vote_param_invalid_vote_id = sp.record(votes=sp.nat(10), address=alice.address, vote_value=DAO.VoteValue.YAY , vote_id=sp.nat(1))
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
        chris_vote_param_valid_yay = sp.record(votes=sp.nat(36), address=chris.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        chris_vote_param_valid_nay = sp.record(votes=sp.nat(36), address=chris.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        gabe_vote_param_valid_nay = sp.record(votes=sp.nat(100), address=gabe.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        ben_vote_param_valid_abstain = sp.record(votes=sp.nat(250), address=ben.address, vote_value=DAO.VoteValue.ABSTAIN, vote_id=sp.nat(0))
        ben_vote_param_valid_nay = sp.record(votes=sp.nat(250), address=ben.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(chris_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)
        c1.vote(chris_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(gabe_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_abstain).run(valid=False, sender=simulated_poll_leader_contract.address)
        c1.vote(ben_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("10. Vote value is invalid")
        bob_invalid_vote_value = sp.record(votes=sp.nat(1), address=bob.address, vote_value=3, vote_id=sp.nat(0))
        c1.vote(bob_invalid_vote_value).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("11. Admin successfull vote")
        admin_valid_vote = sp.record(votes=sp.nat(30), address=admin.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(admin_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=(start_block + 50))

        scenario.p("12. Bob successfull vote")
        bob_valid_vote = sp.record(votes=sp.nat(112), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        end_block = start_block + c1.data.governance_parameters.vote_length_blocks
        c1.vote(bob_valid_vote).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block)

        scenario.p("13. Bob can only vote one time")
        c1.vote(bob_valid_vote).run().run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("14. John cannot vote anymore. It is too late.")
        john_valid_vote = sp.record(votes=sp.nat(30), address=john.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Cannot close when time is not elapsed")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=False, sender=simulated_poll_leader_contract.address, level=end_block)

        scenario.p("5. Only poll_leader can close")
        c1.end(0).run(valid=False, sender=admin.address, level=end_block + 1)

        scenario.p("6. Let's close now")
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("7. Poll is closed")
        scenario.verify(c1.data.vote_state == DAO.NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("8. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("9. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7999), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2000), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("8. Poll is closed")
        scenario.verify(c1.data.vote_state == DAO.NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("9. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("10. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(520), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("8. Poll is closed")
        scenario.verify(c1.data.vote_state == DAO.NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("9. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("10. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(27), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(38), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("4. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("8. Poll is closed")
        scenario.verify(c1.data.vote_state == DAO.NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("9. Check the expected callback has been called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.propose_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("10. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(3), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
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
        scenario.verify(c1.data.vote_state == DAO.STARTING_PHASE_2)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7999), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2001), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
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
        scenario.verify(c1.data.vote_state == DAO.STARTING_PHASE_2)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(521), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
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
        scenario.verify(c1.data.vote_state == DAO.STARTING_PHASE_2)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(1238), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(521), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
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
        scenario.verify(c1.data.vote_state == DAO.STARTING_PHASE_2)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(1238), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(521), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)

        scenario.p("5. propose_callback can only be called when in state STARTING_PHASE_2")
        param_propose_callback_2 = sp.record(id=1, snapshot_block=sp.level)
        c1.propose_callback(param_propose_callback_2).run(valid=False, sender=simulated_phase2_voting_contract.address)

        scenario.p("6. Let's close now and start phase 2")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)
        scenario.verify(c1.data.vote_state == DAO.STARTING_PHASE_2)

        scenario.p("7. Cannot vote when the propose_callback has not been called")
        alice_vote_param_valid_yay = sp.record(votes=sp.nat(1238), address=alice.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_yay).run(valid=False, sender=simulated_poll_leader_contract.address)

        scenario.p("8. Only the phase 2 contract can call the propose_callback.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=False, sender=admin.address)

        scenario.p("9. The majority voting contract will call the propose_callback. Let's simulate this call.")
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.data.vote_state == DAO.PHASE_2_MAJORITY)

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
        alice_vote_param_valid_yay = sp.record(votes=sp.nat(200), address=alice.address, vote_value=DAO.VoteValue.YAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_yay).run(valid=True, sender=simulated_poll_leader_contract.address, level=snapshot_block)

        scenario.p("12. Verify callback calls")
        scenario.verify(simulated_phase2_voting_contract.data.vote_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.last_votes == 200)
        scenario.verify(simulated_phase2_voting_contract.data.last_address.open_some() == alice.address)
        scenario.verify(simulated_phase2_voting_contract.data.last_vote_id == 1)
        scenario.verify(simulated_phase2_voting_contract.data.last_vote_value == DAO.VoteValue.YAY)

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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("4. The majority voting contract will call the propose_callback. Let's simulate this call.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.data.vote_state == DAO.PHASE_2_MAJORITY)

        scenario.p("5. end_callback cann only be called in state ENDING_PHASE_2.")
        params_end_callback = sp.record(voting_id=sp.nat(1), voting_outcome=DAO.PollOutcome.POLL_OUTCOME_PASSED)
        c1.end_callback(params_end_callback).run(valid=False, sender=simulated_phase2_voting_contract.address)

        scenario.p("6. Simulate end of phase with successful outcome")
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.data.vote_state == DAO.ENDING_PHASE_2)

        scenario.p("7. Check expected callbacks are called")
        scenario.verify(simulated_phase2_voting_contract.data.end_called_times == 1)
        scenario.verify(simulated_phase2_voting_contract.data.end_vote_id == 1)

        scenario.p("8. Only the phase2 contract can call the end_callback.")
        c1.end_callback(params_end_callback).run(valid=False, sender=admin.address)

        scenario.p("9. end_callback can only be called with valid id.")
        params_end_callback_invalid_id = sp.record(voting_id=sp.nat(0), voting_outcome=DAO.PollOutcome.POLL_OUTCOME_PASSED)
        c1.end_callback(params_end_callback_invalid_id).run(valid=False, sender=admin.address)

        scenario.p("10. In return the majority contract will call back this contract to give the result. Let's simulate this.")
        c1.end_callback(params_end_callback).run(valid=True, sender=simulated_phase2_voting_contract.address)

        scenario.p("7. Check expected callbacks are called")
        scenario.verify(simulated_poll_leader_contract.data.end_callback_called_times == 1)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_id == 0)
        scenario.verify(simulated_poll_leader_contract.data.end_callback_voting_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)

        scenario.p("8. Check outcome of this contract")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        scenario.verify(c1.data.vote_state == DAO.NONE)

        scenario.p("9. Start a new poll")
        c1.start(5233).run(valid=True, sender=simulated_poll_leader_contract.address)

        scenario.p("10. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks + sp.level
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(27), address=alice.address, vote_value=DAO.VoteValue.NAY,
                                               vote_id=sp.nat(1))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address,
                                                level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(38), address=bob.address, vote_value=DAO.VoteValue.NAY,
                                             vote_id=sp.nat(1))
        c1.vote(bob_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address,
                                              level=start_block)

        scenario.p("11. Let's close now")
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("12. Check vote results is added to history")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        scenario.verify(c1.data.outcomes[1].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("4. The majority voting contract will call the propose_callback. Let's simulate this call.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.data.vote_state == DAO.PHASE_2_MAJORITY)

        scenario.p("5. end_callback cann only be called in state ENDING_PHASE_2.")
        params_end_callback = sp.record(voting_id=sp.nat(1), voting_outcome=DAO.PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(params_end_callback).run(valid=False, sender=simulated_phase2_voting_contract.address)

        scenario.p("6. Simulate end of phase with successful outcome")
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.data.vote_state == DAO.ENDING_PHASE_2)

        scenario.p("7. In return the majority contract will call back this contract to give the result. Let's simulate this.")
        c1.end_callback(params_end_callback).run(valid=True, sender=simulated_phase2_voting_contract.address)

        scenario.p("8. Check outcome of this contract")
        scenario.verify(c1.data.outcomes.contains(0))
        scenario.verify(c1.data.outcomes[0].poll_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
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
        scenario.verify(c1.data.vote_state == DAO.NONE)

def unit_test_offchain_views(is_default = True):
    @sp.add_test(name="unit_test_offchain_views", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_offchain_views")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, simulated_poll_leader_contract, simulated_phase2_voting_contract = TestHelper.create_contracts(scenario, admin)

        scenario.h2("Test all the offchain views.")

        scenario.p("1. Register poll_leader and phase2 contracts")
        scenario.verify(c1.get_contract_state() == DAO.NONE)
        c1.set_poll_leader(simulated_poll_leader_contract.address).run(valid=True, sender=admin)
        c1.set_phase_2_contract(simulated_phase2_voting_contract.address).run(valid=True, sender=admin)

        scenario.p("2. Start poll")
        c1.start(100).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == DAO.PHASE_1_OPT_OUT)

        scenario.p("3. Send votes")
        start_block = c1.data.governance_parameters.vote_delay_blocks
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(7), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        bob_vote_param_valid_nay = sp.record(votes=sp.nat(2), address=bob.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(0))
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
        scenario.verify(c1.get_contract_state() == DAO.PHASE_1_OPT_OUT)
        scenario.verify(c1.get_number_of_historical_outcomes() == 0)
        c1.end(0).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)
        scenario.verify(c1.get_contract_state() == DAO.NONE)

        scenario.p("7. Poll is closed")
        scenario.verify(c1.data.vote_state == DAO.NONE)
        scenario.verify(~c1.data.poll_descriptor.is_some())

        scenario.p("8. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 1)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        alice_vote_param_valid_nay = sp.record(votes=sp.nat(10), address=alice.address, vote_value=DAO.VoteValue.NAY, vote_id=sp.nat(1))
        c1.vote(alice_vote_param_valid_nay).run(valid=True, sender=simulated_poll_leader_contract.address, level=start_block)
        end_block = sp.level + c1.data.governance_parameters.vote_length_blocks
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address, level=end_block + 1)

        scenario.p("10. The majority voting contract will call the propose_callback. Let's simulate this call.")
        snapshot_block = sp.level + 10
        param_propose_callback_3 = sp.record(id=1, snapshot_block=snapshot_block)
        c1.propose_callback(param_propose_callback_3).run(valid=True, sender=simulated_phase2_voting_contract.address)
        scenario.verify(c1.get_contract_state() == DAO.PHASE_2_MAJORITY)

        scenario.p("11. Simulate end of phase with successful outcome")
        c1.end(1).run(valid=True, sender=simulated_poll_leader_contract.address)
        scenario.verify(c1.get_contract_state() == DAO.ENDING_PHASE_2)

        scenario.p("12. In return the majority contract will call back this contract to give the result. Let's simulate this.")
        params_end_callback = sp.record(voting_id=sp.nat(1), voting_outcome=DAO.PollOutcome.POLL_OUTCOME_FAILED)
        c1.end_callback(params_end_callback).run(valid=True, sender=simulated_phase2_voting_contract.address)

        scenario.p("13. Check get_number_of_historical_outcomes and get_historical_outcome_data function")
        scenario.verify(c1.get_number_of_historical_outcomes() == 2)
        outcome_0 = c1.get_historical_outcome_data(0)
        scenario.verify(outcome_0.poll_outcome == DAO.PollOutcome.POLL_OUTCOME_PASSED)
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
        scenario.verify(outcome_1.poll_outcome == DAO.PollOutcome.POLL_OUTCOME_FAILED)
        scenario.verify(outcome_1.poll_data.phase_1_vote_objection == 10)
        scenario.verify(outcome_1.poll_data.total_voters == 100)
        scenario.verify(outcome_1.poll_data.vote_id == 1)
        scenario.verify(outcome_1.poll_data.phase_1_objection_threshold == 10)
        scenario.verify(outcome_1.poll_data.phase_2_needed == sp.bool(True))
        scenario.verify(outcome_1.poll_data.phase_2_vote_id == 1)
        scenario.verify(sp.len(outcome_1.poll_data.phase_1_voters) == 1)
        scenario.verify(c1.get_contract_state() == DAO.NONE)


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
