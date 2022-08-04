import smartpy as sp

Error = sp.io.import_script_from_url("file:./helper/errors.py")

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
             "version": "1.0.0"
             , "description": (
                     "Angry Teenagers: NFTs that fund an exponential cycle of reforestation."
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
