import smartpy as sp

Sale = sp.io.import_script_from_url("file:./sale/sale.py")
NFT = sp.io.import_script_from_url("file:./nft/nft.py")

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
    class FundReceiverAccount(sp.Contract):
        def __init__(self):
            self.init()

    class SimulatedPreSaleContract(sp.Contract):
        def __init__(self):
            self.init(
                tokens = sp.map(l={0: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU01"),
                                        1: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU02"),
                                        2: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU03"),
                                        3: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU04"),
                                        4: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU05"),
                                        5: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU06"),
                                        6: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU07"),
                                        7: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU08"),
                                        8: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU09"),
                                        9: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU010"),
                                        10: sp.address("tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHU11")}, tkey=sp.TNat, tvalue=sp.TAddress),
                burned_tokens = sp.set(l={}, t=sp.TNat)
                    )

        @sp.entry_point
        def burn(self, params):
            sp.for token in params:
                sp.verify(self.data.tokens.contains(token))
                self.data.burned_tokens.add(token)

        @sp.onchain_view(pure=True)
        def all_tokens(self):
            sp.result(sp.list(l={0,1,2,3,4,5,6,7,8,9,10}, t=sp.TNat))

        @sp.onchain_view(pure=True)
        def get_token_owner(self, token):
            sp.verify(self.data.tokens.contains(token))
            sp.result(self.data.tokens[token])

        @sp.onchain_view(pure=True)
        def is_token_burned(self, token):
            sp.result(self.data.burned_tokens.contains(token))


    def create_scenario(name):
        scenario = sp.test_scenario()
        scenario.h1(name)
        scenario.table_of_contents()
        return scenario

    def create_contracts(scenario, admin, john, with_balance=False):
        c1 = Sale.AngryTeenagersSale(admin.address, admin.address, sp.utils.metadata_of_url("https://example.com"))
        if with_balance:
            c1.set_initial_balance(sp.mutez(300000000))
        scenario += c1

        simulated_presale_contract = TestHelper.SimulatedPreSaleContract()
        scenario += simulated_presale_contract

        ARTIFACT_FILE_TYPE = '"image/png"'
        ARTIFACT_FILE_SIZE = '425118'
        ARTIFACT_FILE_NAME = '"angry_teenagers.png"'
        ARTIFACT_DIMENSIONS = '"1000x1000"'
        ARTIFACT_FILE_UNIT = '"px"'
        DISPLAY_FILE_TYPE = '"image/jpeg"'
        DISPLAY_FILE_SIZE = '143913'
        DISPLAY_FILE_NAME = '"angry_teenagers_display.jpeg"'
        DISPLAY_DIMENSIONS = '"1000x1000"'
        DISPLAY_FILE_UNIT = '"px"'
        THUMBNAIL_FILE_TYPE = '"image/jpeg"'
        THUMBNAIL_FILE_SIZE = '26875'
        THUMBNAIL_FILE_NAME = '"angry_teenagers_thumbnail.jpeg"'
        THUMBNAIL_DIMENSIONS = '"350x350"'
        THUMBNAIL_FILE_UNIT = '"px"'

        NAME_PREFIX = '"Angry Teenager #'
        SYMBOL = "ANGRY"
        DESCRIPTION = '"Angry Teenagers: NFTs that fund an exponential cycle of reforestation."'
        LANGUAGE = "en-US"
        ATTRIBUTES_GENERIC = '[{\"name\"}, {\"generic\"}]'
        RIGHTS = '"© 2022 EcoMint. All rights reserved."'
        CREATORS = '["The Angry Teenagers. https://www.angryteenagers.xyz"]'
        PROJECTNAME = "Nsomyam Ye Reforestation"

        MAX_SIZE_OF_VOTING_POWER_LIST = 5000
        REMAINING_ELEMS_IN_VOTING_POWER_AFTER_CLEANUP = 100

        c2  = NFT.AngryTeenagers(administrator=admin.address,
                                   royalties_bytes=sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'),
                                   metadata=sp.utils.metadata_of_url("https://example.com"),
                                   generic_image_ipfs=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                                   generic_image_ipfs_display=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                                   generic_image_ipfs_thumbnail=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                                   what3words_file_ipfs=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"),
                                   max_supply=5236,
                                   artifact_file_type=ARTIFACT_FILE_TYPE,
                                   artifact_file_size_generic=ARTIFACT_FILE_SIZE,
                                   artifact_file_name=ARTIFACT_FILE_NAME,
                                   artifact_dimensions=ARTIFACT_DIMENSIONS,
                                   artifact_file_unit=ARTIFACT_FILE_UNIT,
                                   display_file_type=DISPLAY_FILE_TYPE,
                                   display_file_size_generic=DISPLAY_FILE_SIZE,
                                   display_file_name=DISPLAY_FILE_NAME,
                                   display_dimensions=DISPLAY_DIMENSIONS,
                                   display_file_unit=DISPLAY_FILE_UNIT,
                                   thumbnail_file_type=THUMBNAIL_FILE_TYPE,
                                   thumbnail_file_size_generic=THUMBNAIL_FILE_SIZE,
                                   thumbnail_file_name=THUMBNAIL_FILE_NAME,
                                   thumbnail_dimensions=THUMBNAIL_DIMENSIONS,
                                   thumbnail_file_unit=THUMBNAIL_FILE_UNIT,
                                   name_prefix=NAME_PREFIX,
                                   symbol=SYMBOL,
                                   description=DESCRIPTION,
                                   language=LANGUAGE,
                                   attributes_generic=ATTRIBUTES_GENERIC,
                                   rights=RIGHTS,
                                   creators=CREATORS,
                                   project_name=PROJECTNAME)
        scenario += c2
        c1.register_fa2(c2.address).run(valid=True, sender=admin)
        c2.set_next_administrator(c1.address).run(valid=True, sender=admin)
        c2.validate_new_administrator().run(valid=True, sender=c1.address)

        scenario.h2("Contracts:")
        scenario.p("c1: This sale contract to test")
        scenario.p("c2: The underlying FA2 contract (tested in ./contracts/nft/angry_teenagers_nft.py)")

        return c1, c2, simulated_presale_contract

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

    def check_fa2_ledger(scenario, contract, owner, token_id_min, token_id_max):
        for x in range(token_id_min, token_id_max):
            scenario.verify(contract.data.ledger.contains(x))

# Unit tests -------------------------------------------------------------------------------------------------------
########################################################################################################################
# unit_test_initial_storage
########################################################################################################################
def unit_test_initial_storage(is_default = True):
    @sp.add_test(name="unit_test_initial_storage", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_initial_storage")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the storage is initialized as expected.")

        scenario.p("1. Read each entry of the storage of the c1 contract and check it is initialized as expected")
        scenario.verify(c1.data.administrator == admin.address)
        scenario.verify(c1.data.next_administrator == sp.none)
        scenario.verify(c1.data.fa2 == c2.address)
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        scenario.verify(sp.len(c1.data.pre_allowlist) == 0)

        scenario.verify(c1.data.event_price == sp.mutez(0))
        scenario.verify(c1.data.event_max_supply == sp.nat(0))
        scenario.verify(c1.data.event_max_per_user == sp.nat(0))

        scenario.verify(c1.data.public_allowlist_max_space == sp.nat(0))
        scenario.verify(c1.data.public_allowlist_space_taken == sp.nat(0))
        scenario.verify(c1.data.public_sale_allowlist_config == sp.record(used=sp.bool(False), discount=sp.mutez(0),
                                                 minting_rights=sp.bool(False)))

        scenario.verify(c1.data.token_minted_in_event == sp.nat(0))
        scenario.verify(c1.data.multisig_fund_address == admin.address)

########################################################################################################################
# unit_test_admin_fill_allowlist
########################################################################################################################
def unit_test_admin_fill_allowlist(is_default = True):
    @sp.add_test(name="unit_test_admin_fill_allowlist", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_admin_fill_allowlist")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint used to fill the allowlist. (Who: Only for admin)")
        scenario.p("1. Verify the state of the contract is as expected (see state machine at the top of this file)")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Verify the allowlist and the pre-allowlist are both empty")
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        scenario.verify(sp.len(c1.data.pre_allowlist) == 0)


        scenario.p("3. Verify that only the admin can fill the allowlist")
        # Only admin can call the function
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=False, sender=bob)
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=False, sender=alice)
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=False, sender=john)

        scenario.p("4. Add 2 entries into the allowlist successfully and verify that:")
        scenario.p("4.1. State of the contract hasn't change")
        scenario.p("4.2. Allowlist length has changed accordingly")
        scenario.p("4.3. Both entries are in the allowlist")
        scenario.p("4.4. Pre-allowlist has not changed (another entrypoint is used for that)")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))
        scenario.verify(sp.len(c1.data.pre_allowlist) == 0)

        scenario.p("5. Add another entry successfully to the allowlist and make the same verification than in step 5")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, john.address], t=sp.TAddress)).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.allowlist) == 3)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))
        scenario.verify(c1.data.allowlist.contains(john.address))

        scenario.p("6. Check the offchain view get_mint_token_available returns the expected value")
        scenario.verify(c1.get_mint_token_available(admin.address) == 0)

########################################################################################################################
# unit_test_admin_fill_pre_allowlist
########################################################################################################################
def unit_test_admin_fill_pre_allowlist(is_default = True):
    @sp.add_test(name="unit_test_admin_fill_pre_allowlist", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_admin_fill_pre_allowlist")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint used to fill the pre-allowlist (Who: Only for admin).")

        scenario.p("1. Verify the state of the contract is as expected (see state machine at the top of this file)")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Verify the allowlist and the pre-allowlist are both empty")
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        scenario.verify(sp.len(c1.data.pre_allowlist) == 0)

        scenario.p("3. Verify that only the admin can fill the pre-allowlist")
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=False, sender=bob)
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=False, sender=alice)
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=False, sender=john)

        scenario.p("4. Add 2 entries into the pre-allowlist successfully and verify that:")
        scenario.p("4.1. State of the contract hasn't change")
        scenario.p("4.2. Pre-allowlist length has changed accordingly")
        scenario.p("4.3. Both entries are in the pre-allowlist")
        scenario.p("4.4. Allowlist has not changed (another entrypoint is used for that)")
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.pre_allowlist) == 2)
        scenario.verify(c1.data.pre_allowlist.contains(alice.address))
        scenario.verify(c1.data.pre_allowlist.contains(bob.address))
        scenario.verify(sp.len(c1.data.allowlist) == 0)

        scenario.p("5. Add another entry successfully to the pre-allowlist and make the same verification than in step 5")
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, john.address], t=sp.TAddress)).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.pre_allowlist) == 3)
        scenario.verify(c1.data.pre_allowlist.contains(alice.address))
        scenario.verify(c1.data.pre_allowlist.contains(bob.address))
        scenario.verify(c1.data.pre_allowlist.contains(john.address))

########################################################################################################################
# unit_test_open_event_priv_allowlist_reg
########################################################################################################################
def unit_test_open_event_priv_allowlist_reg(is_default = True):
    @sp.add_test(name="unit_test_open_event_priv_allowlist_reg", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_open_event_priv_allowlist_reg")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_event_priv_allowlist_reg entrypoint. (Who: Only for admin).")
        scenario.p("This entrypoint opens an event where users in the pre-allowlist can register to the allowlist. The amount of XTZ to pay to enter to register to given as a parameter to this entrypoint.")

        scenario.p("1. Verify the state of the contract is as expected (see state machine at the top of this file)")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p(
            "2. Try to call the entrypoint with non-admin users. Verify it fails and the state of the contract stays unchanged.")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10))).run(valid=False, sender=bob)
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10))).run(valid=False, sender=alice)
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10))).run(valid=False, sender=john)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("3. Open successfully the event with the admin. Check the state of the contract is as expected.")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(c1.data.event_price == sp.tez(10))

        scenario.p("4. Check event can be closed and then the state of the contract returns to the expected state.")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2))
        scenario.verify(c1.data.event_price == sp.tez(0))

########################################################################################################################
# unit_test_pay_to_enter_allowlist_priv
########################################################################################################################
def unit_test_pay_to_enter_allowlist_priv(is_default = True):
    @sp.add_test(name="unit_test_pay_to_enter_allowlist_priv", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_pay_to_enter_allowlist_priv")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the pay_to_enter_allowlist_priv entrypoint. (Who: Only for the users in the pre-allowlist).")
        scenario.p("Users in the pre-allowlist can call this entrypoint and pay the configured XTZ price to register into the allowlist.")

        scenario.p("1. Fill the pre-allowlist")
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Verify the state of the contract")
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10))).run(valid=True, sender=admin)

        scenario.p("3. Open the event to register into the allowlist for users in the pre-allowlist")
        scenario.p("4. Verify that:")
        scenario.p("4.1. Only users that pay the right amount of XTZ can register to the allowlist")
        scenario.p("4.2. Only users that are on the pre-allowlist can register into the allowlist")
        scenario.p("4.3. When users in the pre-allowlist pays the expected price, they are registered in the allowlist")
        c1.pay_to_enter_allowlist_priv().run(valid=False, sender=alice)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(5), sender=alice)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        c1.pay_to_enter_allowlist_priv().run(valid=True, amount=sp.tez(10), sender=alice)
        c1.pay_to_enter_allowlist_priv().run(valid=True, amount=sp.tez(10), sender=bob)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(10), sender=john)
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(10), sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))

########################################################################################################################
# unit_test_open_event_pub_allowlist_reg
########################################################################################################################
def unit_test_open_event_pub_allowlist_reg(is_default = True):
    @sp.add_test(name="unit_test_open_event_pub_allowlist_reg", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_open_event_pub_allowlist_reg")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_event_pub_allowlist_reg entrypoint. (Who: Only for the admin).")
        scenario.p("This entrypoint is used to open an event where any users can take a space in the allowlist by paying a price in XTZ (parameters to this entrypoint) as long as space are remaining. One user gets one spot max.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check only the admin can open this event")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10, price=sp.tez(10))).run(
            valid=False, sender=bob)
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10, price=sp.tez(10))).run(
            valid=False, sender=alice)
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10, price=sp.tez(10))).run(
            valid=False, sender=john)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("3. Check this entrypoint fails if the number of space allowed is 0")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=0, price=sp.tez(10))).run(
            valid=False, sender=admin)

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10,price=sp.tez(10))).run(
            valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PUB_ALLOWLIST_REG_3))
        scenario.verify(c1.data.public_allowlist_max_space == 10)
        scenario.verify(c1.data.public_allowlist_space_taken == 0)
        scenario.verify(c1.data.event_price == sp.tez(10))

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.public_allowlist_max_space == 0)
        scenario.verify(c1.data.public_allowlist_space_taken == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))

########################################################################################################################
# unit_test_pay_to_enter_allowlist_pub
########################################################################################################################
def unit_test_pay_to_enter_allowlist_pub(is_default = True):
    @sp.add_test(name="unit_test_pay_to_enter_allowlist_pub", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_pay_to_enter_allowlist_pub")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the pay_to_enter_allowlist_pub entrypoint. (Who: For all users).")
        scenario.p("This entrypoint is used by any users to register in the allowlist when the associated event (public allowlist registration) is used by paying the configured XTZ price. Users have only one spot in the allowlist.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Open the public allowlist registration event")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=2,price=sp.tez(10))).run(
            valid=True, sender=admin)

        scenario.p("3. Check the state of the contract is as expected")
        scenario.verify(c1.data.public_allowlist_max_space == 2)

        scenario.p("4. Check no space are taken yet in the allowlist")
        scenario.verify(c1.data.public_allowlist_space_taken == 0)

        scenario.p("5. Check users can ony register if they pay the XTZ fee")
        c1.pay_to_enter_allowlist_pub().run(valid=False, sender=alice)
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(5), sender=alice)
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        c1.pay_to_enter_allowlist_pub().run(valid=True, amount=sp.tez(10), sender=alice)

        scenario.p("6. Check users cannot call this entrypoint is they already register to the allowlist")

        scenario.p("7. Get users registering successfully to the allowlist and:")
        scenario.p("7.1. Check the space taken in the allowlist is as expected")
        scenario.p("7.2. Check the allowlist length")
        scenario.p("7.3. Check the allowlist contains the registered users")
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(10), sender=alice)
        scenario.verify(sp.len(c1.data.allowlist) == 1)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.public_allowlist_space_taken == 1)
        scenario.verify(c1.data.public_allowlist_max_space == 2)

        c1.pay_to_enter_allowlist_pub().run(valid=True, amount=sp.tez(10), sender=bob)
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))

        scenario.p("8. Check event closes automatically when all spaces are taken")
        scenario.p("9. Check users cannot register anymore when event is closed")
        scenario.p("10. Check allowlist is preserved after event is closed")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.public_allowlist_max_space == 0)
        scenario.verify(c1.data.public_allowlist_space_taken == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))

        # Only 2 spots
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(10), sender=john)
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))
        scenario.verify(c1.data.public_allowlist_space_taken == 0)
        scenario.verify(c1.data.public_allowlist_max_space == 0)
        # Allowlist is not erased
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))

########################################################################################################################
# unit_test_open_pre_sale
########################################################################################################################
def unit_test_open_pre_sale(is_default = True):
    @sp.add_test(name="unit_test_open_pre_sale", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_open_pre_sale")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_pre_sale entrypoint. (Who: Only for the admin)")
        scenario.p("This entrypoint is used by the admin to open a pre-sale event. During a pre-sale, only users in the allowlist can mint tokens.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check that only admin can open a pre-sale")
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10))).run(valid=False, sender=bob)
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10))).run(valid=False, sender=alice)

        scenario.p("3. Check pre-sale can only be opened with consistent parameters")
        c1.open_pre_sale(sp.record(max_supply=0, max_per_user=2, price=sp.tez(10))).run(valid=False, sender=admin)
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=0, price=sp.tez(10))).run(valid=False, sender=admin)
        c1.open_pre_sale(sp.record(max_supply=2, max_per_user=6, price=sp.tez(10))).run(valid=False, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PRESALE_5))
        scenario.verify(c1.data.event_max_supply == 6)
        scenario.verify(c1.data.event_max_per_user == 2)
        scenario.verify(c1.data.event_price == sp.tez(10))

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.event_max_supply == 0)
        scenario.verify(c1.data.event_max_per_user == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))

########################################################################################################################
# unit_test_open_pub_sale
########################################################################################################################
def unit_test_open_pub_sale(is_default = True):
    @sp.add_test(name="unit_test_open_pub_sale", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_open_pub_sale")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_pub_sale entrypoint. (Who: Only for the admin)")
        scenario.p("This entrypoint is used by the admin to open a public-sale event without the use of the allowlist.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check that only admin can open a public-sale")
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10))).run(valid=False, sender=bob)
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10))).run(valid=False, sender=alice)

        scenario.p("3. Check public-sale can only be opened with consistent parameters")
        c1.open_pub_sale(sp.record(max_supply=0, max_per_user=2, price=sp.tez(10))).run(valid=False, sender=admin)
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=0, price=sp.tez(10))).run(valid=False, sender=admin)
        c1.open_pub_sale(sp.record(max_supply=2, max_per_user=6, price=sp.tez(10))).run(valid=False, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PUBLIC_SALE_6))
        scenario.verify(c1.data.event_max_supply == 6)
        scenario.verify(c1.data.event_max_per_user == 2)
        scenario.verify(c1.data.event_price == sp.tez(10))
        scenario.verify(c1.data.public_sale_allowlist_config.used == False)
        scenario.verify(c1.data.public_sale_allowlist_config.discount == sp.tez(0))
        scenario.verify(c1.data.public_sale_allowlist_config.minting_rights == False)

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.event_max_supply == 0)
        scenario.verify(c1.data.event_max_per_user == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))

########################################################################################################################
# unit_test_open_pub_sale_with_allowlist
########################################################################################################################
def unit_test_open_pub_sale_with_allowlist(is_default = True):
    @sp.add_test(name="unit_test_open_pub_sale_with_allowlist", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_open_pub_sale_with_allowlist")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_pub_sale_with_allowlist entrypoint. (Who: Only for the admin)")
        scenario.p("This entrypoint is used by the admin to open a public-sale event with an allowlist.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check that only admin can open a public-sale with allowlist")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=bob)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=alice)

        scenario.p("3. Check public-sale with allowlist can only be opened with consistent parameters")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=0,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=admin)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=0,
                                                           price=sp.tez(10),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=admin)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=2,
                                                           max_per_user=6,
                                                           price=sp.tez(10),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=admin)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=2,
                                                           max_per_user=6,
                                                           price=sp.tez(10),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(11))).run(valid=False, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_OPEN_0))

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           mint_right=True,
                                                           mint_discount=sp.tez(5))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_EVENT_PUBLIC_SALE_6))
        scenario.verify(c1.data.event_max_supply == 6)
        scenario.verify(c1.data.event_max_per_user == 2)
        scenario.verify(c1.data.event_price == sp.tez(10))
        scenario.verify(c1.data.public_sale_allowlist_config.used == True)
        scenario.verify(c1.data.public_sale_allowlist_config.discount == sp.tez(5))
        scenario.verify(c1.data.public_sale_allowlist_config.minting_rights == True)

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(Sale.STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.event_max_supply == 0)
        scenario.verify(c1.data.event_max_per_user == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))
        scenario.verify(c1.data.public_sale_allowlist_config.used == False)
        scenario.verify(c1.data.public_sale_allowlist_config.discount == sp.tez(0))
        scenario.verify(c1.data.public_sale_allowlist_config.minting_rights == False)

########################################################################################################################
# unit_test_mint_and_give
########################################################################################################################
def unit_test_mint_and_give(is_default=True):
    @sp.add_test(name="unit_test_mint_and_give", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mint_and_give")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the mint_and_give entrypoint. (Who: Only for the admin)")
        scenario.p("This function is used by the admin to mint and give tokens when no sales event are opened.")

        scenario.p("1. Check only admin can call this entrypoint")
        c1.mint_and_give(sp.record(amount=1, address=bob.address)).run(valid=False, sender=alice)
        c1.mint_and_give(sp.record(amount=2, address=bob.address)).run(valid=True, sender=admin)

        scenario.p("2. Open a public safe")
        c1.open_pub_sale(sp.record(max_supply=100,
                                                           max_per_user=80,
                                                           price=sp.tez(10))).run(valid=True, sender=admin)

        scenario.p("3. Check this entrypoint cannot be called when a sale is opened")
        c1.mint_and_give(sp.record(amount=2, address=bob.address)).run(valid=False, sender=admin)
        c1.user_mint(sp.record(amount=80, address=alice.address)).run(valid=True, amount=sp.mutez(800000000), sender=alice)

        scenario.p("4. Close the open public sale")
        c1.close_any_open_event().run(valid=True, sender=admin)

        scenario.p("5. Mint and give successfully")
        c1.mint_and_give(sp.record(amount=2, address=john.address)).run(valid=True, sender=admin)
        c1.mint_and_give(sp.record(amount=6, address=bob.address)).run(valid=True, sender=admin)

        scenario.p("6. Check the ledger of the FA2 contract")
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=0, token_id_max=2)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=2, token_id_max=82)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=john.address, token_id_min=82, token_id_max=84)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=84, token_id_max=90)

########################################################################################################################
# unit_test_set_next_administrator
########################################################################################################################
def unit_test_set_next_administrator(is_default = True):
    @sp.add_test(name="unit_test_set_next_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_next_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the set_next_administrator entrypoint. (Who: Only for the admin)")
        scenario.p("This function is used to change the administrator of the contract. This is two steps process. validate_next_admin shall be called after.")

        scenario.p("1. Check only admin can call this entrypoint (i.e only the current admin can change the admin)")
        c1.set_next_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_next_administrator(admin.address).run(valid=False, sender=bob)
        c1.set_next_administrator(bob.address).run(valid=False, sender=john)

        scenario.p("2. Check this function does not change the admin but only the next_admin field.")
        c1.set_next_administrator(alice.address).run(valid=True, sender=admin)
        scenario.verify(c1.data.administrator == admin.address)
        scenario.verify(c1.data.next_administrator.open_some() == alice.address)

        scenario.p("3. This function can be called several times but only by the admin.")
        c1.set_next_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_next_administrator(admin.address).run(valid=False, sender=bob)
        c1.set_next_administrator(bob.address).run(valid=False, sender=john)
        c1.set_next_administrator(bob.address).run(valid=True, sender=admin)
        scenario.verify(c1.data.administrator == admin.address)
        scenario.verify(c1.data.next_administrator.open_some() == bob.address)

########################################################################################################################
# unit_test_validate_new_administrator
########################################################################################################################
def unit_test_validate_new_administrator(is_default = True):
    @sp.add_test(name="unit_test_validate_new_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_validate_new_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

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
        scenario.verify(c1.data.administrator == alice.address)
        scenario.verify(~c1.data.next_administrator.is_some())

        scenario.p("3. Alice is now admin. She can give the admin right to bob")
        c1.set_next_administrator(bob.address).run(valid=False, sender=bob)
        c1.set_next_administrator(bob.address).run(valid=False, sender=admin)
        c1.set_next_administrator(bob.address).run(valid=True, sender=alice)
        c1.validate_new_administrator().run(valid=False, sender=admin)
        c1.validate_new_administrator().run(valid=False, sender=alice)
        c1.validate_new_administrator().run(valid=True, sender=bob)
        scenario.verify(c1.data.administrator == bob.address)
        scenario.verify(~c1.data.next_administrator.is_some())

########################################################################################################################
# unit_test_set_multisig_fund_address
########################################################################################################################
def unit_test_set_multisig_fund_address(is_default=True):
    @sp.add_test(name="unit_test_set_multisig_fund_address", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_multisig_fund_address")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the set_multisig_fund_address entrypoint. (Who: Only for the admin)")
        scenario.p("The multisig_fund address is used to redirect the fund received when a user mints a NFTs to wallet.")

        scenario.p("1. Check that only the admin can call this entrypoint")
        correct_param = alice.address
        c1.set_multisig_fund_address(correct_param).run(valid=False, sender=john)
        c1.set_multisig_fund_address(correct_param).run(valid=False, sender=bob)
        c1.set_multisig_fund_address(correct_param).run(valid=False, sender=alice)

        scenario.p("2. Change successfully the transfer address to Alice account and verify the storage is updated accordingly")
        c1.set_multisig_fund_address(correct_param).run(valid=True, sender=admin)
        scenario.verify(c1.data.multisig_fund_address == alice.address)

########################################################################################################################
# unit_test_register_fa2
########################################################################################################################
def unit_test_register_fa2(is_default=True):
    @sp.add_test(name="unit_test_register_fa2", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_register_fa2")

        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the register_fa2 entrypoint. (Who: Only for the admin)")
        scenario.p("This function is used to register the underlying FA2 contract.")

        scenario.p("1. Check initial storage")
        scenario.verify(c1.data.fa2 == c2.address)

        scenario.p("2. Check only admin can call this entrypoint")
        c1.register_fa2(sp.address('tz10admin')).run(valid=False, sender=gabe)
        c1.register_fa2(sp.address('tz10alice')).run(valid=False, sender=bob)
        c1.register_fa2(sp.address('tz10alice')).run(valid=False, sender=alice)

        scenario.p("3. Check registered FA2 contract is as expected after a change")
        c1.register_fa2(sp.address('tz10bob')).run(valid=True, sender=admin)
        scenario.verify(c1.data.fa2 == sp.address('tz10bob'))
        c1.register_fa2(sp.address('tz10fund')).run(valid=True, sender=admin)
        scenario.verify(c1.data.fa2 == sp.address('tz10fund'))

########################################################################################################################
# unit_test_user_mint_during_public_sale
########################################################################################################################
def unit_test_user_mint_during_public_sale(is_default=True):
    @sp.add_test(name="unit_test_user_mint_during_public_sale", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_user_mint_during_public_sale")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_public_sale entrypoint. (Who: for all users)")
        scenario.p("This entrypoint is called by users to mint NFTs when a public sale is opened.")

        scenario.p("1. Check users cannot mint when event is not opened")
        c1.user_mint(sp.record(amount=8, address=alice.address)).run(valid=False, sender=alice)

        scenario.p("2. Start a public sale event without allowlist with a max supply of NFTs to mint and max NFTs to mint per user")
        c1.open_pub_sale(sp.record(max_supply=50,
                                            max_per_user=23,
                                            price=sp.tez(10))).run(valid=True, sender=admin)

        scenario.p("3. Verify a users cannot mint more than allowed")
        c1.user_mint(sp.record(amount=24, address=alice.address)).run(valid=False, amount=sp.tez(240), sender=alice)

        scenario.p("4. Verify a user cannot mint 0 NFT")
        c1.user_mint(sp.record(amount=0, address=alice.address)).run(valid=False, amount=sp.tez(10), sender=alice)

        scenario.p("5. Verify a user cannot mint if he doesn't provide the right amount of XTZ")
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(0), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(100000), sender=admin)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(99999999), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(2123456), sender=john)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(5555), sender=bob)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(100000001), sender=alice)

        scenario.p("7. Mint some NFTs")
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=True, amount=sp.tez(100), sender=alice)
        scenario.verify(c1.balance == sp.mutez(0))
        c1.user_mint(sp.record(amount=5, address=john.address)).run(valid=True, amount=sp.tez(50), sender=john)
        scenario.verify(c1.balance == sp.mutez(0))
        c1.user_mint(sp.record(amount=3, address=admin.address)).run(valid=True, amount=sp.tez(30), sender=admin)
        scenario.verify(c1.balance == sp.tez(0))
        c1.user_mint(sp.record(amount=1, address=bob.address)).run(valid=True, amount=sp.tez(10), sender=bob)
        scenario.verify(c1.balance == sp.tez(0))
        # Only 31 token remaining in the current sale
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=True, amount=sp.tez(100), sender=alice)
        c1.user_mint(sp.record(amount=15, address=bob.address)).run(valid=True, amount=sp.tez(150), sender=bob)
        c1.user_mint(sp.record(amount=5, address=bob.address)).run(valid=True, amount=sp.tez(50), sender=bob)
        c1.user_mint(sp.record(amount=2, address=alice.address)).run(valid=False, amount=sp.tez(20), sender=alice)

        scenario.p("7. Verify users cannot mint more than total allocated supply")
        c1.user_mint(sp.record(amount=2, address=alice.address)).run(valid=False, amount=sp.tez(20), sender=alice)
        c1.user_mint(sp.record(amount=24, address=john.address)).run(valid=False, amount=sp.tez(240), sender=john)

        scenario.p("8. One is still mintable. Mint it.")
        c1.user_mint(sp.record(amount=1, address=alice.address)).run(valid=True, amount=sp.tez(10), sender=alice)

        scenario.p("9. Verify the FA2 ledger contains the expected NFTs")
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=0, token_id_max=10)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=john.address, token_id_min=10, token_id_max=15)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=admin.address, token_id_min=15, token_id_max=18)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=18, token_id_max=19)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=19, token_id_max=29)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=29, token_id_max=49)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=49,token_id_max=50)

########################################################################################################################
# unit_test_user_mint_during_pre_sale
########################################################################################################################
def unit_test_user_mint_during_pre_sale(is_default=True):
    @sp.add_test(name="unit_test_user_mint_during_pre_sale", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_user_mint_during_pre_sale")

        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_pre_sale entrypoint.  (Who: for all users in the allowlist)")
        scenario.p("This entrypoint is called by users to mint NFTs when a pre-sale is opened. to mint during pre-sale, a user needs to be registered in the allowlist.")

        scenario.p("1. Fill the allowlist")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address, john.address, admin.address], t=sp.TAddress)).\
            run(valid=True, sender=admin)

        scenario.p("2. Verify this entrypoint cannot be called when the associated event is not opened")
        c1.user_mint(sp.record(amount=8, address=alice.address)).run(valid=False, sender=alice)

        scenario.p("3. Start the pre-sale event")
        c1.open_pre_sale(sp.record(max_supply=50, max_per_user=23, price=sp.tez(10))).run(valid=True,
                                                                                                          sender=admin)

        scenario.p("4. Verify users cannot mint more than the number of defined NFT per users")
        c1.user_mint(sp.record(amount=24, address=alice.address)).run(valid=False, amount=sp.tez(240), sender=alice)

        scenario.p("5. Verify cannot mint if not in the allowlist")
        c1.user_mint(sp.record(amount=10, address=gabe.address)).run(valid=False, amount=sp.tez(100), sender=gabe)

        scenario.p("6. Verify user cannot mint 0 NFT")
        c1.user_mint(sp.record(amount=0, address=alice.address)).run(valid=False, amount=sp.tez(10), sender=alice)

        scenario.p("7. Verify user cannot mint if he does not provide the expected amount of XTZ")
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(0), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(100000), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(99999999), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(2123456), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(5555), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(100000001), sender=alice)

        scenario.p("8. Mint some NFTs")
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=True, amount=sp.tez(100), sender=alice)
        # Mint some more
        c1.user_mint(sp.record(amount=5, address=john.address)).run(valid=True, amount=sp.tez(50), sender=john)
        scenario.verify(c1.balance == sp.mutez(0))
        # And again
        c1.user_mint(sp.record(amount=3, address=admin.address)).run(valid=True, amount=sp.tez(30), sender=admin)
        scenario.verify(c1.balance == sp.tez(0))
        c1.user_mint(sp.record(amount=1, address=bob.address)).run(valid=True, amount=sp.tez(10), sender=bob)
        scenario.verify(c1.balance == sp.tez(0))
        # Only 31 token remaining in the current sale
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=True, amount=sp.tez(100), sender=alice)
        c1.user_mint(sp.record(amount=15, address=bob.address)).run(valid=True, amount=sp.tez(150), sender=bob)
        c1.user_mint(sp.record(amount=5, address=bob.address)).run(valid=True, amount=sp.tez(50), sender=bob)
        c1.user_mint(sp.record(amount=2, address=alice.address)).run(valid=False, amount=sp.tez(20), sender=alice)

        scenario.p("8. Verify users cannot mint more than the total allocated supply")
        c1.user_mint(sp.record(amount=2, address=alice.address)).run(valid=False, amount=sp.tez(20), sender=alice)
        c1.user_mint(sp.record(amount=24, address=john.address)).run(valid=False, amount=sp.tez(240), sender=john)

        scenario.p("9. One is still mintable. Mint it.")
        c1.user_mint(sp.record(amount=1, address=alice.address)).run(valid=True, amount=sp.tez(10), sender=alice)

        scenario.p("10. Verify the FA2 ledger contains the expected NFTs")
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=0, token_id_max=10)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=john.address, token_id_min=10, token_id_max=15)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=admin.address, token_id_min=15, token_id_max=18)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=18, token_id_max=19)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=19, token_id_max=29)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=29, token_id_max=49)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=49,token_id_max=50)

########################################################################################################################
# unit_test_user_mint_during_public_sale_with_allowlist_discount
########################################################################################################################
def unit_test_user_mint_during_public_sale_with_allowlist_discount(is_default=True):
    @sp.add_test(name="unit_test_user_mint_during_public_sale_with_allowlist_discount", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_user_mint_during_public_sale_with_allowlist_discount")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_public_sale_with_allowlist_discount entrypoint.  (Who: for all users)")
        scenario.p("This entrypoint is called by users to mint NFTs when a public sale is opened using the allowlist and the associated discount. Any users can miint during the public sale but only the ones in the allowlist will have a discount.")

        scenario.p("1. Fill the allowlist")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Verify users cannot mint if no event are opened")
        c1.user_mint(sp.record(amount=8, address=alice.address)).run(valid=False, amount=sp.tez(80), sender=alice)

        scenario.p("3. Open a public sale with allowlist suing the discount feature")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=50,
                                            max_per_user=23,
                                            price=sp.tez(10),
                                            mint_right=False,
                                            mint_discount=sp.tez(5),
                                            )).run(valid=True, sender=admin)

        scenario.p("4. Verify users cannot mint more than the max numbers per user")
        c1.user_mint(sp.record(amount=24, address=alice.address)).run(valid=False, amount=sp.tez(120), sender=alice)

        scenario.p("5. Verify user cannot mint 0 NFT")
        c1.user_mint(sp.record(amount=0, address=alice.address)).run(valid=False, amount=sp.tez(5), sender=alice)

        scenario.p("6. Verify users can only mint if the they provide the right amount of XTZ")
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(0), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(100000), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(99999999), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(2123456), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(5555), sender=alice)
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=False, amount=sp.mutez(50000001), sender=alice)

        scenario.p("7. Mint some NFTs")
        scenario.p("8. Verify users in the allowlist get a discount")
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=True, amount=sp.tez(50), sender=john)
        # Mint some more
        c1.user_mint(sp.record(amount=5, address=john.address)).run(valid=True, amount=sp.tez(50), sender=john)
        scenario.verify(c1.balance == sp.mutez(0))
        # And again
        c1.user_mint(sp.record(amount=3, address=admin.address)).run(valid=True, amount=sp.tez(30), sender=admin)
        scenario.verify(c1.balance == sp.tez(0))
        c1.user_mint(sp.record(amount=1, address=bob.address)).run(valid=True, amount=sp.tez(5), sender=bob)
        scenario.verify(c1.balance == sp.tez(0))
        # Only 31 token remaining in the current sale
        c1.user_mint(sp.record(amount=10, address=alice.address)).run(valid=True, amount=sp.tez(50), sender=alice)
        c1.user_mint(sp.record(amount=15, address=bob.address)).run(valid=True, amount=sp.tez(75), sender=bob)
        c1.user_mint(sp.record(amount=5, address=bob.address)).run(valid=True, amount=sp.tez(25), sender=bob)
        c1.user_mint(sp.record(amount=2, address=alice.address)).run(valid=False, amount=sp.tez(10), sender=alice)

        scenario.p("9. Verify users cannot mint more than the total allocated supply")
        c1.user_mint(sp.record(amount=2, address=alice.address)).run(valid=False, amount=sp.tez(10), sender=alice)
        c1.user_mint(sp.record(amount=24, address=john.address)).run(valid=False, amount=sp.tez(240), sender=john)

        scenario.p("9. One is still mintable. Mint it.")
        c1.user_mint(sp.record(amount=1, address=alice.address)).run(valid=True, amount=sp.tez(5), sender=alice)

        scenario.p("11. Verify the Fa2 ledger contains expected NFTs")
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=0, token_id_max=10)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=john.address, token_id_min=10, token_id_max=15)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=admin.address, token_id_min=15, token_id_max=18)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=18, token_id_max=19)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=19, token_id_max=29)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=bob.address, token_id_min=29, token_id_max=49)
        TestHelper.check_fa2_ledger(scenario=scenario, contract=c2,
                                    owner=alice.address, token_id_min=49,token_id_max=50)

########################################################################################################################
# unit_test_user_mint_during_public_sale_with_allowlist_mint_rights
########################################################################################################################
def unit_test_user_mint_during_public_sale_with_allowlist_mint_rights(is_default=True):
    @sp.add_test(name="unit_test_user_mint_during_public_sale_with_allowlist_mint_rights", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_user_mint_during_public_sale_with_allowlist_mint_rights")

        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_public_sale_with_allowlist_mint_rights entrypoint.  (Who: for all users)")
        scenario.p("This entrypoint is called by users to mint NFTs when a public sale is opened using the allowlist and mint rights feature enabled. Any users can mint during the public sale. The ones in the allowlist have mint rights, meaning they can mint theirs NFTs (bounded by the defined max number of NFTs per user) even if all the total allocated supply is minted as long as the event is opened.")

        scenario.p("1. Fill the allowlist")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address, nat.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Verify users cannot mint if no event are opened")
        c1.user_mint(sp.record(amount=8, address=alice.address)).run(valid=False, sender=alice)

        scenario.p("3. Start a public sale with minting rights enabled")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=100,
                                            max_per_user=30,
                                            price=sp.tez(10),
                                            mint_right=True,
                                            mint_discount=sp.tez(0),
                                            )).run(valid=True, sender=admin)

        scenario.p("4. Mint NFTs")
        c1.user_mint(sp.record(amount=30, address=john.address)).run(valid=True, amount=sp.tez(300), sender=john)
        c1.user_mint(sp.record(amount=20, address=nat.address)).run(valid=True, amount=sp.tez(200), sender=nat)
        c1.user_mint(sp.record(amount=20, address=ben.address)).run(valid=True, amount=sp.tez(200), sender=ben)
        c1.user_mint(sp.record(amount=20, address=gaston.address)).run(valid=True, amount=sp.tez(200), sender=gaston)
        c1.user_mint(sp.record(amount=30, address=gabe.address)).run(valid=True, amount=sp.tez(300), sender=gabe)

        scenario.p("5. Verify users in the allowlist can always mint theirs NFTs even if all total supply is minted")
        c1.user_mint(sp.record(amount=10, address=ben.address)).run(valid=False, amount=sp.tez(100), sender=ben)
        c1.user_mint(sp.record(amount=10, address=nat.address)).run(valid=True, amount=sp.tez(100), sender=nat)
        c1.user_mint(sp.record(amount=30, address=alice.address)).run(valid=True, amount=sp.tez(300), sender=alice)
        c1.user_mint(sp.record(amount=20, address=bob.address)).run(valid=True, amount=sp.tez(200), sender=bob)
        c1.user_mint(sp.record(amount=10, address=bob.address)).run(valid=True, amount=sp.tez(100), sender=bob)

########################################################################################################################
# unit_test_mutez_transfer
########################################################################################################################
def unit_test_mutez_transfer(is_default=True):
    @sp.add_test(name="unit_test_mutez_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mutez_transfer")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john, with_balance=True)

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

########################################################################################################################
# unit_test_admin_process_presale
########################################################################################################################
def unit_test_admin_process_presale(is_default=True):
    @sp.add_test(name="unit_test_admin_process_presale", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_admin_process_presale")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the unit_test_admin_process_presale entrypoint.  (Who: Only for the admin)")

        scenario.p("1. Only admin can call the entrypoint")
        c1.admin_process_presale(simulated_presale_contract.address).run(valid=False, sender=alice)
        c1.admin_process_presale(simulated_presale_contract.address).run(valid=False, sender=bob)
        c1.admin_process_presale(simulated_presale_contract.address).run(valid=False, sender=john)

        scenario.p("2. Burn some tokens")
        simulated_presale_contract.burn(sp.list(l={1,3,7}, t=sp.TNat)).run(valid=True)

        scenario.p("3. Call the entrypoint successfully")
        c1.admin_process_presale(simulated_presale_contract.address).run(valid=True, sender=admin)

        scenario.p("3. Check the FA2 ledger contains the expected NFTs")
        scenario.verify(c2.data.ledger.contains(0))
        scenario.verify(c2.data.ledger.contains(1))
        scenario.verify(c2.data.ledger.contains(2))
        scenario.verify(c2.data.ledger.contains(3))
        scenario.verify(c2.data.ledger.contains(4))
        scenario.verify(c2.data.ledger.contains(5))
        scenario.verify(c2.data.ledger.contains(6))
        scenario.verify(c2.data.ledger.contains(7))
        scenario.verify(~c2.data.ledger.contains(8))
        scenario.verify(c2.data.ledger[0] == simulated_presale_contract.data.tokens[0])
        scenario.verify(c2.data.ledger[1] == simulated_presale_contract.data.tokens[2])
        scenario.verify(c2.data.ledger[2] == simulated_presale_contract.data.tokens[4])
        scenario.verify(c2.data.ledger[3] == simulated_presale_contract.data.tokens[5])
        scenario.verify(c2.data.ledger[4] == simulated_presale_contract.data.tokens[6])
        scenario.verify(c2.data.ledger[5] == simulated_presale_contract.data.tokens[8])
        scenario.verify(c2.data.ledger[6] == simulated_presale_contract.data.tokens[9])
        scenario.verify(c2.data.ledger[7] == simulated_presale_contract.data.tokens[10])

        scenario.p("3. Check all tokens are burned")
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(0))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(1))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(2))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(3))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(4))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(5))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(6))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(7))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(8))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(9))
        scenario.verify(simulated_presale_contract.data.burned_tokens.contains(10))
        scenario.verify(~simulated_presale_contract.data.burned_tokens.contains(11))


########################################################################################################################
# module_test_pre_sale_public_sale_with_allowlist
########################################################################################################################
def module_test_pre_sale_public_sale_with_allowlist(is_default=True):
    @sp.add_test(name="module_test_pre_sale_public_sale_with_allowlist", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("module_test_pre_sale_public_sale_with_allowlist")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test a scenario with a pre-sale and then a public sale with allowlist")

        scenario.p("1. Fill the allowlist with alice account")
        c1.admin_fill_allowlist(sp.set(l=[alice.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Fill the pre-allowlist with bob, nat and gaston accounts")
        c1.admin_fill_pre_allowlist(sp.set(l=[bob.address, nat.address, gaston.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("3. Verify non admin accounts cannot open the private allowlist registration event")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(3))).run(valid=False, sender=bob)

        scenario.p("4. Open a private allowlist registration event")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(3))).run(valid=True, sender=admin)

        scenario.p("5. pay_to_enter_allowlist_pub cannot be called when private allowlist registration event is opened")
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(3), sender=bob)

        scenario.p("6. Verify users cannot register to the allowlist if they do not pay the right amount of XTZ")
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(2), sender=bob)

        scenario.p("7. Successfully register bob in the allowlist")
        c1.pay_to_enter_allowlist_priv().run(valid=True, amount=sp.tez(3), sender=bob)

        scenario.p("8. Verify users that are not in the pre-allowlist cannot register to the allowlist in this event")
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(3), sender=bob)
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(3), sender=alice)
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(3), sender=john)

        scenario.p("9. Successfully register nat in the allowlist")
        c1.pay_to_enter_allowlist_priv().run(valid=True, amount=sp.tez(3), sender=nat)

        scenario.p("10. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(bob.address) == 0)
        scenario.verify(c1.get_mint_token_available(nat.address) == 0)
        scenario.verify(c1.get_mint_token_available(alice.address) == 0)
        scenario.verify(c1.get_mint_token_available(admin.address) == 0)

        scenario.p("11. Verify only admin can close the open event")
        c1.close_any_open_event().run(valid=False, sender=nat)

        scenario.p("12. Successfully close the private allowlist registration")
        c1.close_any_open_event().run(valid=True, sender=admin)

        scenario.p("13. Verify the event is closed and pay_to_enter_allowlist_priv cannot be called anymore")
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(3), sender=gaston)

        scenario.p("14. Verify only admin can open the public allowlist registration")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=2, price=sp.tez(5))).run(valid=False, sender=bob)

        scenario.p("15. Open the public allowlist registration event")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=2, price=sp.tez(5))).run(valid=True, sender=admin)
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(5), sender=gaston)


        scenario.p("16. Verify any user can register to the allowlist now")
        c1.pay_to_enter_allowlist_pub().run(valid=True, amount=sp.tez(5), sender=gaston)

        scenario.p("17. Verify users already in the allowlist cannot register anymore or if do not pay the right amoun")
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(5), sender=alice)
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(5), sender=nat)
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(5), sender=bob)
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(3), sender=gabe)
        c1.pay_to_enter_allowlist_pub().run(valid=True, amount=sp.tez(5), sender=gabe)

        scenario.p("18. Verify that users cannot register anymore in the allowlist when all the allocated spaces in the event are taken")
        c1.pay_to_enter_allowlist_pub().run(valid=False, amount=sp.tez(5), sender=ben)

        scenario.p("19. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(bob.address) == 0)
        scenario.verify(c1.get_mint_token_available(nat.address) == 0)
        scenario.verify(c1.get_mint_token_available(alice.address) == 0)
        scenario.verify(c1.get_mint_token_available(admin.address) == 0)

        scenario.p("20. Verify only the admin can close the event")
        c1.close_any_open_event().run(valid=False, sender=bob)

        scenario.p("21. Check event is already closed")
        c1.close_any_open_event().run(valid=False, sender=admin)

        scenario.p("22. Verify only the admin can open a pre-sale event")
        c1.open_pre_sale(sp.record(max_supply=50, max_per_user=15, price=sp.tez(100))).run(
            valid=False, sender=john)

        scenario.p("23. Successfully open a pre-sale event")
        c1.open_pre_sale(sp.record(max_supply=50, max_per_user=15, price=sp.tez(100))).run(
            valid=True, sender=admin)

        scenario.p("24. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(bob.address) == 15)
        scenario.verify(c1.get_mint_token_available(nat.address) == 15)
        scenario.verify(c1.get_mint_token_available(alice.address) == 15)
        scenario.verify(c1.get_mint_token_available(gabe.address) == 15)
        scenario.verify(c1.get_mint_token_available(admin.address) == 0)


        scenario.p("25. Verify users cannot mint more than the number of NFT mintable per user in this event")
        c1.user_mint(sp.record(amount=16, address=alice.address)).run(valid=False, amount=sp.tez(1600), sender=alice)


        scenario.p("26. Verify users shall pay the right amount of XTZ to mint")
        c1.user_mint(sp.record(amount=16, address=alice.address)).run(valid=False, amount=sp.tez(1495), sender=alice)
        c1.user_mint(sp.record(amount=15, address=alice.address)).run(valid=True, amount=sp.tez(1500), sender=alice)
        c1.user_mint(sp.record(amount=15, address=bob.address)).run(valid=True, amount=sp.tez(1500), sender=bob)
        scenario.verify(c1.get_mint_token_available(bob.address) == 0)

        scenario.p("27. Verify users cannot mint more than the total supply allocated in this event")
        c1.user_mint(sp.record(amount=10, address=nat.address)).run(valid=True, amount=sp.tez(1000), sender=nat)
        scenario.verify(c1.get_mint_token_available(nat.address) == 5)
        c1.user_mint(sp.record(amount=5, address=gaston.address)).run(valid=True, amount=sp.tez(500), sender=gaston)
        # Not enough remaining
        c1.user_mint(sp.record(amount=6, address=gabe.address)).run(valid=False, amount=sp.tez(600), sender=gabe)
        c1.user_mint(sp.record(amount=5, address=gabe.address)).run(valid=True, amount=sp.tez(500), sender=gabe)

        scenario.p("28. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(bob.address) == 0)
        scenario.verify(c1.get_mint_token_available(nat.address) == 0)
        scenario.verify(c1.get_mint_token_available(alice.address) == 0)
        scenario.verify(c1.get_mint_token_available(admin.address) == 0)

        scenario.p("29. Verify only admin can close the event")
        c1.close_any_open_event().run(valid=False, sender=john)

        scenario.p("30. Close the event successfully")
        c1.close_any_open_event().run(valid=True, sender=admin)

        scenario.p("31. Verify only admin can open the public sale")
        c1.open_pub_sale_with_allowlist(sp.record(
            max_supply=50,
            max_per_user=10,
            price=sp.tez(150),
            mint_right=True,
            mint_discount=sp.tez(100))).run(valid=False, sender=ben)

        scenario.p("32. Successfully open a public sale with allowlist using the discount and mint right features")
        c1.open_pub_sale_with_allowlist(sp.record(
            max_supply=30,
            max_per_user=20,
            price=sp.tez(200),
            mint_right=True,
            mint_discount=sp.tez(100))).run(valid=True, sender=admin)

        scenario.p("33. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(alice.address) == 20)
        scenario.verify(c1.get_mint_token_available(john.address) == 20)
        scenario.verify(c1.get_mint_token_available(ben.address) == 20)

        scenario.p("34. Verify Alice can mint with a discount as she is in the allowlist")
        c1.user_mint(sp.record(amount=20, address=alice.address)).run(valid=False, amount=sp.tez(4000), sender=alice)
        c1.user_mint(sp.record(amount=21, address=alice.address)).run(valid=False, amount=sp.tez(2100), sender=alice)
        c1.user_mint(sp.record(amount=20, address=alice.address)).run(valid=True, amount=sp.tez(2000), sender=alice)

        scenario.p("35. Verify John can mint but without the discount as he is not in the allowlist")
        c1.user_mint(sp.record(amount=20, address=john.address)).run(valid=False, amount=sp.tez(2000), sender=john)
        c1.user_mint(sp.record(amount=20, address=john.address)).run(valid=True, amount=sp.tez(4000), sender=john)
        scenario.verify(c1.get_mint_token_available(john.address) == 0)
        c1.user_mint(sp.record(amount=10, address=ben.address)).run(valid=True, amount=sp.tez(2000), sender=ben)

        scenario.p("36. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(alice.address) == 0)
        scenario.verify(c1.get_mint_token_available(ben.address) == 0)
        scenario.verify(c1.get_mint_token_available(nat.address) == 20)
        scenario.verify(c1.get_mint_token_available(bob.address) == 20)

        scenario.p("37. Verify there is no supply anymore for users not in the allowlist")
        c1.user_mint(sp.record(amount=1, address=chris.address)).run(valid=False, amount=sp.tez(200), sender=chris)

        scenario.p("38. Verify users in the allowlist can still mint using their mint rights")
        c1.user_mint(sp.record(amount=20, address=bob.address)).run(valid=True, amount=sp.tez(2000), sender=bob)
        scenario.verify(c1.get_mint_token_available(bob.address) == 0)
        c1.user_mint(sp.record(amount=10, address=nat.address)).run(valid=True, amount=sp.tez(1000), sender=nat)
        scenario.verify(c1.get_mint_token_available(nat.address) == 10)
        c1.user_mint(sp.record(amount=10, address=nat.address)).run(valid=True, amount=sp.tez(1000), sender=nat)
        scenario.verify(c1.get_mint_token_available(nat.address) == 0)

        scenario.p("39. Verify that even users with mint rights cannot mint more than the max number of NFT mintable per user")
        c1.user_mint(sp.record(amount=10, address=nat.address)).run(valid=False, amount=sp.tez(1000), sender=nat)

        scenario.p("40. Verify only admin can close the event")
        c1.close_any_open_event().run(valid=False, sender=nat)

        scenario.p("41. Successfully close the event")
        c1.close_any_open_event().run(valid=True, sender=admin)

        scenario.p("42. Verify users, even if in allowlist, cannot mint anymore when event is closed")
        c1.user_mint(sp.record(amount=20, address=gabe.address)).run(valid=False, amount=sp.tez(2000), sender=gabe)

        scenario.p("43. Verify only admin can clear the allowlist")
        c1.clear_allowlist().run(valid=False, sender=bob)
        c1.clear_allowlist().run(valid=False, sender=alice)
        c1.clear_allowlist().run(valid=False, sender=john)
        c1.clear_allowlist().run(valid=False, sender=nat)

        scenario.p("44. Successfully clear the allowlist")
        c1.clear_allowlist().run(valid=True, sender=admin)

        scenario.p("45. Verify allowlist is cleared in the contract storage")
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        scenario.verify(c1.data.state == Sale.STATE_NO_EVENT_OPEN_0)

        scenario.p("46. Check the FA2 ledger contains the expected NFTs")
        TestHelper.check_fa2_ledger(scenario, c2, alice.address, 0, 15)
        TestHelper.check_fa2_ledger(scenario, c2, bob.address, 15, 30)
        TestHelper.check_fa2_ledger(scenario, c2, nat.address, 30, 40)
        TestHelper.check_fa2_ledger(scenario, c2, gaston.address, 40, 45)
        TestHelper.check_fa2_ledger(scenario, c2, gabe.address, 45, 50)
        TestHelper.check_fa2_ledger(scenario, c2, alice.address, 50, 70)
        TestHelper.check_fa2_ledger(scenario, c2, john.address, 70, 90)
        TestHelper.check_fa2_ledger(scenario, c2, ben.address, 90, 100)
        TestHelper.check_fa2_ledger(scenario, c2, bob.address, 100, 120)
        TestHelper.check_fa2_ledger(scenario, c2, nat.address, 120, 140)

########################################################################################################################
# module_test_public_sale
########################################################################################################################
def module_test_public_sale(is_default=True):
    @sp.add_test(name="module_test_public_sale", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("module_test_public_sale")

        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, c2, simulated_presale_contract = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test a scenario with a a public sale without allowlist")

        scenario.p("1. Verify only admin can open a public sale")
        c1.open_pub_sale(sp.record(
            max_supply=30,
            max_per_user=20,
            price=sp.tez(200))).run(valid=False, sender=bob)

        scenario.p("2. Successfully open a public sale without allowlist")
        c1.open_pub_sale(sp.record(
            max_supply=30,
            max_per_user=20,
            price=sp.tez(200))).run(valid=True, sender=admin)

        scenario.p("3. Check users cannot mint more NFTs that the max number mintable per user in this event")
        c1.user_mint(sp.record(amount=21, address=alice.address)).run(valid=False, amount=sp.tez(4200), sender=alice)

        scenario.p("4. Check the user can mint the max number of NFT mintable per user in this event in one call")
        c1.user_mint(sp.record(amount=20, address=alice.address)).run(valid=True, amount=sp.tez(4000), sender=alice)
        c1.user_mint(sp.record(amount=10, address=john.address)).run(valid=False, amount=sp.tez(4000), sender=john)
        c1.user_mint(sp.record(amount=10, address=ben.address)).run(valid=True, amount=sp.tez(2000), sender=ben)

        scenario.p("5. Check the user cannot mint more than the total allocated supply in this event")
        c1.user_mint(sp.record(amount=10, address=ben.address)).run(valid=False, amount=sp.tez(2000), sender=ben)

        scenario.p("6. Check users can mint exactly the total allocated supply in this event")
        c1.user_mint(sp.record(amount=20, address=chris.address)).run(valid=False, amount=sp.tez(4000), sender=chris)

        scenario.p("7. Check only admin can close the event")
        c1.close_any_open_event().run(valid=False, sender=nat)

        scenario.p("8. Successfully close the event")
        c1.close_any_open_event().run(valid=True, sender=admin)

        scenario.p("9. Check the FA2 ledger contains the expected NFTs")
        TestHelper.check_fa2_ledger(scenario, c2, alice.address, 0, 20)
        TestHelper.check_fa2_ledger(scenario, c2, ben.address, 20, 30)

# Execute tests --------------------------------------------------------------------------------------------------------
unit_test_initial_storage()
unit_test_admin_fill_allowlist()
unit_test_admin_fill_pre_allowlist()
unit_test_open_event_priv_allowlist_reg()
unit_test_pay_to_enter_allowlist_priv()
unit_test_open_event_pub_allowlist_reg()
unit_test_pay_to_enter_allowlist_pub()
unit_test_open_pre_sale()
unit_test_open_pub_sale()
unit_test_open_pub_sale_with_allowlist()
unit_test_mint_and_give()
unit_test_set_next_administrator()
unit_test_validate_new_administrator()
unit_test_set_multisig_fund_address()
unit_test_register_fa2()
unit_test_user_mint_during_public_sale()
unit_test_user_mint_during_pre_sale()
unit_test_user_mint_during_public_sale_with_allowlist_discount()
unit_test_user_mint_during_public_sale_with_allowlist_mint_rights()
unit_test_mutez_transfer()
unit_test_admin_process_presale()
module_test_pre_sale_public_sale_with_allowlist()
module_test_public_sale()
