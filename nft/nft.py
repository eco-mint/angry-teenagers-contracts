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
UPDATE_ARTWORK_METADATA_FUNCTION_TYPE = sp.TList(sp.TPair(TOKEN_ID, sp.TBytes))

BALANCE_RECORD_TYPE = sp.TMap(sp.TNat, sp.TNat)

########################################################################################################################
########################################################################################################################
# Constants
########################################################################################################################
##################################################################################################################

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
    def __init__(self,
                 administrator,
                 metadata,
                 generic_ipfs,
                 project_oracles_stream,
                 what3words_file_ipfs,
                 total_supply):
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

            generic_ipfs = generic_ipfs,

            project_oracles_stream = project_oracles_stream,

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
             , self.get_project_oracles_stream
             , self.get_all_non_revealed_token
        ]

        metadata_base = {
             "version": "1.0.2"
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
            # TODO: Use a reveal token list to avoid multiple reveal
            self.data.token_metadata[sp.fst(artwork_metadata)] = sp.pair(sp.fst(artwork_metadata), sp.map(l={ "": sp.snd(artwork_metadata)}, tkey=sp.TString, tvalue=sp.TBytes))


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
        # TODO: To rework
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
        self.data.token_metadata[token_id] = sp.pair(token_id, sp.map(l={"": self.data.generic_ipfs}, tkey=sp.TString, tvalue=sp.TBytes))




