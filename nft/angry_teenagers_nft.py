import smartpy as sp

Error = sp.io.import_script_from_url("file:angry_teenagers_errors.py")

########################################################################################################################
########################################################################################################################
# Types definition
########################################################################################################################
##################################################################################################################
TOKEN_ID = sp.TNat
SQUARE_SET_NFT_ID = sp.TNat
BALANCE_OF_REQUEST_TYPE = sp.TRecord(owner=sp.TAddress, token_id=TOKEN_ID).layout(("owner", "token_id"))
BALANCE_OF_RESPONSE_TYPE = sp.TList(sp.TRecord(request=BALANCE_OF_REQUEST_TYPE, balance=sp.TNat).layout(("request", "balance")))
BALANCE_OF_FUNCTION_TYPE = sp.TRecord(callback=sp.TContract(BALANCE_OF_RESPONSE_TYPE), requests=sp.TList(BALANCE_OF_REQUEST_TYPE)).layout(("requests", "callback"))
TRANSFER_TX_TYPE = sp.TRecord(to_=sp.TAddress, token_id=TOKEN_ID, amount=sp.TNat).layout(("to_", ("token_id", "amount")))
TRANSFER_TYPE = sp.TRecord(from_=sp.TAddress, txs=sp.TList(TRANSFER_TX_TYPE)).layout(("from_", "txs"))
TRANSFER_FUNCTION_TYPE = sp.TList(TRANSFER_TYPE)
OPERATOR_TYPE = sp.TRecord(owner=sp.TAddress, operator=sp.TAddress, token_id=TOKEN_ID).layout(("owner", ("operator", "token_id")))
ARTWORKS_CONTAINER_FUNCTION_TYPE = sp.TRecord(artifactUri=sp.TBytes, displayUri=sp.TBytes, thumbnailUri=sp.TBytes, attributesJSonString=sp.TBytes)
UPDATE_ARTWORK_METADATA_FUNCTION_TYPE = sp.TList(sp.TPair(TOKEN_ID, ARTWORKS_CONTAINER_FUNCTION_TYPE))

BALANCE_RECORD_TYPE = sp.TMap(sp.TNat, sp.TNat)

########################################################################################################################
########################################################################################################################
# Constants
########################################################################################################################
##################################################################################################################
NAME_METADATA = "name"
SYMBOL_METADATA = "symbol"
DECIMALS_METADATA = "decimals"
LANGUAGE_METADATA = "language"
DESCRIPTION_METADATA = "description"
DATE_METADATA = "date"
ARTIFACTURI_METADATA = "artifactUri"
DISPLAYURI_METADATA = "displayUri"
THUMBNAILURI_METADATA = "thumbnailUri"
ATTRIBUTES_METADATA = "attributes"
RIGHTS_METADATA = "rights"
ISTRANSFERABLE_METADATA = "isTransferable"
ISBOOLEANAMOUNT_METADATA = "isBooleanAmount"
SHOULDPREFERSYMBOL_METADATA = "shouldPreferSymbol"
CREATORS_METADATA = "creators"
PROJECTNAME_METADATA = "projectName"
FORMATS_METADATA = "formats"
WHAT3WORDSFILE_METADATA = "what3wordsFile"
WHAT3WORDID_METADATA = "what3wordsId"
REVEALED_METADATA = "revealed"
ROYALTIES_METADATA = "royalties"
PROJECTORACLEURI_METADATA = "projectOraclesUri"

########################################################################################################################
########################################################################################################################
# Classes
########################################################################################################################
##################################################################################################################
## The link between operators and the addresses they operate is kept
## in a *lazy set* of `(owner × operator × token-id)` values.
##
## A lazy set is a big-map whose keys are the elements of the set and
## values are all `Unit`.
class Operator_set:
    def make(self):
        return sp.big_map(tkey=OPERATOR_TYPE, tvalue = sp.TUnit)

    def make_key(self, owner, operator, token_id):
        metakey = sp.record(owner=owner,
                            operator=operator,
                            token_id=token_id)
        metakey = sp.set_type_expr(metakey, OPERATOR_TYPE)
        return metakey

    def add(self, set, owner, operator, token_id):
        set[self.make_key(owner, operator, token_id)] = sp.unit
    def remove(self, set, owner, operator, token_id):
        del set[self.make_key(owner, operator, token_id)]
    def is_member(self, set, owner, operator, token_id):
        return set.contains(self.make_key(owner, operator, token_id))

class AngryTeenagers(sp.Contract):
    def __init__(self, administrator, royalties_bytes, metadata, generic_image_ipfs, generic_image_ipfs_thumbnail, project_oracles_stream, what3words_file_ipfs, total_supply):
        self.operator_set = Operator_set()

        self.init(
            ledger = sp.big_map(tkey=TOKEN_ID, tvalue=sp.TAddress),
            operators=self.operator_set.make(),

            voting_power = sp.big_map(tkey=sp.TAddress, tvalue=BALANCE_RECORD_TYPE),

            # Administrator
            administrator=administrator,
            sale_contract_administrator=administrator,
            artwork_administrator=administrator,

            # Pause
            paused=sp.bool(False),

            # Minted tokens
            minted_tokens = sp.nat(0),

            # What3words set file in ipfs
            what3words_file_ipfs=what3words_file_ipfs,

            # Total Max supply -- !!! Must match the number of line in the what3words file in ipfs
            total_supply=total_supply,

            # Token metadata
            token_metadata = sp.big_map(l={}, tkey=TOKEN_ID, tvalue=sp.TPair(TOKEN_ID, sp.TMap(sp.TString, sp.TBytes))),
            extra_token_metadata = sp.big_map(l={}, tkey=TOKEN_ID, tvalue=sp.TRecord(token_id =TOKEN_ID, token_info = sp.TMap(sp.TString, sp.TBytes))),

            generic_image_ipfs = generic_image_ipfs,
            generic_image_ipfs_thumbnail = generic_image_ipfs_thumbnail,

            project_oracles_stream = project_oracles_stream,

            royalties = royalties_bytes,

            metadata = metadata
        )

        list_of_views = [
             self.get_balance
             , self.does_token_exist
             , self.count_tokens
             , self.all_tokens
             , self.get_user_tokens
             , self.is_operator
             , self.total_supply
             , self.token_metadata
             , self.get_all_non_revealed_token
        ]

        metadata_base = {
             "version": "1.0"
             , "description": (
                     "Angry Teenagers... on the Tezos blockchain."
        )
             , "interfaces": ["TZIP-012", "TZIP-016", "TZIP-021"]
             , "authors": [
                 "EcoMint LTD"
            ]
             , "homepage": "https://www.angryteenagers.xyz"
             , "views": list_of_views
             , "permissions": {
                 "operator":
                     "owner-or-operator-transfer"
                 , "receiver": "owner-no-hook"
                 , "sender": "owner-no-hook"
            }
        }
        self.init_metadata("metadata_base", metadata_base)

########################################################################################################################
# FA2 standard interface
########################################################################################################################
    @sp.entry_point
    def balance_of(self, params):
        # paused may mean that balances are meaningless:
        sp.verify( ~self.is_paused(), message = Error.ErrorMessage.unauthorized_user())
        sp.set_type(params, BALANCE_OF_FUNCTION_TYPE)
        def f_process_request(req):
            sp.verify(self.data.ledger.contains(req.token_id), message=Error.ErrorMessage.token_undefined())
            sp.if self.data.ledger[req.token_id] == req.owner:
                sp.result(sp.record(
                        request = sp.record(
                            owner = sp.set_type_expr(req.owner, sp.TAddress),
                            token_id = sp.set_type_expr(req.token_id, sp.TNat)),
                        balance = 1))
            sp.else:
                sp.result(sp.record(
                    request=sp.record(
                        owner=sp.set_type_expr(req.owner, sp.TAddress),
                        token_id=sp.set_type_expr(req.token_id, sp.TNat)),
                    balance=0))

        res = sp.local("responses", params.requests.map(f_process_request))
        destination = sp.set_type_expr(params.callback, sp.TContract(BALANCE_OF_RESPONSE_TYPE))
        sp.transfer(res.value, sp.mutez(0), destination)

    @sp.entry_point
    def transfer(self, params):
        sp.verify(~self.is_paused(), message=Error.ErrorMessage.paused())
        sp.set_type(params, TRANSFER_FUNCTION_TYPE)
        sp.for transfer in params:
            current_from = transfer.from_
            sp.for tx in transfer.txs:
                sender_verify = (current_from == sp.sender)
                message = Error.ErrorMessage.not_owner()
                message = Error.ErrorMessage.not_operator()
                sender_verify |= (self.operator_set.is_member(self.data.operators,
                                                              current_from,
                                                              sp.sender,
                                                              tx.token_id))
                sp.verify(sender_verify, message=message)
                sp.verify(tx.amount == 1, Error.ErrorMessage.insufficient_balance())
                sp.verify(self.data.ledger.contains(tx.token_id), Error.ErrorMessage.token_undefined())
                sp.verify(self.data.ledger[tx.token_id] == current_from, Error.ErrorMessage.not_owner())
                self.data.ledger[tx.token_id] = tx.to_

                self.update_balance(current_from, tx.to_)

    @sp.entry_point
    def update_operators(self, params):
        sp.set_type(params, sp.TList(
            sp.TVariant(
                add_operator=OPERATOR_TYPE,
                remove_operator=OPERATOR_TYPE
            )
        ))

        sp.for update in params:
            with update.match_cases() as arg:
                with arg.match("add_operator") as upd:
                    sp.verify(
                        (upd.owner == sp.sender),
                        message=Error.ErrorMessage.not_admin_or_operator()
                    )
                    self.operator_set.add(self.data.operators,
                                          upd.owner,
                                          upd.operator,
                                          upd.token_id)
                with arg.match("remove_operator") as upd:
                    sp.verify(
                        (upd.owner == sp.sender) | self.is_administrator(sp.sender),
                        message=Error.ErrorMessage.not_admin_or_operator()
                    )
                    self.operator_set.remove(self.data.operators,
                                             upd.owner,
                                             upd.operator,
                                             upd.token_id)

########################################################################################################################
# Dedicated entry points
########################################################################################################################
    @sp.entry_point
    def mutez_transfer(self, params):
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        sp.set_type(params.destination, sp.TAddress)
        sp.set_type(params.amount, sp.TMutez)
        sp.send(params.destination, params.amount)

    @sp.entry_point
    def set_metadata(self, k, v):
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        self.data.metadata[k] = v

    @sp.entry_point
    def set_extra_token_metadata(self, tok, k2, v):
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        sp.if ~self.data.extra_token_metadata.contains(tok):
            self.data.extra_token_metadata[tok] = sp.record(token_id=tok, token_info=sp.map(l={}, tkey=sp.TString, tvalue=sp.TBytes))
        self.data.extra_token_metadata[tok].token_info[k2] = v

    @sp.entry_point
    def set_pause(self, params):
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        self.data.paused = params

    @sp.entry_point
    def set_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        self.data.administrator = params

    @sp.entry_point
    def set_sale_contract_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        self.data.sale_contract_administrator = params

    @sp.entry_point
    def set_artwork_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        self.data.artwork_administrator = params

    @sp.entry_point
    def update_artwork_data(self, params):
        sp.verify(self.is_artwork_administrator(sp.sender), message = Error.ErrorMessage.not_admin())
        sp.set_type(params, UPDATE_ARTWORK_METADATA_FUNCTION_TYPE)
        sp.for artwork_metadata in params:
            sp.verify(self.data.ledger.contains(sp.fst(artwork_metadata)), message=Error.ErrorMessage.token_undefined())
            sp.verify(self.data.token_metadata.contains(sp.fst(artwork_metadata)), Error.ErrorMessage.token_undefined())
            info = sp.snd(self.data.token_metadata[sp.fst(artwork_metadata)])
            sp.verify(info.contains(REVEALED_METADATA), Error.ErrorMessage.token_undefined())
            sp.verify(info[REVEALED_METADATA] == sp.utils.bytes_of_string("false"), Error.ErrorMessage.token_revealed())

            my_map = sp.update_map(sp.snd(self.data.token_metadata[sp.fst(artwork_metadata)]), REVEALED_METADATA, sp.some(sp.utils.bytes_of_string("true")))
            my_map = sp.update_map(my_map, ARTIFACTURI_METADATA, sp.some((sp.snd(artwork_metadata)).artifactUri))
            my_map = sp.update_map(my_map, DISPLAYURI_METADATA, sp.some((sp.snd(artwork_metadata)).displayUri))
            my_map = sp.update_map(my_map, THUMBNAILURI_METADATA, sp.some((sp.snd(artwork_metadata)).thumbnailUri))
            my_map = sp.update_map(my_map, ATTRIBUTES_METADATA, sp.some((sp.snd(artwork_metadata)).attributesJSonString))
            formats_bytes_prefix = sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"')
            formats_bytes_suffix = sp.utils.bytes_of_string('"}]')
            formats = sp.local(FORMATS_METADATA, formats_bytes_prefix + (sp.snd(artwork_metadata)).artifactUri + formats_bytes_suffix)
            my_map = sp.update_map(my_map, FORMATS_METADATA, sp.some(formats.value))

            self.data.token_metadata[sp.fst(artwork_metadata)] = sp.pair(sp.fst(artwork_metadata), my_map)


    @sp.entry_point
    def set_royalties(self, params):
        # Verify type
        sp.set_type(params, sp.TBytes)

        # Asserts
        sp.verify(self.is_administrator(sp.sender), message = Error.ErrorMessage.not_admin())

        # Set the royalties field for NFTs not minted yet
        self.data.royalties = params

        # Change already minted NFTs
        i = sp.local("i", sp.nat(0))
        sp.while i.value < self.data.minted_tokens:
            sp.verify(self.data.ledger.contains(i.value), message=Error.ErrorMessage.token_undefined())
            sp.verify(self.data.token_metadata.contains(i.value), message=Error.ErrorMessage.token_undefined())
            info = sp.snd(self.data.token_metadata[i.value])
            sp.verify(info.contains(ROYALTIES_METADATA), Error.ErrorMessage.token_undefined())

            my_map = sp.update_map(sp.snd(self.data.token_metadata[i.value]), ROYALTIES_METADATA, sp.some(params))
            self.data.token_metadata[i.value] = sp.pair(i.value, my_map)

            i.value = i.value + 1

    @sp.entry_point
    def mint(self, params):
        sp.set_type(params, sp.TAddress)
        sp.verify(self.is_sale_contract_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        # We don't check for pauseness because we're the admin.
        sp.verify(self.data.minted_tokens < self.data.total_supply, message=Error.ErrorMessage.no_land_available())

        self.data.ledger[self.data.minted_tokens] = params
        self.build_token_metadata(self.data.minted_tokens)

        self.data.minted_tokens = self.data.minted_tokens + 1

        sp.if ~self.data.voting_power.contains(params):
            self.data.voting_power[params] = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TNat)

        with sp.match_cons(self.data.voting_power[params].items().rev()) as last_balance:
            sp.verify(((sp.level == last_balance.head.key) |
                   (sp.level > last_balance.head.key)), message=Error.ErrorMessage.balance_inconsistency())
            self.data.voting_power[params][sp.level] = last_balance.head.value + 1
        sp.else:
            self.data.voting_power[params][sp.level] = 1

########################################################################################################################
# Onchain views
########################################################################################################################
    @sp.onchain_view()
    def get_voting_power(self, params):
        sp.set_type(params, sp.TPair(sp.TAddress, sp.TNat))
        address, level = sp.match_pair(params)
        sp.if ~self.data.voting_power.contains(address):
            sp.result(sp.nat(0))
        sp.else:
            sp.verify(sp.len(self.data.voting_power[address]) > 0, message=Error.ErrorMessage.balance_inconsistency())
            found = sp.local('found', sp.bool(False))
            result = sp.local('result', sp.nat(0))
            sp.for elem in self.data.voting_power[address].items().rev():
                sp.if (~(found.value)) & (elem.key <= level):
                    result.value = elem.value
                    found.value = True

            sp.if ~(found.value):
                result.value = sp.nat(0)

            sp.result(result.value)


    @sp.onchain_view()
    def get_total_voting_power(self):
        """Get how many tokens was in this FA2 contract onchain.
        """
        sp.result(self.data.minted_tokens)

########################################################################################################################
# Offchain views
########################################################################################################################
    @sp.offchain_view(pure=True)
    def count_tokens(self):
        """Get how many tokens are in this FA2 contract.
        """
        sp.result(self.data.minted_tokens)

    @sp.offchain_view(pure=True)
    def does_token_exist(self, tok):
        """Akd whether a token exists.
        """
        sp.set_type(tok, sp.TNat)
        sp.result(self.data.ledger.contains(tok))

    @sp.offchain_view(pure=True)
    def all_tokens(self):
        """Get all tokens.
        """
        sp.result(sp.range(0, self.data.minted_tokens))

    @sp.offchain_view(pure=True)
    def get_user_tokens(self, params):
        """Get user tokens.
        """
        sp.set_type(params, sp.TAddress)
        token_list = sp.local('token_list', sp.list(l={}, t=TOKEN_ID))
        i = sp.local("i", sp.nat(0))
        sp.while i.value < self.data.minted_tokens:
            sp.verify(self.data.ledger.contains(i.value), message=Error.ErrorMessage.token_undefined())
            sp.if self.data.ledger[i.value] == params:
                token_list.value.push(i.value)
            i.value = i.value + 1
        sp.result(token_list.value)

    @sp.offchain_view(pure=True)
    def get_all_non_revealed_token(self):
        """Get all non-revealed token.
        """
        token_list = sp.local('token_list', sp.list(l={}, t=TOKEN_ID))
        i = sp.local("i", sp.nat(0))
        sp.while i.value < self.data.minted_tokens:
            sp.verify(self.data.token_metadata.contains(i.value), message=Error.ErrorMessage.token_undefined())
            sp.if (sp.snd(self.data.token_metadata[i.value]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"):
                token_list.value.push(i.value)
            i.value = i.value + 1
        sp.result(token_list.value)

    @sp.offchain_view(pure=True)
    def total_supply(self, tok):
        """Get the total supply.
        """
        sp.set_type(tok, sp.TNat)
        sp.result(self.data.total_supply)

    @sp.offchain_view(pure=True)
    def is_operator(self, query):
        """Return whether an address is operator of a token.
        """
        sp.set_type(query,
                    sp.TRecord(token_id=sp.TNat,
                               owner=sp.TAddress,
                               operator=sp.TAddress).layout(
                        ("owner", ("operator", "token_id"))))
        sp.result(
            self.operator_set.is_member(self.data.operators,
                                        query.owner,
                                        query.operator,
                                        query.token_id)
        )

    @sp.offchain_view(pure=True)
    def get_balance(self, req):
        """Get balance as defined in TZIP-012.
        """
        sp.set_type(
            req, sp.TRecord(
                owner=sp.TAddress,
                token_id=sp.TNat
            ).layout(("owner", "token_id")))
        sp.verify(self.data.ledger.contains(req.token_id), message=Error.ErrorMessage.token_undefined())
        sp.if self.data.ledger[req.token_id] == req.owner:
            sp.result(sp.nat(1))
        sp.else:
            sp.result(sp.nat(0))


    @sp.offchain_view(pure=True)
    def get_project_oracles_stream(self):
        """Get oracle stream
        """
        sp.result(self.data.project_oracles_stream)

    @sp.offchain_view(pure=True)
    def token_metadata(self, tok):
        """Get token metadata
        """
        sp.set_type(tok, sp.TNat)
        sp.verify(tok < self.data.total_supply)
        sp.verify(self.data.ledger.contains(tok), message=Error.ErrorMessage.token_undefined())
        sp.verify(self.data.token_metadata.contains(tok), message=Error.ErrorMessage.token_undefined())

        sp.result(self.data.token_metadata[tok])

########################################################################################################################
# Internal functions
########################################################################################################################
    def is_paused(self):
        return self.data.paused

    def is_administrator(self, sender):
        return sender == self.data.administrator

    def is_sale_contract_administrator(self, sender):
        return (sender == self.data.administrator) | (sender == self.data.sale_contract_administrator)

    def is_artwork_administrator(self, sender):
        return (sender == self.data.administrator) | (sender == self.data.artwork_administrator)

    def update_balance(self, sender, receiver):
        sp.verify(self.data.voting_power.contains(sender), message=Error.ErrorMessage.balance_inconsistency())
        sp.verify(sp.len(self.data.voting_power[sender]) > 0,
                  message=Error.ErrorMessage.balance_inconsistency())
        with sp.match_cons(self.data.voting_power[sender].items().rev()) as last_balance:
            sp.verify(((sp.level == last_balance.head.key) |
                       (sp.level > last_balance.head.key)), message=Error.ErrorMessage.balance_inconsistency())
            sp.verify(last_balance.head.value > 0, message=Error.ErrorMessage.balance_inconsistency())
            self.data.voting_power[sender][sp.level] = sp.is_nat(last_balance.head.value - 1).open_some()
        sp.else:
            sp.failwith(Error.ErrorMessage.balance_inconsistency())

        sp.if ~self.data.voting_power.contains(receiver):
            self.data.voting_power[receiver] = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TNat)

        with sp.match_cons(self.data.voting_power[receiver].items().rev()) as last_balance:
            sp.verify(((sp.level == last_balance.head.key) |
                   (sp.level > last_balance.head.key)), message=Error.ErrorMessage.balance_inconsistency())
            self.data.voting_power[receiver][sp.level] = last_balance.head.value + 1
        sp.else:
            self.data.voting_power[receiver][sp.level] = 1

    def build_token_metadata(self, token_id):
        # set type
        sp.set_type(token_id, sp.TNat)

        # asserts
        sp.verify(~self.data.token_metadata.contains(token_id), Error.ErrorMessage.invalid_token_metadata())

        nat_to_bytes = sp.local('nat_to_bytes', sp.map(l={sp.nat(0): sp.bytes('0x30'),
                                                          sp.nat(1): sp.bytes('0x31'),
                                                          sp.nat(2): sp.bytes('0x32'),
                                                          sp.nat(3): sp.bytes('0x33'),
                                                          sp.nat(4): sp.bytes('0x34'),
                                                          sp.nat(5): sp.bytes('0x35'),
                                                          sp.nat(6): sp.bytes('0x36'),
                                                          sp.nat(7): sp.bytes('0x37'),
                                                          sp.nat(8): sp.bytes('0x38'),
                                                          sp.nat(9): sp.bytes('0x39')}, tkey=sp.TNat,
                                                       tvalue=sp.TBytes));

        x = sp.local('x', token_id)
        token_id_string = sp.local('token_id_string', sp.bytes('0x'))
        sp.if x.value == 0:
            token_id_string.value = sp.concat([token_id_string.value, nat_to_bytes.value[0]]);
        sp.else:
            sp.while 0 < x.value:
                token_id_string.value = sp.concat([nat_to_bytes.value[x.value % 10], token_id_string.value])
                x.value //= 10

        name = sp.concat([sp.utils.bytes_of_string('"Angry Teenager #'), token_id_string.value, sp.utils.bytes_of_string('"')])

        formats_bytes_prefix = sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"')
        formats_bytes_suffix = sp.utils.bytes_of_string('"}]')
        formats = sp.local('formats', formats_bytes_prefix + self.data.generic_image_ipfs + formats_bytes_suffix)

        meta_map = sp.map(l={
            NAME_METADATA: name,
            SYMBOL_METADATA: sp.utils.bytes_of_string("ANGRY"),
            DECIMALS_METADATA: sp.utils.bytes_of_string("0"),
            LANGUAGE_METADATA: sp.utils.bytes_of_string("en-US"),
            DESCRIPTION_METADATA: sp.utils.bytes_of_string('"Angry Teenagers ... on the Tezos blockchain."'),
            DATE_METADATA: sp.pack(sp.now),
            ARTIFACTURI_METADATA: self.data.generic_image_ipfs,
            DISPLAYURI_METADATA: self.data.generic_image_ipfs,
            THUMBNAILURI_METADATA: self.data.generic_image_ipfs_thumbnail,
            ATTRIBUTES_METADATA: sp.utils.bytes_of_string('[{\"name\", \"generic\"}]'),
            RIGHTS_METADATA: sp.utils.bytes_of_string('"© 2022 EcoMint. All rights reserved."'),
            ISTRANSFERABLE_METADATA: sp.utils.bytes_of_string("true"),
            ISBOOLEANAMOUNT_METADATA: sp.utils.bytes_of_string("true"),
            SHOULDPREFERSYMBOL_METADATA: sp.utils.bytes_of_string("false"),
            CREATORS_METADATA: sp.utils.bytes_of_string('["EcoMint LTD. https://www.angryteenagers.xyz"]'),
            PROJECTNAME_METADATA: sp.utils.bytes_of_string("Project-1"),
            FORMATS_METADATA: formats.value,
            WHAT3WORDSFILE_METADATA: self.data.what3words_file_ipfs,
            WHAT3WORDID_METADATA: token_id_string.value,
            REVEALED_METADATA: sp.utils.bytes_of_string("false"),
            ROYALTIES_METADATA: self.data.royalties,
            PROJECTORACLEURI_METADATA: self.data.project_oracles_stream
        })

        self.data.token_metadata[token_id] = sp.pair(token_id, meta_map)

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

    def create_contracts(scenario, admin, john):
        c1  = AngryTeenagers(administrator=admin.address,
                           royalties_bytes=sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'),
                           metadata=sp.utils.metadata_of_url("https://example.com"),
                           generic_image_ipfs=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                           generic_image_ipfs_thumbnail=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                           project_oracles_stream=sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"),
                            what3words_file_ipfs=sp.utils.bytes_of_string(
                                "ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"),
                            total_supply=128
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
        scenario.verify(c1.data.generic_image_ipfs == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify(c1.data.generic_image_ipfs_thumbnail == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

        scenario.verify(c1.data.project_oracles_stream == sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"))

        scenario.verify(c1.data.royalties == sp.utils.bytes_of_string('{"decimals": 2, "shares": { "' + "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5" + '": 10}}'))

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
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[4]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[5]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
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
        first_new_royalties = sp.utils.bytes_of_string('{"decimals": 4, "shares": { "' + "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf6" + '": 20}}')
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
        scenario.verify(info_0[ROYALTIES_METADATA] == first_new_royalties)
        scenario.verify(info_1[ROYALTIES_METADATA] == first_new_royalties)
        scenario.verify(info_2[ROYALTIES_METADATA] == first_new_royalties)
        scenario.verify(info_3[ROYALTIES_METADATA] == first_new_royalties)

        scenario.p("6. Change again the royalties")
        second_new_royalties = sp.utils.bytes_of_string('{"decimals": 4, "shares": { "' + "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf7" + '": 30}}')
        c1.set_royalties(second_new_royalties).run(valid=True, sender=admin)

        scenario.p("7. Mint another NFTs")
        c1.mint(alice.address).run(valid=True, sender=admin)

        scenario.p("8. Verify all NFTs contain the right royalties field")
        scenario.verify(c1.data.token_metadata.contains(4))
        info_4 = sp.snd(c1.data.token_metadata[4])
        scenario.verify_equal(c1.data.royalties, second_new_royalties)
        scenario.verify(info_0[ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_1[ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_2[ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_3[ROYALTIES_METADATA] == second_new_royalties)
        scenario.verify(info_4[ROYALTIES_METADATA] == second_new_royalties)


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

        record1 = sp.record(artifactUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"),
                            displayUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"),
                            thumbnailUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"),
                            attributesJSonString=sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))
        record2 = sp.record(artifactUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"),
                            displayUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"),
                            thumbnailUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"),
                            attributesJSonString=sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))
        record3 = sp.record(artifactUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"),
                            displayUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"),
                            thumbnailUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"),
                            attributesJSonString=sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'))
        list1 = sp.list({sp.pair(1, record1), sp.pair(2, record2)})
        list2 = sp.list({sp.pair(3, record3)})

        scenario.p("1. Check that NFT cannot be revealed if they are not minted")
        c1.update_artwork_data(list1).run(valid=False, sender=admin)

        scenario.p("2. Successfully mint 4 NFTs")
        TestHelper.mint_4_tokens(scenario, c1, bob, admin, nat, john, ben, gabe)

        scenario.p("3. Check that minted NFTs are not revealed yet")
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))

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

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))

        scenario.verify((sp.snd(c1.data.token_metadata[1]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[2]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[3]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'))

        scenario.p("8. Reveal NFT 0")
        list4 = sp.list({sp.pair(0, record2)})
        c1.update_artwork_data(list4).run(valid=True, sender=gaston)

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[THUMBNAILURI_METADATA]  == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[1]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[2]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[3]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'))

        scenario.p("9. Check the function update_artwork_data cannot be called multiple times on the same NFT")
        list3 = sp.list({sp.pair(0, record2), sp.pair(2, record3), sp.pair(1, record2)})
        c1.update_artwork_data(list3).run(valid=False, sender=gaston)

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[REVEALED_METADATA] == sp.utils.bytes_of_string("true"))

        scenario.verify((sp.snd(c1.data.token_metadata[0]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[THUMBNAILURI_METADATA]  == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[0]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[1]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify((sp.snd(c1.data.token_metadata[1]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[2]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB12"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB22"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB32"))
        scenario.verify((sp.snd(c1.data.token_metadata[2]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic2\"}]'))

        scenario.verify((sp.snd(c1.data.token_metadata[3]))[ARTIFACTURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB13"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[DISPLAYURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB23"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[THUMBNAILURI_METADATA] == sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB33"))
        scenario.verify((sp.snd(c1.data.token_metadata[3]))[ATTRIBUTES_METADATA] == sp.utils.bytes_of_string('[{\"name\", \"generic3\"}]'))

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

        scenario.verify_equal(info[ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(info[DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(info[THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(info[ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(info[REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(info[WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[WHAT3WORDID_METADATA], sp.utils.bytes_of_string("0"))
        scenario.verify_equal(info[NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #0"'))
        scenario.verify_equal(info[FORMATS_METADATA], sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"}]'))
        scenario.verify_equal(info[SYMBOL_METADATA], sp.utils.bytes_of_string('ANGRY'))
        scenario.verify_equal(info[ATTRIBUTES_METADATA], sp.utils.bytes_of_string('[{\"name\", \"generic\"}]'))
        scenario.verify_equal(info[DECIMALS_METADATA], sp.utils.bytes_of_string('0'))
        scenario.verify_equal(info[LANGUAGE_METADATA], sp.utils.bytes_of_string('en-US'))
        scenario.verify_equal(info[DESCRIPTION_METADATA], sp.utils.bytes_of_string('"Angry Teenagers ... on the Tezos blockchain."'))
        scenario.verify_equal(info[RIGHTS_METADATA], sp.utils.bytes_of_string('"© 2022 EcoMint. All rights reserved."'))
        scenario.verify_equal(info[ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(info[ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(info[SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string("false"))
        scenario.verify_equal(info[CREATORS_METADATA], sp.utils.bytes_of_string('["EcoMint LTD. https://www.angryteenagers.xyz"]'))
        scenario.verify_equal(info[PROJECTNAME_METADATA], sp.utils.bytes_of_string('Project-1'))

        for j in range(0, 50):
            c1.mint(alice.address).run(valid=True, sender=admin)

        scenario.verify(c1.data.token_metadata.contains(49))
        id = sp.fst(c1.data.token_metadata[49])
        info = sp.snd(c1.data.token_metadata[49])
        scenario.verify(id == 49)

        scenario.verify_equal(info[ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(info[DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(info[THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(info[ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(info[REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(info[NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(info[WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(info[FORMATS_METADATA], sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"}]'))
        scenario.verify_equal(info[SYMBOL_METADATA], sp.utils.bytes_of_string('ANGRY'))
        scenario.verify_equal(info[ATTRIBUTES_METADATA], sp.utils.bytes_of_string('[{\"name\", \"generic\"}]'))
        scenario.verify_equal(info[DECIMALS_METADATA], sp.utils.bytes_of_string('0'))
        scenario.verify_equal(info[LANGUAGE_METADATA], sp.utils.bytes_of_string('en-US'))
        scenario.verify_equal(info[DESCRIPTION_METADATA], sp.utils.bytes_of_string('"Angry Teenagers ... on the Tezos blockchain."'))
        scenario.verify_equal(info[RIGHTS_METADATA], sp.utils.bytes_of_string('"© 2022 EcoMint. All rights reserved."'))
        scenario.verify_equal(info[ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(info[ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(info[SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string("false"))
        scenario.verify_equal(info[CREATORS_METADATA], sp.utils.bytes_of_string('["EcoMint LTD. https://www.angryteenagers.xyz"]'))
        scenario.verify_equal(info[PROJECTNAME_METADATA], sp.utils.bytes_of_string('Project-1'))

        record1 = sp.record(artifactUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"),
                            displayUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"),
                            thumbnailUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"),
                            attributesJSonString=sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))
        list1 = sp.list({sp.pair(49, record1)})
        c1.update_artwork_data(list1).run(valid=True, sender=admin)

        scenario.verify(c1.data.token_metadata.contains(49))
        id = sp.fst(c1.data.token_metadata[49])
        info = sp.snd(c1.data.token_metadata[49])
        scenario.verify(id == 49)
        scenario.verify_equal(info[ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify_equal(info[DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify_equal(info[THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify_equal(info[ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(info[REVEALED_METADATA], sp.utils.bytes_of_string('true'))
        scenario.verify_equal(info[NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(info[WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(info[WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(info[FORMATS_METADATA], sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"}]'))
        scenario.verify_equal(info[SYMBOL_METADATA], sp.utils.bytes_of_string('ANGRY'))
        scenario.verify_equal(info[ATTRIBUTES_METADATA], sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))
        scenario.verify_equal(info[DECIMALS_METADATA], sp.utils.bytes_of_string('0'))
        scenario.verify_equal(info[LANGUAGE_METADATA], sp.utils.bytes_of_string('en-US'))
        scenario.verify_equal(info[DESCRIPTION_METADATA], sp.utils.bytes_of_string('"Angry Teenagers ... on the Tezos blockchain."'))
        scenario.verify_equal(info[RIGHTS_METADATA], sp.utils.bytes_of_string('"© 2022 EcoMint. All rights reserved."'))
        scenario.verify_equal(info[ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(info[ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(info[SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string("false"))
        scenario.verify_equal(info[CREATORS_METADATA], sp.utils.bytes_of_string('["EcoMint LTD. https://www.angryteenagers.xyz"]'))
        scenario.verify_equal(info[PROJECTORACLEURI_METADATA], sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"))
        scenario.verify_equal(info[PROJECTNAME_METADATA], sp.utils.bytes_of_string('Project-1'))


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

        scenario.verify_equal(metadata[ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(metadata[DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(metadata[THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(metadata[ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(metadata[REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(metadata[WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[WHAT3WORDID_METADATA], sp.utils.bytes_of_string("0"))
        scenario.verify_equal(metadata[NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #0"'))
        scenario.verify_equal(metadata[FORMATS_METADATA], sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"}]'))
        scenario.verify_equal(metadata[SYMBOL_METADATA], sp.utils.bytes_of_string('ANGRY'))
        scenario.verify_equal(metadata[ATTRIBUTES_METADATA], sp.utils.bytes_of_string('[{\"name\", \"generic\"}]'))
        scenario.verify_equal(metadata[DECIMALS_METADATA], sp.utils.bytes_of_string('0'))
        scenario.verify_equal(metadata[LANGUAGE_METADATA], sp.utils.bytes_of_string('en-US'))
        scenario.verify_equal(metadata[DESCRIPTION_METADATA], sp.utils.bytes_of_string('"Angry Teenagers ... on the Tezos blockchain."'))
        scenario.verify_equal(metadata[RIGHTS_METADATA], sp.utils.bytes_of_string('"© 2022 EcoMint. All rights reserved."'))
        scenario.verify_equal(metadata[ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(metadata[ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(metadata[SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string("false"))
        scenario.verify_equal(metadata[CREATORS_METADATA], sp.utils.bytes_of_string('["EcoMint LTD. https://www.angryteenagers.xyz"]'))
        scenario.verify_equal(metadata[PROJECTNAME_METADATA], sp.utils.bytes_of_string('Project-1'))

        for j in range(0, 50):
            c1.mint(alice.address).run(valid=True, sender=admin)

        metadata_pair = c1.token_metadata(49)
        scenario.verify(sp.fst(metadata_pair) == 49)
        metadata = sp.snd(metadata_pair)
        scenario.verify_equal(metadata[ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(metadata[DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(metadata[THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"))
        scenario.verify_equal(metadata[ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(metadata[REVEALED_METADATA], sp.utils.bytes_of_string('false'))
        scenario.verify_equal(metadata[NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(metadata[WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(metadata[FORMATS_METADATA], sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"}]'))
        scenario.verify_equal(metadata[SYMBOL_METADATA], sp.utils.bytes_of_string('ANGRY'))
        scenario.verify_equal(metadata[ATTRIBUTES_METADATA], sp.utils.bytes_of_string('[{\"name\", \"generic\"}]'))
        scenario.verify_equal(metadata[DECIMALS_METADATA], sp.utils.bytes_of_string('0'))
        scenario.verify_equal(metadata[LANGUAGE_METADATA], sp.utils.bytes_of_string('en-US'))
        scenario.verify_equal(metadata[DESCRIPTION_METADATA], sp.utils.bytes_of_string('"Angry Teenagers ... on the Tezos blockchain."'))
        scenario.verify_equal(metadata[RIGHTS_METADATA], sp.utils.bytes_of_string('"© 2022 EcoMint. All rights reserved."'))
        scenario.verify_equal(metadata[ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(metadata[ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(metadata[SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string("false"))
        scenario.verify_equal(metadata[CREATORS_METADATA], sp.utils.bytes_of_string('["EcoMint LTD. https://www.angryteenagers.xyz"]'))
        scenario.verify_equal(metadata[PROJECTNAME_METADATA], sp.utils.bytes_of_string('Project-1'))

        record1 = sp.record(artifactUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"),
                            displayUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"),
                            thumbnailUri=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"),
                            attributesJSonString=sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))
        list1 = sp.list({sp.pair(49, record1)})
        c1.update_artwork_data(list1).run(valid=True, sender=admin)

        metadata_pair = c1.token_metadata(49)
        scenario.verify(sp.fst(metadata_pair) == 49)
        metadata = sp.snd(metadata_pair)
        scenario.verify_equal(metadata[ARTIFACTURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"))
        scenario.verify_equal(metadata[DISPLAYURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB21"))
        scenario.verify_equal(metadata[THUMBNAILURI_METADATA], sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB31"))
        scenario.verify_equal(metadata[ROYALTIES_METADATA], sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'))
        scenario.verify_equal(metadata[REVEALED_METADATA], sp.utils.bytes_of_string('true'))
        scenario.verify_equal(metadata[NAME_METADATA], sp.utils.bytes_of_string('"Angry Teenager #49"'))
        scenario.verify_equal(metadata[WHAT3WORDSFILE_METADATA], sp.utils.bytes_of_string("ipfs://QmWk3kZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD1"))
        scenario.verify_equal(metadata[WHAT3WORDID_METADATA], sp.utils.bytes_of_string("49"))
        scenario.verify_equal(metadata[FORMATS_METADATA], sp.utils.bytes_of_string('[{"mimeType": "image/png","uri":"ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYB11"}]'))
        scenario.verify_equal(metadata[SYMBOL_METADATA], sp.utils.bytes_of_string('ANGRY'))
        scenario.verify_equal(metadata[ATTRIBUTES_METADATA], sp.utils.bytes_of_string('[{\"name\", \"generic1\"}]'))
        scenario.verify_equal(metadata[DECIMALS_METADATA], sp.utils.bytes_of_string('0'))
        scenario.verify_equal(metadata[LANGUAGE_METADATA], sp.utils.bytes_of_string('en-US'))
        scenario.verify_equal(metadata[DESCRIPTION_METADATA], sp.utils.bytes_of_string('"Angry Teenagers ... on the Tezos blockchain."'))
        scenario.verify_equal(metadata[RIGHTS_METADATA], sp.utils.bytes_of_string('"© 2022 EcoMint. All rights reserved."'))
        scenario.verify_equal(metadata[ISTRANSFERABLE_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(metadata[ISBOOLEANAMOUNT_METADATA], sp.utils.bytes_of_string("true"))
        scenario.verify_equal(metadata[SHOULDPREFERSYMBOL_METADATA], sp.utils.bytes_of_string("false"))
        scenario.verify_equal(metadata[CREATORS_METADATA], sp.utils.bytes_of_string('["EcoMint LTD. https://www.angryteenagers.xyz"]'))
        scenario.verify_equal(metadata[PROJECTORACLEURI_METADATA], sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"))
        scenario.verify_equal(metadata[PROJECTNAME_METADATA], sp.utils.bytes_of_string('Project-1'))

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
