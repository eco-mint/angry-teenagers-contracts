import smartpy as sp

NFT = sp.io.import_script_from_url("file:./nft/nft.py")

########################################################################################################################
########################################################################################################################
# Testing
########################################################################################################################
##################################################################################################################
# Unit Test ------------------------------------------------------------------------------------------------------------

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

########################################################################################################################
# Helper class for unit testing
########################################################################################################################
class TestHelper():
    def create_scenario(name):
        scenario = sp.test_scenario()
        scenario.h1(name)
        scenario.table_of_contents()
        return scenario

    def create_contracts(scenario, admin, john):
        c1  = NFT.AngryTeenagers(administrator=admin.address,
                        royalties_bytes=sp.utils.bytes_of_string('{"decimals": 3, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'),
                        metadata=sp.utils.metadata_of_url("https://example.com"),
                        generic_image_ipfs=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"),
                        generic_image_ipfs_display=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2"),
                        generic_image_ipfs_thumbnail=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"),
                        project_oracles_stream=sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"),
                        what3words_file_ipfs=sp.utils.bytes_of_string(
                            "ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"),
                        total_supply=128,
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
                        project_name=PROJECTNAME
                            )
        scenario += c1
        scenario.h2("Contracts")
        scenario.p("c1: This FA2 contract to test")
        return c1

    def create_account(scenario):
        admin = sp.test_account("admin")
        alice = sp.test_account("alice")
        bob = sp.test_account("bob")
        john = sp.test_account("john")
        scenario.h2("Accounts")
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
            scenario.verify(contract.data.token_metadata.contains(x))
            scenario.verify(contract.data.ledger.contains(x))

    def mint_4_tokens(scenario, c1, bob, admin, nat, john, ben, gabe):
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)

        scenario.verify(c1.count_tokens() == 0)
        scenario.verify(c1.does_token_exist(0) == False)
        scenario.verify(c1.does_token_exist(1) == False)
        scenario.verify(c1.does_token_exist(2) == False)
        scenario.verify(c1.does_token_exist(3) == False)
        scenario.verify(c1.does_token_exist(4) == False)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={}, t=sp.TNat))
        c1.mint(nat.address).run(valid=True, sender=bob)
        c1.mint(john.address).run(valid=True, sender=bob)
        c1.mint(ben.address).run(valid=True, sender=bob)
        c1.mint(gabe.address).run(valid=True, sender=bob)
        scenario.verify(c1.count_tokens() == 4)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == True)
        scenario.verify(c1.does_token_exist(2) == True)
        scenario.verify(c1.does_token_exist(3) == True)
        scenario.verify(c1.does_token_exist(4) == False)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={0, 1, 2, 3}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(nat.address), sp.list(l={0}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(john.address), sp.list(l={1}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(ben.address), sp.list(l={2}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(gabe.address), sp.list(l={3}, t=sp.TNat))

    def compare_list(scenario, a, b):
        scenario.verify_equal(a, b)

    def compare_bytes(scenario,a, b):
        scenario.verify_equal(sp.len(a), sp.len(b))
        for i in (0, sp.len(a)):
            scenario.verify(sp.slice(a, i, i).open_some() != sp.slice(b, i, i).open_some())

    def format_helper(artifact_link, display_link, thumbnail_link, artifact_size, display_size, thumbnail_size):
        # This function hardcodes string to be sure the contract is building the expected final string
        value = '[{"uri":"' + artifact_link + \
                '","mimeType":"image/png","fileSize":' + artifact_size + ',"fileName":"angry_teenagers.png","dimensions":{"value":"1000x1000","unit":"px"}},{"uri":"' + \
                display_link + '","mimeType":"image/jpeg","fileSize":' + display_size + ',"fileName":"angry_teenagers_display.jpeg","dimensions":{"value":"1000x1000","unit":"px"}},{"uri":"' + \
                thumbnail_link + '","mimeType":"image/jpeg","fileSize":' + thumbnail_size + ',"fileName":"angry_teenagers_thumbnail.jpeg","dimensions":{"value":"350x350","unit":"px"}}]'
        return sp.utils.bytes_of_string(value)

########################################################################################################################
# unit_fa2_test_initial_storage
########################################################################################################################
def unit_fa2_test_initial_storage(is_default = True):
    @sp.add_test(name="unit_fa2_test_initial_storage", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_initial_storage")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the storage is initialized as expected.")

        scenario.p("1. Read each entry of the storage of the c1 contract and check it is initialized as expected")
        scenario.verify(c1.data.administrator == admin.address)
        scenario.verify(c1.data.sale_contract_administrator == admin.address)
        scenario.verify(c1.data.artwork_administrator == admin.address)
        scenario.verify(c1.data.what3words_file_ipfs == sp.utils.bytes_of_string(
                                "ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify(c1.data.total_supply == 128)
        scenario.verify(c1.data.minted_tokens == sp.nat(0))
        scenario.verify(c1.data.paused == sp.bool(False))
        scenario.verify(c1.data.generic_image_ipfs == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify(c1.data.generic_image_ipfs_display == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2"))
        scenario.verify(c1.data.generic_image_ipfs_thumbnail == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"))
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

        scenario.verify(c1.data.project_oracles_stream == sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"))

        scenario.verify(c1.data.royalties == sp.utils.bytes_of_string('{"decimals": 3, "shares": { "' + "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5" + '": 10}}'))

        scenario.verify(~c1.data.token_metadata.contains(0))

########################################################################################################################
# unit_fa2_test_mint
########################################################################################################################
def unit_fa2_test_mint(is_default = True):
    @sp.add_test(name="unit_fa2_test_mint", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_mint")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint mint. (Who: Only for main admin or sale contract admin)")

        scenario.p("1. Set the sale contract admin to be bob and the artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Check only main admin or sale contract can mint")
        c1.mint(nat.address).run(valid=False, sender=nat)
        c1.mint(nat.address).run(valid=False, sender=ben)
        c1.mint(nat.address).run(valid=False, sender=gabe)
        c1.mint(nat.address).run(valid=False, sender=chris)
        c1.mint(nat.address).run(valid=False, sender=john)

        scenario.p("3. Check that no NFTs have been minted yet in the contract storage")
        scenario.p("4. Check that offchain views all_tokens and get_user_tokens return the expected values")
        scenario.verify(c1.count_tokens() == 0)
        scenario.verify(c1.does_token_exist(0) == False)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(nat.address), sp.list(l={}, t=sp.TNat))

        scenario.p("5. Successfully mint with the sale admin and the main admin")
        c1.mint(nat.address).run(valid=True, sender=bob)

        scenario.p("6. Check that offchain views all_tokens, get_user_tokens and does_token_exist return the expected values")
        scenario.verify(c1.count_tokens() == 1)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == False)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={0}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(nat.address), sp.list(l={0}, t=sp.TNat))

        scenario.p("7. Mint more token")
        c1.mint(nat.address).run(valid=True, sender=admin)
        scenario.verify(c1.count_tokens() == 2)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == True)
        scenario.verify(c1.does_token_exist(2) == False)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={0, 1}, t=sp.TNat))

        scenario.p("8. Mint more tokens")
        scenario.p("10. Check that offchain views all_tokens, get_user_tokens and does_token_exist return the expected values")
        c1.mint(nat.address).run(valid=True, sender=bob)
        scenario.verify(c1.count_tokens() == 3)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == True)
        scenario.verify(c1.does_token_exist(2) == True)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={0, 1, 2}, t=sp.TNat))
        scenario.verify(c1.does_token_exist(3) == False)
        c1.mint(chris.address).run(valid=True, sender=bob)
        scenario.verify(c1.count_tokens() == 4)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == True)
        scenario.verify(c1.does_token_exist(2) == True)
        scenario.verify(c1.does_token_exist(3) == True)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={0, 1, 2, 3}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(chris.address), sp.list(l={3}, t=sp.TNat))
        scenario.verify(c1.does_token_exist(4) == False)
        c1.mint(bob.address).run(valid=True, sender=bob)
        scenario.verify(c1.count_tokens() == 5)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == True)
        scenario.verify(c1.does_token_exist(2) == True)
        scenario.verify(c1.does_token_exist(3) == True)
        scenario.verify(c1.does_token_exist(4) == True)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={0, 1, 2, 3, 4}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(chris.address), sp.list(l={3}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(bob.address), sp.list(l={4}, t=sp.TNat))
        scenario.verify(c1.does_token_exist(5) == False)
        c1.mint(john.address).run(valid=True, sender=bob)
        scenario.verify(c1.count_tokens() == 6)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == True)
        scenario.verify(c1.does_token_exist(2) == True)
        scenario.verify(c1.does_token_exist(3) == True)
        scenario.verify(c1.does_token_exist(4) == True)
        scenario.verify(c1.does_token_exist(5) == True)
        TestHelper.compare_list(scenario, c1.all_tokens(), sp.list(l={0, 1, 2, 3, 4, 5}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(chris.address), sp.list(l={3}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(bob.address), sp.list(l={4}, t=sp.TNat))
        TestHelper.compare_list(scenario, c1.get_user_tokens(john.address), sp.list(l={5}, t=sp.TNat))
        scenario.verify(c1.does_token_exist(6) == False)

        scenario.p("9. Check ledger in the storage contains expected NFTs")
        scenario.verify(c1.data.minted_tokens == sp.nat(6))
        scenario.verify(c1.data.ledger[0] == nat.address)
        scenario.verify(c1.data.ledger[1] == nat.address)
        scenario.verify(c1.data.ledger[2] == nat.address)
        scenario.verify(c1.data.ledger[3] == chris.address)
        scenario.verify(c1.data.ledger[4] == bob.address)
        scenario.verify(c1.data.ledger[5] == john.address)

        scenario.p("10. Check minted NFTs are not revealed yet")
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[4]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[5]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify(~c1.data.token_metadata.contains(6))

def unit_fa2_test_mint_max(is_default=True):
    @sp.add_test(name="unit_fa2_test_mint_max", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_mint_max")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test to mint the maximum number of possible NFTs in the contract")

        scenario.p("1. Simulate minting NFTs until max is reached")
        for i in range(128):
            c1.mint(bob.address).run(valid=True, sender=admin)
        c1.mint(bob.address).run(valid=False, sender=admin)
        scenario.verify(c1.data.minted_tokens == sp.nat(128))

########################################################################################################################
# unit_fa2_test_set_royalties
########################################################################################################################
def unit_fa2_test_set_royalties(is_default=True):
    @sp.add_test(name="unit_fa2_test_set_royalties", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_set_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint set_royalties. (Who: Only for main admin)")

        scenario.p("1. Set sale admin to be bob and the artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Check only main admin can call set_royalties")
        first_new_royalties = sp.utils.bytes_of_string('{"decimals": 3, "shares": { "' + "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf6" + '": 20}}')
        c1.set_royalties(first_new_royalties).run(valid=False, sender=bob)
        c1.set_royalties(first_new_royalties).run(valid=False, sender=john)
        c1.set_royalties(first_new_royalties).run(valid=False, sender=alice)
        c1.set_royalties(first_new_royalties).run(valid=True, sender=admin)

        scenario.p("3. Verify royalties are changed accordingly in the contract starage after a successful call of set_royalties")
        scenario.verify_equal(c1.data.royalties, first_new_royalties)

        scenario.p("4. Mint NFTs")
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(bob.address).run(valid=True, sender=admin)

        scenario.p("5. Check royalties field")
        scenario.verify(c1.data.token_metadata.contains(0))
        info_0 = sp.snd(c1.data.token_metadata[0])
        scenario.verify(c1.data.token_metadata.contains(1))
        info_1 = sp.snd(c1.data.token_metadata[1])
        scenario.verify(c1.data.token_metadata.contains(2))
        info_2 = sp.snd(c1.data.token_metadata[2])
        scenario.verify(c1.data.token_metadata.contains(3))
        info_3 = sp.snd(c1.data.token_metadata[3])
        scenario.verify(info_0[NFT.ROYALTIES_METADATA] == first_new_royalties)
        scenario.verify(info_1[NFT.ROYALTIES_METADATA] == first_new_royalties)
        scenario.verify(info_2[NFT.ROYALTIES_METADATA] == first_new_royalties)
        scenario.verify(info_3[NFT.ROYALTIES_METADATA] == first_new_royalties)

        scenario.p("6. Change again the royalties")
        second_new_royalties = sp.utils.bytes_of_string('{"decimals": 3, "shares": { "' + "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf7" + '": 30}}')
        c1.set_royalties(second_new_royalties).run(valid=True, sender=admin)

        scenario.p("7. Mint another NFTs")
        c1.mint(alice.address).run(valid=True, sender=admin)

        scenario.p("8. Verify all NFTs contain the right royalties field")
        scenario.verify(c1.data.token_metadata.contains(4))
        info_4 = sp.snd(c1.data.token_metadata[4])
        scenario.verify_equal(c1.data.royalties, second_new_royalties)
        scenario.verify(info_0[NFT.ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_1[NFT.ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_2[NFT.ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_3[NFT.ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_4[NFT.ROYALTIES_METADATA] == second_new_royalties)


########################################################################################################################
# unit_fa2_test_set_administrator
########################################################################################################################
def unit_fa2_test_set_administrator(is_default=True):
    @sp.add_test(name="unit_fa2_test_set_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_set_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2(" Test the entrypoint set_admin. (Who: Only for main admin)")
        scenario.p("Used to change the main admin.")

        scenario.p("1. Set sale admin to be bob and the artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Check main admin is set as expected in the contract storage")
        scenario.verify(c1.data.administrator == admin.address)

        scenario.p("3. Check only main admin can call set_admin")
        c1.set_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_administrator(alice.address).run(valid=False, sender=bob)
        c1.set_administrator(alice.address).run(valid=False, sender=john)

        scenario.p("4. Successfully change the main admin to be alice and check that:")
        c1.set_administrator(alice.address).run(valid=True, sender=admin)

        scenario.p("5. Main admin in contract storage is alice")
        scenario.verify(c1.data.administrator == alice.address)

        scenario.p("6. Admin is not main admin anymore")
        c1.set_administrator(bob.address).run(valid=False, sender=admin)
        c1.set_administrator(bob.address).run(valid=False, sender=bob)
        c1.set_administrator(bob.address).run(valid=False, sender=john)

        scenario.p("7. Only alice can call set_admin")
        scenario.p("8. Successfully change the main admin to be bob and check that:")
        c1.set_administrator(bob.address).run(valid=True, sender=alice)

        scenario.p("9. Main admin in contract storage is now bob")
        scenario.verify(c1.data.administrator == bob.address)

        scenario.p("10. Offchain views count_tokens and does_token_exist return the expected result")
        scenario.verify(c1.count_tokens() == 0)
        scenario.verify(c1.does_token_exist(0) == False)

########################################################################################################################
# unit_fa2_test_set_sale_contract_administrator
########################################################################################################################
def unit_fa2_test_set_sale_contract_administrator(is_default=True):
    @sp.add_test(name="unit_fa2_test_set_sale_contract_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_set_sale_contract_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint set_sale_contract_administrator. (Who: Only main admin)")
        scenario.p("Used to change the sale contract admin. ")

        scenario.p("1. Set artwork administrator to be john")
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Check that the sale contract administrator is the admin by default")
        scenario.verify(c1.data.sale_contract_administrator == admin.address)

        scenario.p("3. Check that only the main admin can change the sale contract administrator")
        c1.set_sale_contract_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_sale_contract_administrator(alice.address).run(valid=False, sender=bob)
        c1.set_sale_contract_administrator(alice.address).run(valid=False, sender=john)

        scenario.p("4. Successfully change the sale contract administrator to be alice")
        c1.set_sale_contract_administrator(alice.address).run(valid=True, sender=admin)

        scenario.p("5. Check the sale contract administrator is alice in the contract storage")
        scenario.verify(c1.data.sale_contract_administrator == alice.address)

        scenario.p("6. Check that only the main admin can change the sale contract administrator")
        c1.set_sale_contract_administrator(bob.address).run(valid=False, sender=alice)
        c1.set_sale_contract_administrator(bob.address).run(valid=False, sender=bob)
        c1.set_sale_contract_administrator(bob.address).run(valid=False, sender=john)

        scenario.p("8. Successfully change the sale contract administrator to be bob")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)

        scenario.p("9. Check the sale contract administrator is bob in the contract storage")
        scenario.verify(c1.data.sale_contract_administrator == bob.address)

        scenario.p("10. Check that offchain views count_tokens and does_token_exist return the expected values")
        scenario.verify(c1.count_tokens() == 0)
        scenario.verify(c1.does_token_exist(0) == False)

########################################################################################################################
# unit_fa2_test_set_artwork_administrator
########################################################################################################################
def unit_fa2_test_set_artwork_administrator(is_default=True):
    @sp.add_test(name="unit_fa2_test_set_artwork_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_set_artwork_administrator")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint set_artwork_administrator. (Who: Only main admin)")
        scenario.p("Used to change the artwork contract admin. ")

        scenario.p("1. Set sale contract administrator to be john")
        c1.set_sale_contract_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Check that the artwork administrator is the admin by default")
        scenario.verify(c1.data.artwork_administrator == admin.address)

        scenario.p("3. Check that only the main admin can change the artwork administrator")
        c1.set_artwork_administrator(alice.address).run(valid=False, sender=alice)
        c1.set_artwork_administrator(alice.address).run(valid=False, sender=bob)
        c1.set_artwork_administrator(alice.address).run(valid=False, sender=john)

        scenario.p("4. Successfully change the artwork administrator to be alice")
        c1.set_artwork_administrator(alice.address).run(valid=True, sender=admin)

        scenario.p("5. Check the artwork administrator is alice in the contract storage")
        scenario.verify(c1.data.artwork_administrator == alice.address)

        scenario.p("6. Check that only the main admin can change the artwork administrator")
        c1.set_artwork_administrator(bob.address).run(valid=False, sender=alice)
        c1.set_artwork_administrator(bob.address).run(valid=False, sender=bob)
        c1.set_artwork_administrator(bob.address).run(valid=False, sender=john)

        scenario.p("8. Successfully change the artwork administrator to be bob")
        c1.set_artwork_administrator(bob.address).run(valid=True, sender=admin)

        scenario.p("9. Check the artwork administrator is bob in the contract storage")
        scenario.verify(c1.data.artwork_administrator == bob.address)

        scenario.p("10. Check that offchain views count_tokens and does_token_exist return the expected values")
        scenario.verify(c1.count_tokens() == 0)
        scenario.verify(c1.does_token_exist(0) == False)

########################################################################################################################
# unit_fa2_test_set_pause
########################################################################################################################
def unit_fa2_test_set_pause(is_default=True):
    @sp.add_test(name="unit_fa2_test_set_pause", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_set_pause")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint set_pause. (Who: Only main admin)")
        scenario.p("Used to pause the FA2 contract.")

        scenario.p("1. Check the pause to set to False by default in the contract storage")
        scenario.verify(c1.data.paused == False)

        scenario.p("2. Check that only the main admin can call the set_pause entrypoint")
        c1.set_pause(True).run(valid=False, sender=alice)
        c1.set_pause(True).run(valid=False, sender=bob)
        c1.set_pause(True).run(valid=False, sender=john)
        scenario.verify(c1.data.paused == False)

        scenario.p("3. Successfully set the contract to pause")
        c1.set_pause(True).run(valid=True, sender=admin)

        scenario.p("4. Check the pause is set to True in the contract storage")
        scenario.verify(c1.data.paused == True)

        scenario.p("5. Check only the admin can set back the contract to False")
        c1.set_pause(False).run(valid=False, sender=alice)
        c1.set_pause(False).run(valid=False, sender=bob)
        c1.set_pause(False).run(valid=False, sender=john)
        scenario.verify(c1.data.paused == True)

        scenario.p("6. Successfully set back the pause to False")
        c1.set_pause(False).run(valid=True, sender=admin)

        scenario.p("7. Check the pause is set to False in the contract storage")
        scenario.verify(c1.data.paused == False)

        scenario.p("8. Check that offchain views count_tokens and does_token_exist return the expected values")
        scenario.verify(c1.count_tokens() == 0)
        scenario.verify(c1.does_token_exist(0) == False)

########################################################################################################################
# unit_fa2_test_update_artwork_data
########################################################################################################################
def unit_fa2_test_update_artwork_data(is_default=True):
    @sp.add_test(name="unit_fa2_test_update_artwork_data", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_update_artwork_data")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint update_artwork_data. (Who: Only main admin and artwork admin)")
        scenario.p("Used to pause the FA2 contract.")

        artifact_size_1 = "400001"
        artifact_size_2 = "400002"
        artifact_size_3 = "400003"
        display_size_1 = "100001"
        display_size_2 = "100002"
        display_size_3 = "100003"
        thumbnail_size_1 = "20001"
        thumbnail_size_2 = "20002"
        thumbnail_size_3 = "20003"
        record1 = sp.record(artifact_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"),
                            display_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"),
                            thumbnail_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"),
                            attributes=sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'),
                            artifact_size=sp.utils.bytes_of_string(artifact_size_1),
                            display_size=sp.utils.bytes_of_string(display_size_1),
                            thumbnail_size=sp.utils.bytes_of_string(thumbnail_size_1))
        record2 = sp.record(artifact_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"),
                            display_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"),
                            thumbnail_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"),
                            attributes=sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'),
                            artifact_size=sp.utils.bytes_of_string(artifact_size_2),
                            display_size=sp.utils.bytes_of_string(display_size_2),
                            thumbnail_size=sp.utils.bytes_of_string(thumbnail_size_2))
        record3 = sp.record(artifact_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"),
                            display_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"),
                            thumbnail_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"),
                            attributes=sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'),
                            artifact_size=sp.utils.bytes_of_string(artifact_size_3),
                            display_size=sp.utils.bytes_of_string(display_size_3),
                            thumbnail_size=sp.utils.bytes_of_string(thumbnail_size_3))
        list1 = sp.list({sp.pair(1, record1), sp.pair(2, record2)})
        list2 = sp.list({sp.pair(3, record3)})

        scenario.p("1. Check that NFT cannot be revealed if they are not minted")
        c1.update_artwork_data(list1).run(valid=False, sender=admin)

        scenario.p("2. Successfully mint 4 NFTs")
        TestHelper.mint_4_tokens(scenario, c1, bob, admin, nat, john, ben, gabe)

        scenario.p("3. Check that minted NFTs are not revealed yet")
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))

        scenario.p("4. Check that only the main or artwork admin can reveal token metadata")
        c1.update_artwork_data(list1).run(valid=False, sender=alice)
        c1.update_artwork_data(list1).run(valid=False, sender=john)
        c1.update_artwork_data(list1).run(valid=False, sender=bob)
        c1.update_artwork_data(list1).run(valid=False, sender=chris)
        c1.update_artwork_data(list1).run(valid=False, sender=gabe)

        scenario.p("5. Set the artwork admin to be the gaston account")
        c1.set_artwork_administrator(gaston.address).run(valid=True, sender=admin)

        scenario.p("6. Check only the main admin and the artwork admin can reveal NFTs by calling update_artwork_data")
        scenario.p("7. Reveal NFTs successfully and check the storage is updated accordingly")
        c1.update_artwork_data(list1).run(valid=True, sender=gaston)
        c1.update_artwork_data(list2).run(valid=True, sender=admin)

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))

        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'))

        scenario.p("8. Reveal NFT 0")
        list4 = sp.list({sp.pair(0, record2)})
        c1.update_artwork_data(list4).run(valid=True, sender=gaston)

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.THUMBNAILURI_METADATA]  == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'))

        scenario.p("9. Check the function update_artwork_data cannot be called multiple times on the same NFT")
        list3 = sp.list({sp.pair(0, record2), sp.pair(2, record3), sp.pair(1, record2)})
        c1.update_artwork_data(list3).run(valid=False, sender=gaston)

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.REVEALED_METADATA] == sp.utils.bytes_of_string("true"))

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.THUMBNAILURI_METADATA]  == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[NFT.ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'))

        list5 = sp.list({sp.pair(4, record2)})
        c1.update_artwork_data(list5).run(valid=False, sender=gaston)

        scenario.p("10. Check the offchain views does_token_exist and count_tokens return the expected values")
        scenario.verify(c1.count_tokens() == 4)
        scenario.verify(c1.does_token_exist(0) == True)
        scenario.verify(c1.does_token_exist(1) == True)
        scenario.verify(c1.does_token_exist(2) == True)
        scenario.verify(c1.does_token_exist(3) == True)
        scenario.verify(c1.does_token_exist(4) == False)

########################################################################################################################
# unit_fa2_test_mutez_transfer
########################################################################################################################
def unit_fa2_test_mutez_transfer(is_default=True):
    @sp.add_test(name="unit_fa2_test_mutez_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_mutez_transfer")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the mutez_transfer entrypoint. (Who: Only for main admin)")
        scenario.p("This entrypoint is called byt the main admin to extract fund on the contract. Normally no funds are supposed to be held in the contract however if something bad happens or somebody makes a mistake transfer, we still want to have the ability to extract the fund.")

        scenario.p("1. Add fund to the contract")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin, amount=sp.mutez(300000000))

        scenario.p("2. Check that only the admin can call this entrypoint")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=alice)
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=bob)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(200000000))).run(valid=False, sender=john)

        scenario.p("3. Check the function extracts the fund as expected")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=True, sender=admin)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(100000000))).run(valid=True, sender=admin)

        scenario.p("4. Check that the function fails when no fund are remaining")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(100000000))).run(valid=False, sender=admin)

        scenario.p("5. Check offchain view count_tokens returns the expected value")
        scenario.verify(c1.count_tokens() == 0)

########################################################################################################################
# unit_fa2_test_transfer
########################################################################################################################
def unit_fa2_test_transfer(is_default=True):
    @sp.add_test(name="unit_fa2_test_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_transfer")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the transfer entrypoint. (Who: For all users)")
        scenario.p("This entrypoint is part of the TZIP-012 interface specification of a FA2 contract.")

        scenario.p("1. Set sale contract admin to be bob and artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Successfully mint some NFTs")
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(bob.address).run(valid=True, sender=admin)
        c1.mint(gabe.address).run(valid=True, sender=admin)
        c1.mint(gaston.address).run(valid=True, sender=admin)
        c1.mint(gabe.address).run(valid=True, sender=admin)

        scenario.p("3. Check ledger contains the expected NFTs")
        scenario.verify(c1.data.ledger[0] == alice.address)
        scenario.verify(c1.data.ledger[1] == alice.address)
        scenario.verify(c1.data.ledger[2] == alice.address)
        scenario.verify(c1.data.ledger[3] == john.address)
        scenario.verify(c1.data.ledger[4] == john.address)
        scenario.verify(c1.data.ledger[5] == john.address)
        scenario.verify(c1.data.ledger[6] == john.address)
        scenario.verify(c1.data.ledger[7] == alice.address)
        scenario.verify(c1.data.ledger[8] == bob.address)
        scenario.verify(c1.data.ledger[9] == gabe.address)
        scenario.verify(c1.data.ledger[10] == gaston.address)
        scenario.verify(c1.data.ledger[11] == gabe.address)

        scenario.p("4. Set the contract in pause using the set_pause entrypoint")
        c1.set_pause(True).run(valid=True, sender=admin)

        transfer1 = sp.record(to_=chris.address, token_id=0, amount=1)
        source1 = sp.record(from_=alice.address, txs=sp.list({transfer1}))

        scenario.p("5. Check transfer is not possible when contract is in pause")
        c1.transfer(sp.list({source1})).run(valid=False, sender=alice)

        scenario.p("6. Remove pause")
        c1.set_pause(False).run(valid=True, sender=admin)

        scenario.p("7. Make a successful transfer and check the ledger is as expected")
        c1.transfer(sp.list({source1})).run(valid=True, sender=alice)

        scenario.p("8. Check ledger contains the expected NFTs")
        scenario.verify(c1.data.ledger[0] == chris.address)
        scenario.verify(c1.data.ledger[1] == alice.address)
        scenario.verify(c1.data.ledger[2] == alice.address)
        scenario.verify(c1.data.ledger[3] == john.address)
        scenario.verify(c1.data.ledger[4] == john.address)
        scenario.verify(c1.data.ledger[5] == john.address)
        scenario.verify(c1.data.ledger[6] == john.address)
        scenario.verify(c1.data.ledger[7] == alice.address)
        scenario.verify(c1.data.ledger[8] == bob.address)
        scenario.verify(c1.data.ledger[9] == gabe.address)
        scenario.verify(c1.data.ledger[10] == gaston.address)
        scenario.verify(c1.data.ledger[11] == gabe.address)

        transfer2 = sp.record(to_=alice.address, token_id=0, amount=2)
        source2 = sp.record(from_=chris.address, txs=sp.list({transfer2}))

        scenario.p("9. Check not more than on token_id can be transferred (it is an NFT)")
        c1.transfer(sp.list({source2})).run(valid=False, sender=chris)

        scenario.p("10. Check only owners when no operators are defined can transfer their NFTs. Even admins can't.")
        c1.transfer(sp.list({source2})).run(valid=False, sender=bob)
        c1.transfer(sp.list({source2})).run(valid=False, sender=john)
        c1.transfer(sp.list({source2})).run(valid=False, sender=gabe)
        c1.transfer(sp.list({source2})).run(valid=False, sender=alice)
        c1.transfer(sp.list({source2})).run(valid=False, sender=admin)

        scenario.p("11. Make a bunch of successful transfers and check the ledger is as expected")
        transfer3 = sp.record(to_=john.address, token_id=0, amount=1)
        transfer4 = sp.record(to_=chris.address, token_id=1, amount=1)
        transfer5 = sp.record(to_=chris.address, token_id=2, amount=1)
        transfer6 = sp.record(to_=bob.address, token_id=3, amount=1)
        transfer7 = sp.record(to_=alice.address, token_id=4, amount=1)
        transfer8 = sp.record(to_=alice.address, token_id=5, amount=1)
        transfer9 = sp.record(to_=gabe.address, token_id=6, amount=1)
        transfer10 = sp.record(to_=chris.address, token_id=7, amount=1)
        transfer11 = sp.record(to_=gaston.address, token_id=8, amount=1)
        transfer12 = sp.record(to_=gabe.address, token_id=9, amount=1)
        transfer13 = sp.record(to_=chris.address, token_id=10, amount=1)
        transfer14 = sp.record(to_=john.address, token_id=11, amount=1)

        source3 = sp.record(from_=chris.address, txs=sp.list({transfer3}))
        source4 = sp.record(from_=alice.address, txs=sp.list({transfer4, transfer5, transfer10}))
        source5 = sp.record(from_=john.address, txs=sp.list({transfer6, transfer7, transfer8, transfer9}))
        source6 = sp.record(from_=bob.address, txs=sp.list({transfer11}))
        source7 = sp.record(from_=gabe.address, txs=sp.list({transfer12, transfer14}))
        source8 = sp.record(from_=gaston.address, txs=sp.list({transfer13}))

        c1.transfer(sp.list({source3})).run(valid=True, sender=chris)
        c1.transfer(sp.list({source4})).run(valid=True, sender=alice)
        c1.transfer(sp.list({source5})).run(valid=True, sender=john)
        c1.transfer(sp.list({source6})).run(valid=True, sender=bob)
        c1.transfer(sp.list({source7})).run(valid=True, sender=gabe)
        c1.transfer(sp.list({source8})).run(valid=True, sender=gaston)

        scenario.verify(c1.data.ledger[0] == john.address)
        scenario.verify(c1.data.ledger[1] == chris.address)
        scenario.verify(c1.data.ledger[2] == chris.address)
        scenario.verify(c1.data.ledger[3] == bob.address)
        scenario.verify(c1.data.ledger[4] == alice.address)
        scenario.verify(c1.data.ledger[5] == alice.address)
        scenario.verify(c1.data.ledger[6] == gabe.address)
        scenario.verify(c1.data.ledger[7] == chris.address)
        scenario.verify(c1.data.ledger[8] == gaston.address)
        scenario.verify(c1.data.ledger[9] == gabe.address)
        scenario.verify(c1.data.ledger[10] == chris.address)
        scenario.verify(c1.data.ledger[11] == john.address)

########################################################################################################################
# unit_fa2_test_update_operators
########################################################################################################################
def unit_fa2_test_update_operators(is_default=True):
    @sp.add_test(name="unit_fa2_test_update_operators", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_update_operators")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the update_operators entrypoint. (Who: For all users)")
        scenario.p("This entrypoint is part of the TZIP-012 interface specification of a FA2 contract.")

        scenario.p("1. Set sale contract admin to be bob and artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Successfully mint two NFT with alice account")
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)

        scenario.p("3. Check the ledger contains the expected NFTs")
        scenario.verify(c1.data.ledger[0] == alice.address)
        scenario.verify(c1.data.ledger[1] == alice.address)

        transfer1 = sp.record(to_=chris.address, token_id=0, amount=1)
        source1 = sp.record(from_=alice.address, txs=sp.list({transfer1}))

        scenario.p("4. Check admin cannot transfer the NFTs owned by alice")
        c1.transfer(sp.list({source1})).run(valid=False, sender=admin)

        add1 = sp.variant('add_operator', sp.record(owner=alice.address, operator=admin.address, token_id=0))
        add2 = sp.variant('add_operator', sp.record(owner=alice.address, operator=john.address, token_id=1))

        scenario.p("5. Check admin cannot become operator of a NFT he doesn't own by himself")
        c1.update_operators(sp.list({add1})).run(valid=False, sender=admin)

        scenario.p("6. Check john cannot become operator of a NFT he doesn't own by himself")
        c1.update_operators(sp.list({add2})).run(valid=False, sender=john)
        c1.transfer(sp.list({source1})).run(valid=False, sender=admin)

        scenario.p("7. Check that alice can add both john operator of NFT 1 and admin operator of NFT 0 in one call")
        c1.update_operators(sp.list({add1, add2})).run(valid=True, sender=alice)

        scenario.p("8. Check now that admin and john can transfer NFTs where they have been added as operators")
        transfer2 = sp.record(to_=chris.address, token_id=1, amount=1)
        source2 = sp.record(from_=alice.address, txs=sp.list({transfer2}))
        c1.transfer(sp.list({source1})).run(valid=False, sender=john)
        c1.transfer(sp.list({source1})).run(valid=True, sender=admin)
        c1.transfer(sp.list({source2})).run(valid=False, sender=admin)
        c1.transfer(sp.list({source2})).run(valid=True, sender=john)

        scenario.p("9. Send back the NFTs to alice")
        transfer3 = sp.record(to_=alice.address, token_id=0, amount=1)
        source3 = sp.record(from_=chris.address, txs=sp.list({transfer3}))
        c1.transfer(sp.list({source3})).run(valid=True, sender=chris)


        c1.transfer(sp.list({source1})).run(valid=True, sender=admin)

        scenario.p("10. Check that after been removed as operator, admin and john cannot transfer these NFTs anymore")
        scenario.p("11. Check alice can still transfer her NFTs")
        c1.transfer(sp.list({source3})).run(valid=True, sender=chris)

        add3 = sp.variant('remove_operator', sp.record(owner=alice.address, operator=admin.address, token_id=0))
        c1.update_operators(sp.list({add3})).run(valid=False, sender=john)

        scenario.p("12. Check alice can still transfer her NFTs")
        c1.update_operators(sp.list({add3})).run(valid=True, sender=alice)

        # Admin is not operator anymore
        c1.transfer(sp.list({source1})).run(valid=False, sender=admin)
        # Alice can still transfer her token
        c1.transfer(sp.list({source1})).run(valid=True, sender=alice)

########################################################################################################################
# unit_fa2_test_token_metadata_storage
########################################################################################################################
def unit_fa2_test_token_metadata_storage(is_default=True):
    @sp.add_test(name="unit_fa2_test_token_metadata_storage", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_token_metadata_storage")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the token_metadata storage.")

        scenario.p("1. Set sale contract admin to be bob and artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Successfully mint NFTs")
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)

        scenario.p("3. Check token_metadata storage contains expected values for various NFTs")
        scenario.verify(c1.data.token_metadata.contains(0))
        id = sp.fst(c1.data.token_metadata[0])
        info = sp.snd(c1.data.token_metadata[0])
        scenario.verify(id == 0)

        scenario.verify_equal(info[NFT.ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[NFT.DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2"))
        scenario.verify_equal(info[NFT.THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"))
        scenario.verify_equal(info[NFT.ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 3, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(info[NFT.REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(info[NFT.WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[NFT.WHAT3WORDID_METADATA], sp.utils.bytes_of_string("0"))
        scenario.verify_equal(info[NFT.NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #0"'))
        scenario.verify_equal(info[NFT.FORMATS_METADATA], TestHelper.format_helper("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1",
                                                                                   "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2",
                                                                                   "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3",
                                                                                   ARTIFACT_FILE_SIZE,
                                                                                   DISPLAY_FILE_SIZE,
                                                                                   THUMBNAIL_FILE_SIZE))
        scenario.verify_equal(info[NFT.SYMBOL_METADATA], c1.symbol)
        scenario.verify_equal(info[NFT.ATTRIBUTES_METADATA], c1.attributes_generic)
        scenario.verify_equal(info[NFT.DECIMALS_METADATA], sp.utils.bytes_of_string(NFT.DECIMALS))
        scenario.verify_equal(info[NFT.LANGUAGE_METADATA], c1.language)
        scenario.verify_equal(info[NFT.DESCRIPTION_METADATA], c1.description)
        scenario.verify_equal(info[NFT.RIGHTS_METADATA], c1.rights)
        scenario.verify_equal(info[NFT.ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string(NFT.ISTRANSFERABLE))
        scenario.verify_equal(info[NFT.ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string(NFT.ISBOOLEANAMOUNT))
        scenario.verify_equal(info[NFT.SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string(NFT.SHOULDPREFERSYMBOL))
        scenario.verify_equal(info[NFT.CREATORS_METADATA], c1.creators)
        scenario.verify_equal(info[NFT.PROJECTNAME_METADATA], c1.project_name)

        for j in range(0, 50):
            c1.mint(alice.address).run(valid=True, sender=admin)

        scenario.verify(c1.data.token_metadata.contains(49))
        id = sp.fst(c1.data.token_metadata[49])
        info = sp.snd(c1.data.token_metadata[49])
        scenario.verify(id == 49)

        scenario.verify_equal(info[NFT.ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[NFT.DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2"))
        scenario.verify_equal(info[NFT.THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"))
        scenario.verify_equal(info[NFT.ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 3, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(info[NFT.REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(info[NFT.NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(info[NFT.WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[NFT.WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(info[NFT.FORMATS_METADATA], TestHelper.format_helper("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1",
                                                                                   "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2",
                                                                                   "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3",
                                                                                   ARTIFACT_FILE_SIZE,
                                                                                   DISPLAY_FILE_SIZE,
                                                                                   THUMBNAIL_FILE_SIZE))
        scenario.verify_equal(info[NFT.SYMBOL_METADATA], c1.symbol)
        scenario.verify_equal(info[NFT.ATTRIBUTES_METADATA], c1.attributes_generic)
        scenario.verify_equal(info[NFT.DECIMALS_METADATA], sp.utils.bytes_of_string(NFT.DECIMALS))
        scenario.verify_equal(info[NFT.LANGUAGE_METADATA], c1.language)
        scenario.verify_equal(info[NFT.DESCRIPTION_METADATA], c1.description)
        scenario.verify_equal(info[NFT.RIGHTS_METADATA], c1.rights)
        scenario.verify_equal(info[NFT.ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string(NFT.ISTRANSFERABLE))
        scenario.verify_equal(info[NFT.ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string(NFT.ISBOOLEANAMOUNT))
        scenario.verify_equal(info[NFT.SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string(NFT.SHOULDPREFERSYMBOL))
        scenario.verify_equal(info[NFT.CREATORS_METADATA], c1.creators)
        scenario.verify_equal(info[NFT.PROJECTNAME_METADATA], c1.project_name)

        artifact_size_1 = "400001"
        display_size_1 = "100001"
        thumbnail_size_1 = "20001"
        record1 = sp.record(artifact_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"),
                            display_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"),
                            thumbnail_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"),
                            attributes=c1.attributes_generic,
                            artifact_size=sp.utils.bytes_of_string(artifact_size_1),
                            display_size=sp.utils.bytes_of_string(display_size_1),
                            thumbnail_size=sp.utils.bytes_of_string(thumbnail_size_1))
        list1 = sp.list({sp.pair(49, record1)})
        c1.update_artwork_data(list1).run(valid=True, sender=admin)

        scenario.verify(c1.data.token_metadata.contains(49))
        id = sp.fst(c1.data.token_metadata[49])
        info = sp.snd(c1.data.token_metadata[49])
        scenario.verify(id == 49)
        scenario.verify_equal(info[NFT.ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify_equal(info[NFT.DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify_equal(info[NFT.THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify_equal(info[NFT.ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 3, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(info[NFT.REVEALED_METADATA], sp.utils.bytes_of_string('true'))
        scenario.verify_equal(info[NFT.NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(info[NFT.WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[NFT.WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(info[NFT.FORMATS_METADATA], TestHelper.format_helper("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11",
                                                                                   "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21",
                                                                                   "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31",
                                                                                   artifact_size_1, display_size_1, thumbnail_size_1))
        scenario.verify_equal(info[NFT.SYMBOL_METADATA], c1.symbol)
        scenario.verify_equal(info[NFT.ATTRIBUTES_METADATA], c1.attributes_generic)
        scenario.verify_equal(info[NFT.DECIMALS_METADATA], sp.utils.bytes_of_string(NFT.DECIMALS))
        scenario.verify_equal(info[NFT.LANGUAGE_METADATA], c1.language)
        scenario.verify_equal(info[NFT.DESCRIPTION_METADATA], c1.description)
        scenario.verify_equal(info[NFT.RIGHTS_METADATA], c1.rights)
        scenario.verify_equal(info[NFT.ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string(NFT.ISTRANSFERABLE))
        scenario.verify_equal(info[NFT.ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string(NFT.ISBOOLEANAMOUNT))
        scenario.verify_equal(info[NFT.SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string(NFT.SHOULDPREFERSYMBOL))
        scenario.verify_equal(info[NFT.CREATORS_METADATA], c1.creators)
        scenario.verify_equal(info[NFT.PROJECTORACLEURI_METADATA], sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"))
        scenario.verify_equal(info[NFT.PROJECTNAME_METADATA], c1.project_name)


########################################################################################################################
# unit_fa2_test_token_metadata_offchain
########################################################################################################################
def unit_fa2_test_token_metadata_offchain(is_default=True):
    @sp.add_test(name="unit_fa2_test_token_metadata_offchain", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_token_metadata_offchain")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the token_metadata offchain view entrypoint.")
        scenario.p("This view is used to retrieve the token metadata of onegiven NFT. These offchain views functions are less sensitive as they can be replaced even after the contract has been deployed (the code is stored in an ipfs file).")

        scenario.p("1. Set sale contract admin to be bob and artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Successfully mint NFTs")
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)

        scenario.p("3. Check token_metadata returns the expected values for various NFTs")
        metadata_pair = c1.token_metadata(0)
        scenario.verify(sp.fst(metadata_pair) == 0)
        metadata = sp.snd(metadata_pair)

        scenario.verify_equal(metadata[NFT.ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[NFT.DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2"))
        scenario.verify_equal(metadata[NFT.THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"))
        scenario.verify_equal(metadata[NFT.ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 3, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(metadata[NFT.REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(metadata[NFT.WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[NFT.WHAT3WORDID_METADATA], sp.utils.bytes_of_string("0"))
        scenario.verify_equal(metadata[NFT.NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #0"'))
        scenario.verify_equal(metadata[NFT.FORMATS_METADATA], TestHelper.format_helper("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1",
                                                                                       "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2",
                                                                                       "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3",
                                                                                       ARTIFACT_FILE_SIZE,
                                                                                       DISPLAY_FILE_SIZE,
                                                                                       THUMBNAIL_FILE_SIZE))
        scenario.verify_equal(metadata[NFT.SYMBOL_METADATA], c1.symbol)
        scenario.verify_equal(metadata[NFT.ATTRIBUTES_METADATA], c1.attributes_generic)
        scenario.verify_equal(metadata[NFT.DECIMALS_METADATA], sp.utils.bytes_of_string(NFT.DECIMALS))
        scenario.verify_equal(metadata[NFT.LANGUAGE_METADATA], c1.language)
        scenario.verify_equal(metadata[NFT.DESCRIPTION_METADATA], c1.description)
        scenario.verify_equal(metadata[NFT.RIGHTS_METADATA], c1.rights)
        scenario.verify_equal(metadata[NFT.ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string(NFT.ISTRANSFERABLE))
        scenario.verify_equal(metadata[NFT.ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string(NFT.ISBOOLEANAMOUNT))
        scenario.verify_equal(metadata[NFT.SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string(NFT.SHOULDPREFERSYMBOL))
        scenario.verify_equal(metadata[NFT.CREATORS_METADATA], c1.creators)
        scenario.verify_equal(metadata[NFT.PROJECTNAME_METADATA], c1.project_name)

        for j in range(0, 50):
            c1.mint(alice.address).run(valid=True, sender=admin)

        metadata_pair = c1.token_metadata(49)
        scenario.verify(sp.fst(metadata_pair) == 49)
        metadata = sp.snd(metadata_pair)
        scenario.verify_equal(metadata[NFT.ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[NFT.DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2"))
        scenario.verify_equal(metadata[NFT.THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"))
        scenario.verify_equal(metadata[NFT.ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 3, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(metadata[NFT.REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(metadata[NFT.NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(metadata[NFT.WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[NFT.WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(metadata[NFT.FORMATS_METADATA], TestHelper.format_helper("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1",
                                                                                       "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD2",
                                                                                       "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3",
                                                                                       ARTIFACT_FILE_SIZE,
                                                                                       DISPLAY_FILE_SIZE,
                                                                                       THUMBNAIL_FILE_SIZE))
        scenario.verify_equal(metadata[NFT.SYMBOL_METADATA], c1.symbol)
        scenario.verify_equal(metadata[NFT.ATTRIBUTES_METADATA], c1.attributes_generic)
        scenario.verify_equal(metadata[NFT.DECIMALS_METADATA], sp.utils.bytes_of_string(NFT.DECIMALS))
        scenario.verify_equal(metadata[NFT.LANGUAGE_METADATA], c1.language)
        scenario.verify_equal(metadata[NFT.DESCRIPTION_METADATA], c1.description)
        scenario.verify_equal(metadata[NFT.RIGHTS_METADATA], c1.rights)
        scenario.verify_equal(metadata[NFT.ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string(NFT.ISTRANSFERABLE))
        scenario.verify_equal(metadata[NFT.ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string(NFT.ISBOOLEANAMOUNT))
        scenario.verify_equal(metadata[NFT.SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string(NFT.SHOULDPREFERSYMBOL))
        scenario.verify_equal(metadata[NFT.CREATORS_METADATA], c1.creators)
        scenario.verify_equal(metadata[NFT.PROJECTNAME_METADATA], c1.project_name)

        artifact_size_1 = "400001"
        display_size_1 = "100001"
        thumbnail_size_1 = "20001"
        record1 = sp.record(artifact_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"),
                            display_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"),
                            thumbnail_uri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"),
                            attributes=c1.attributes_generic,
                            artifact_size=sp.utils.bytes_of_string(artifact_size_1),
                            display_size=sp.utils.bytes_of_string(display_size_1),
                            thumbnail_size=sp.utils.bytes_of_string(thumbnail_size_1))
        list1 = sp.list({sp.pair(49, record1)})
        c1.update_artwork_data(list1).run(valid=True, sender=admin)

        metadata_pair = c1.token_metadata(49)
        scenario.verify(sp.fst(metadata_pair) == 49)
        metadata = sp.snd(metadata_pair)
        scenario.verify_equal(metadata[NFT.ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify_equal(metadata[NFT.DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify_equal(metadata[NFT.THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify_equal(metadata[NFT.ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 3, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(metadata[NFT.REVEALED_METADATA], sp.utils.bytes_of_string('true'))
        scenario.verify_equal(metadata[NFT.NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(metadata[NFT.WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[NFT.WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(metadata[NFT.FORMATS_METADATA], TestHelper.format_helper("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11",
                                                                                       "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21",
                                                                                       "ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31",
                                                                                       artifact_size_1, display_size_1, thumbnail_size_1))
        scenario.verify_equal(metadata[NFT.SYMBOL_METADATA], c1.symbol)
        scenario.verify_equal(metadata[NFT.ATTRIBUTES_METADATA], c1.attributes_generic)
        scenario.verify_equal(metadata[NFT.DECIMALS_METADATA], sp.utils.bytes_of_string(NFT.DECIMALS))
        scenario.verify_equal(metadata[NFT.LANGUAGE_METADATA], c1.language)
        scenario.verify_equal(metadata[NFT.DESCRIPTION_METADATA], c1.description)
        scenario.verify_equal(metadata[NFT.RIGHTS_METADATA], c1.rights)
        scenario.verify_equal(metadata[NFT.ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string(NFT.ISTRANSFERABLE))
        scenario.verify_equal(metadata[NFT.ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string(NFT.ISBOOLEANAMOUNT))
        scenario.verify_equal(metadata[NFT.SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string(NFT.SHOULDPREFERSYMBOL))
        scenario.verify_equal(metadata[NFT.CREATORS_METADATA], c1.creators)
        scenario.verify_equal(metadata[NFT.PROJECTORACLEURI_METADATA], sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"))
        scenario.verify_equal(metadata[NFT.PROJECTNAME_METADATA], c1.project_name)

########################################################################################################################
# unit_fa2_test_get_project_oracles_stream
########################################################################################################################
def unit_fa2_test_get_project_oracles_stream(is_default=True):
    @sp.add_test(name="unit_fa2_test_get_project_oracles_stream", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_get_project_oracles_stream")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the token_metadata get_project_oracles_stream view entrypoint.")
        scenario.p("This view is used to retrieve the oracles stream of the contract. These offchain views functions are less sensitive as they can be replaced even after the contract has been deployed (the code is stored in an ipfs file).")

        scenario.p("1. Check the storage contains the expected ceramic stream")
        scenario.verify(c1.get_project_oracles_stream() == sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"))

########################################################################################################################
# unit_fa2_test_get_voting_power
########################################################################################################################
def unit_fa2_test_get_voting_power(is_default=True):
    @sp.add_test(name="unit_fa2_test_get_voting_power", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_fa2_test_get_voting_power")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the get_voting_power onchain views.")

        scenario.p("1. Set sale contract admin to be bob and artwork admin to be john")
        c1.set_sale_contract_administrator(bob.address).run(valid=True, sender=admin)
        c1.set_artwork_administrator(john.address).run(valid=True, sender=admin)

        scenario.p("2. Get total voting power")
        total_voting_power = c1.get_total_voting_power()
        scenario.verify(total_voting_power == 0)

        scenario.p("3. Successfully mint some NFTs")
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(alice.address).run(valid=True, sender=admin)
        c1.mint(bob.address).run(valid=True, sender=admin)
        c1.mint(gabe.address).run(valid=True, sender=admin)
        c1.mint(gaston.address).run(valid=True, sender=admin)
        c1.mint(gabe.address).run(valid=True, sender=admin)

        scenario.p("4. Get total voting power")
        total_voting_power = c1.get_total_voting_power()
        scenario.verify(total_voting_power == 12)

        scenario.p("5. Get voting power per user")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, sp.level))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, sp.level))
        scenario.verify(john_voting_power == 4)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, sp.level))
        scenario.verify(bob_voting_power == 1)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, sp.level))
        scenario.verify(gabe_voting_power == 2)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, sp.level))
        scenario.verify(gaston_voting_power == 1)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, sp.level))
        scenario.verify(chris_voting_power == 0)

        scenario.p("6. Mint more token")
        old_level = sp.nat(1)
        c1.mint(alice.address).run(valid=True, sender=admin, level=sp.level + 10)
        c1.mint(gaston.address).run(valid=True, sender=admin)
        c1.mint(gabe.address).run(valid=True, sender=admin)

        scenario.p("7. Transfer some of them")
        transfer1 = sp.record(to_=bob.address, token_id=0, amount=1)
        source1 = sp.record(from_=alice.address, txs=sp.list({transfer1}))
        c1.transfer(sp.list({source1})).run(valid=True, sender=alice)
        transfer2 = sp.record(to_=chris.address, token_id=4, amount=1)
        source2 = sp.record(from_=john.address, txs=sp.list({transfer2}))
        c1.transfer(sp.list({source2})).run(valid=True, sender=john)

        scenario.p("8. Get total voting power")
        total_voting_power = c1.get_total_voting_power()
        scenario.verify(total_voting_power == 15)

        scenario.p("9. Get voting power per user for old level")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, old_level))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, old_level))
        scenario.verify(john_voting_power == 4)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, old_level))
        scenario.verify(bob_voting_power == 1)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, old_level))
        scenario.verify(gabe_voting_power == 2)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, old_level))
        scenario.verify(gaston_voting_power == 1)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, old_level))
        scenario.verify(chris_voting_power == 0)

        scenario.p("10. Get voting power per user for current level")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, sp.level))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, sp.level))
        scenario.verify(john_voting_power == 3)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, sp.level))
        scenario.verify(bob_voting_power == 2)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, sp.level))
        scenario.verify(gabe_voting_power == 3)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, sp.level))
        scenario.verify(gaston_voting_power == 2)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, sp.level))
        scenario.verify(chris_voting_power == 1)
        old_level2 = sp.nat(20)

        scenario.p("11. Mint even more token")
        old_level = sp.nat(1)
        c1.mint(alice.address).run(valid=True, sender=admin, level=sp.level + 50)
        c1.mint(gaston.address).run(valid=True, sender=admin)
        c1.mint(gaston.address).run(valid=True, sender=admin)
        c1.mint(gaston.address).run(valid=True, sender=admin)
        c1.mint(gabe.address).run(valid=True, sender=admin)
        c1.mint(gabe.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(john.address).run(valid=True, sender=admin)
        c1.mint(bob.address).run(valid=True, sender=admin)

        scenario.p("12. Get total voting power")
        total_voting_power = c1.get_total_voting_power()
        scenario.verify(total_voting_power == 24)

        scenario.p("13. Get voting power per user for old level")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, old_level))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, old_level))
        scenario.verify(john_voting_power == 4)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, old_level))
        scenario.verify(bob_voting_power == 1)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, old_level))
        scenario.verify(gabe_voting_power == 2)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, old_level))
        scenario.verify(gaston_voting_power == 1)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, old_level))
        scenario.verify(chris_voting_power == 0)

        scenario.p("14. Get voting power per user for old level 2")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, old_level2))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, old_level2))
        scenario.verify(john_voting_power == 3)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, old_level2))
        scenario.verify(bob_voting_power == 2)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, old_level2))
        scenario.verify(gabe_voting_power == 3)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, old_level2))
        scenario.verify(gaston_voting_power == 2)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, old_level2))
        scenario.verify(chris_voting_power == 1)

        scenario.p("14. Get voting power per user for current level")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, sp.level))
        scenario.verify(alice_voting_power == 5)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, sp.level))
        scenario.verify(john_voting_power == 5)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, sp.level))
        scenario.verify(bob_voting_power == 3)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, sp.level))
        scenario.verify(gabe_voting_power == 5)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, sp.level))
        scenario.verify(gaston_voting_power == 5)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, sp.level))
        scenario.verify(chris_voting_power == 1)

        scenario.p("15. Transfer all tokens")
        t1 = sp.record(to_=bob.address, token_id=1, amount=1)
        t2 = sp.record(to_=bob.address, token_id=2, amount=1)
        t7 = sp.record(to_=john.address, token_id=7, amount=1)
        t12 = sp.record(to_=gabe.address, token_id=12, amount=1)
        t15 = sp.record(to_=chris.address, token_id=15, amount=1)
        alice_transfer = sp.record(from_=alice.address, txs=sp.list({t1, t2, t7, t12, t15}))

        t3 = sp.record(to_=alice.address, token_id=3, amount=1)
        t5 = sp.record(to_=chris.address, token_id=5, amount=1)
        t6 = sp.record(to_=bob.address, token_id=6, amount=1)
        t21 = sp.record(to_=gabe.address, token_id=21, amount=1)
        t22 = sp.record(to_=gabe.address, token_id=22, amount=1)
        john_transfer = sp.record(from_=john.address, txs=sp.list({t3, t5, t6, t21, t22}))

        t0 = sp.record(to_=chris.address, token_id=0, amount=1)
        t8 = sp.record(to_=gaston.address, token_id=8, amount=1)
        t23 = sp.record(to_=chris.address, token_id=23, amount=1)
        bob_transfer = sp.record(from_=bob.address, txs=sp.list({t0, t8, t23}))

        t9 = sp.record(to_=bob.address, token_id=9, amount=1)
        t11 = sp.record(to_=john.address, token_id=11, amount=1)
        t14 = sp.record(to_=alice.address, token_id=14, amount=1)
        t19 = sp.record(to_=chris.address, token_id=19, amount=1)
        t20 = sp.record(to_=chris.address, token_id=20, amount=1)
        gabe_transfer = sp.record(from_=gabe.address, txs=sp.list({t9, t11, t14, t19, t20}))

        t10 = sp.record(to_=bob.address, token_id=10, amount=1)
        t13 = sp.record(to_=gabe.address, token_id=13, amount=1)
        t16 = sp.record(to_=chris.address, token_id=16, amount=1)
        t17 = sp.record(to_=bob.address, token_id=17, amount=1)
        t18 = sp.record(to_=alice.address, token_id=18, amount=1)
        gaston_transfer = sp.record(from_=gaston.address, txs=sp.list({t10, t13, t16, t17, t18}))

        t4 = sp.record(to_=alice.address, token_id=4, amount=1)
        chris_transfer = sp.record(from_=chris.address, txs=sp.list({t4}))

        c1.transfer(sp.list({alice_transfer})).run(valid=True, sender=alice, level=sp.level + 100)
        c1.transfer(sp.list({john_transfer})).run(valid=True, sender=john)
        c1.transfer(sp.list({bob_transfer})).run(valid=True, sender=bob)
        c1.transfer(sp.list({gabe_transfer})).run(valid=True, sender=gabe)
        c1.transfer(sp.list({gaston_transfer})).run(valid=True, sender=gaston)
        c1.transfer(sp.list({chris_transfer})).run(valid=True, sender=chris)
        old_level3 = 80

        scenario.p("16. Get total voting power")
        total_voting_power = c1.get_total_voting_power()
        scenario.verify(total_voting_power == 24)

        scenario.p("17. Get voting power per user for old level")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, old_level))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, old_level))
        scenario.verify(john_voting_power == 4)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, old_level))
        scenario.verify(bob_voting_power == 1)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, old_level))
        scenario.verify(gabe_voting_power == 2)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, old_level))
        scenario.verify(gaston_voting_power == 1)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, old_level))
        scenario.verify(chris_voting_power == 0)

        scenario.p("18. Get voting power per user for old level 2")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, old_level2))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, old_level2))
        scenario.verify(john_voting_power == 3)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, old_level2))
        scenario.verify(bob_voting_power == 2)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, old_level2))
        scenario.verify(gabe_voting_power == 3)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, old_level2))
        scenario.verify(gaston_voting_power == 2)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, old_level2))
        scenario.verify(chris_voting_power == 1)

        scenario.p("18. Get voting power per user for old_level3")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, old_level3))
        scenario.verify(alice_voting_power == 5)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, old_level3))
        scenario.verify(john_voting_power == 5)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, old_level3))
        scenario.verify(bob_voting_power == 3)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, old_level3))
        scenario.verify(gabe_voting_power == 5)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, old_level3))
        scenario.verify(gaston_voting_power == 5)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, old_level3))
        scenario.verify(chris_voting_power == 1)

        scenario.p("19. Get voting power per user for current level")
        alice_voting_power = c1.get_voting_power(sp.pair(alice.address, sp.level))
        scenario.verify(alice_voting_power == 4)
        john_voting_power = c1.get_voting_power(sp.pair(john.address, sp.level))
        scenario.verify(john_voting_power == 2)
        bob_voting_power = c1.get_voting_power(sp.pair(bob.address, sp.level))
        scenario.verify(bob_voting_power == 6)
        gabe_voting_power = c1.get_voting_power(sp.pair(gabe.address, sp.level))
        scenario.verify(gabe_voting_power == 4)
        gaston_voting_power = c1.get_voting_power(sp.pair(gaston.address, sp.level))
        scenario.verify(gaston_voting_power == 1)
        chris_voting_power = c1.get_voting_power(sp.pair(chris.address, sp.level))
        scenario.verify(chris_voting_power == 7)

        scenario.p("20. Check the ledger")
        scenario.verify(c1.data.ledger[0] == chris.address)
        scenario.verify(c1.data.ledger[1] == bob.address)
        scenario.verify(c1.data.ledger[2] == bob.address)
        scenario.verify(c1.data.ledger[3] == alice.address)
        scenario.verify(c1.data.ledger[4] == alice.address)
        scenario.verify(c1.data.ledger[5] == chris.address)
        scenario.verify(c1.data.ledger[6] == bob.address)
        scenario.verify(c1.data.ledger[7] == john.address)
        scenario.verify(c1.data.ledger[8] == gaston.address)
        scenario.verify(c1.data.ledger[9] == bob.address)
        scenario.verify(c1.data.ledger[10] == bob.address)
        scenario.verify(c1.data.ledger[11] == john.address)
        scenario.verify(c1.data.ledger[12] == gabe.address)
        scenario.verify(c1.data.ledger[13] == gabe.address)
        scenario.verify(c1.data.ledger[14] == alice.address)
        scenario.verify(c1.data.ledger[15] == chris.address)
        scenario.verify(c1.data.ledger[16] == chris.address)
        scenario.verify(c1.data.ledger[17] == bob.address)
        scenario.verify(c1.data.ledger[18] == alice.address)
        scenario.verify(c1.data.ledger[19] == chris.address)
        scenario.verify(c1.data.ledger[20] == chris.address)
        scenario.verify(c1.data.ledger[21] == gabe.address)
        scenario.verify(c1.data.ledger[22] == gabe.address)
        scenario.verify(c1.data.ledger[23] == chris.address)

unit_fa2_test_initial_storage()
unit_fa2_test_mint()
unit_fa2_test_mint_max()
unit_fa2_test_set_administrator()
unit_fa2_test_set_sale_contract_administrator()
unit_fa2_test_set_artwork_administrator()
unit_fa2_test_set_pause()
unit_fa2_test_update_artwork_data()
unit_fa2_test_mutez_transfer()
unit_fa2_test_set_royalties()
unit_fa2_test_transfer()
unit_fa2_test_update_operators()
unit_fa2_test_token_metadata_storage()
unit_fa2_test_token_metadata_offchain()
unit_fa2_test_get_project_oracles_stream()
unit_fa2_test_get_voting_power()
