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
ARTWORKS_CONTAINER_FUNCTION_TYPE = sp.TRecord(artifact_uri=sp.TBytes, artifact_size=sp.TBytes, display_uri=sp.TBytes, display_size=sp.TBytes, thumbnail_uri=sp.TBytes, thumbnail_size=sp.TBytes, attributes=sp.TBytes)
UPDATE_ARTWORK_METADATA_FUNCTION_TYPE = sp.TList(sp.TPair(TOKEN_ID, ARTWORKS_CONTAINER_FUNCTION_TYPE))

BALANCE_RECORD_TYPE = sp.TRecord(level=sp.TNat, value=sp.TNat)

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


DECIMALS = "0"
ISTRANSFERABLE = "true"
ISBOOLEANAMOUNT = "true"
SHOULDPREFERSYMBOL = "false"
REVEALED = "false"

FORMAT_OPEN_SQUAREBRACKET = sp.utils.bytes_of_string("[")
FORMAT_OPEN_CURLYBRACKET = sp.utils.bytes_of_string("{")
FORMAT_CLOSE_SQUAREBRACKET = sp.utils.bytes_of_string("]")
FORMAT_CLOSE_CURLYBRACKET = sp.utils.bytes_of_string("}")
FORMAT_COMMA = sp.utils.bytes_of_string(",")
FORMAT_QUOTE = sp.utils.bytes_of_string('"')
FORMAT_URI = sp.utils.bytes_of_string('"uri":')
FORMAT_FILENAME = sp.utils.bytes_of_string('"fileName":')
FORMAT_FILESIZE = sp.utils.bytes_of_string('"fileSize":')
FORMAT_VALUE = sp.utils.bytes_of_string('"value":')
FORMAT_UNIT = sp.utils.bytes_of_string('"unit":')
FORMAT_DIMENSIONS = sp.utils.bytes_of_string('"dimensions":')
FORMAT_MIMETYPE = sp.utils.bytes_of_string('"mimeType":')

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
        return sp.big_map(tkey=OPERATOR_TYPE, tvalue=sp.TUnit)

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
    def __init__(self, administrator,
                 royalties_bytes,
                 metadata,
                 generic_image_ipfs,
                 generic_image_ipfs_display,
                 generic_image_ipfs_thumbnail,
                 what3words_file_ipfs,
                 max_supply,
                 artifact_file_type,
                 artifact_file_size_generic,
                 artifact_file_name,
                 artifact_dimensions,
                 artifact_file_unit,
                 display_file_type,
                 display_file_size_generic,
                 display_file_name,
                 display_dimensions,
                 display_file_unit,
                 thumbnail_file_type,
                 thumbnail_file_size_generic,
                 thumbnail_file_name,
                 thumbnail_dimensions,
                 thumbnail_file_unit,
                 name_prefix,
                 symbol,
                 description,
                 language,
                 attributes_generic,
                 rights,
                 creators,
                 project_name
                 ):
        self.operator_set = Operator_set()

        self.artifact_file_type = sp.utils.bytes_of_string(artifact_file_type)
        self.artifact_file_size_generic = sp.utils.bytes_of_string(artifact_file_size_generic)
        self.artifact_file_name = sp.utils.bytes_of_string(artifact_file_name)
        self.artifact_dimensions = sp.utils.bytes_of_string(artifact_dimensions)
        self.artifact_file_unit = sp.utils.bytes_of_string(artifact_file_unit)
        self.display_file_type = sp.utils.bytes_of_string(display_file_type)
        self.display_file_size_generic = sp.utils.bytes_of_string(display_file_size_generic)
        self.display_file_name = sp.utils.bytes_of_string(display_file_name)
        self.display_dimensions = sp.utils.bytes_of_string(display_dimensions)
        self.display_file_unit = sp.utils.bytes_of_string(display_file_unit)
        self.thumbnail_file_type = sp.utils.bytes_of_string(thumbnail_file_type)
        self.thumbnail_file_size_generic = sp.utils.bytes_of_string(thumbnail_file_size_generic)
        self.thumbnail_file_name = sp.utils.bytes_of_string(thumbnail_file_name)
        self.thumbnail_dimensions = sp.utils.bytes_of_string(thumbnail_dimensions)
        self.thumbnail_file_unit = sp.utils.bytes_of_string(thumbnail_file_unit)

        self.name_prefix = sp.utils.bytes_of_string(name_prefix)
        self.symbol = sp.utils.bytes_of_string(symbol)
        self.description = sp.utils.bytes_of_string(description)
        self.language = sp.utils.bytes_of_string(language)
        self.attributes_generic = sp.utils.bytes_of_string(attributes_generic)
        self.rights = sp.utils.bytes_of_string(rights)
        self.creators = sp.utils.bytes_of_string(creators)
        self.project_name = sp.utils.bytes_of_string(project_name)

        self.init_type(
            sp.TRecord(
                ledger=sp.TBigMap(TOKEN_ID, sp.TAddress),
                operators=sp.TBigMap(OPERATOR_TYPE, sp.TUnit),
                voting_power=sp.TBigMap(sp.TPair(sp.TAddress, sp.TNat), BALANCE_RECORD_TYPE),
                voting_power_highest_index=sp.TBigMap(sp.TAddress, sp.TNat),
                administrator=sp.TAddress,
                next_administrator=sp.TOption(sp.TAddress),
                sale_contract_administrator=sp.TAddress,
                artwork_administrator=sp.TAddress,
                paused=sp.TBool,
                minted_tokens=sp.TNat,
                what3words_file_ipfs=sp.TBytes,
                max_supply=sp.TNat,
                token_metadata=sp.TBigMap(TOKEN_ID, sp.TPair(TOKEN_ID, sp.TMap(sp.TString, sp.TBytes))),
                extra_token_metadata=sp.TBigMap(TOKEN_ID, sp.TRecord(token_id=TOKEN_ID, token_info=sp.TMap(sp.TString, sp.TBytes))),
                generic_image_ipfs=sp.TBytes,
                generic_image_ipfs_display=sp.TBytes,
                generic_image_ipfs_thumbnail=sp.TBytes,
                project_oracles_deposits=sp.TBigMap(sp.TNat, sp.TBytes),
                project_oracles_number_of_deposits=sp.TNat,
                royalties=sp.TBytes,
                metadata= sp.TBigMap(sp.TString, sp.TBytes)
            )
        )

        self.init(
            ledger=sp.big_map(tkey=TOKEN_ID, tvalue=sp.TAddress),
            operators=self.operator_set.make(),

            voting_power=sp.big_map(tkey=sp.TPair(sp.TAddress, sp.TNat), tvalue=BALANCE_RECORD_TYPE),
            voting_power_highest_index = sp.big_map(tkey=sp.TAddress, tvalue=sp.TNat),

            # Administrator
            administrator=administrator,
            next_administrator=sp.none,
            sale_contract_administrator=administrator,
            artwork_administrator=administrator,

            # Pause
            paused=sp.bool(False),

            # Minted tokens
            minted_tokens=sp.nat(0),

            # What3words set file in ipfs
            what3words_file_ipfs=what3words_file_ipfs,

            # Max supply -- !!! Must match the number of line in the what3words file in ipfs
            max_supply=max_supply,

            # Token metadata
            token_metadata=sp.big_map(l={}, tkey=TOKEN_ID, tvalue=sp.TPair(TOKEN_ID, sp.TMap(sp.TString, sp.TBytes))),
            extra_token_metadata=sp.big_map(l={}, tkey=TOKEN_ID, tvalue=sp.TRecord(token_id =TOKEN_ID, token_info = sp.TMap(sp.TString, sp.TBytes))),

            generic_image_ipfs=generic_image_ipfs,
            generic_image_ipfs_display=generic_image_ipfs_display,
            generic_image_ipfs_thumbnail=generic_image_ipfs_thumbnail,

            project_oracles_deposits=sp.big_map(l={}, tkey=sp.TNat, tvalue=sp.TBytes),
            project_oracles_number_of_deposits=sp.nat(0),

            royalties=royalties_bytes,

            metadata=metadata
        )

        list_of_views = [
             self.get_balance
             , self.does_token_exist
             , self.count_tokens
             , self.all_tokens
             , self.get_user_tokens
             , self.is_operator
             , self.max_supply
             , self.token_metadata
             , self.get_project_oracles_deposit
             , self.get_project_oracles_number_of_deposits
             , self.get_all_non_revealed_token
        ]

        metadata_base = {
             "name": "Angry Teenagers"
            ,
             "version": "1.3.0"
             , "description": (
                     "Angry Teenagers: NFTs that fund an exponential cycle of reforestation."
        )
             , "interfaces": ["TZIP-012", "TZIP-016", "TZIP-021"]
             , "authors": [
                 "EcoMint LTD <www.angryteenagers.xyz>"
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
    @sp.entry_point(check_no_incoming_transfer=True)
    def balance_of(self, params):
        # paused may mean that balances are meaningless:
        sp.verify( ~self.is_paused(), message=Error.ErrorMessage.unauthorized_user())
        sp.set_type(params, BALANCE_OF_FUNCTION_TYPE)
        def f_process_request(req):
            sp.if self.data.ledger.get(req.token_id, message=Error.Fa2ErrorMessage.token_undefined()) == req.owner:
                sp.result(sp.record(
                        request=sp.record(
                        owner=sp.set_type_expr(req.owner, sp.TAddress),
                        token_id=sp.set_type_expr(req.token_id, sp.TNat)),
                        balance=1))
            sp.else:
                sp.result(sp.record(
                    request=sp.record(
                        owner=sp.set_type_expr(req.owner, sp.TAddress),
                        token_id=sp.set_type_expr(req.token_id, sp.TNat)),
                    balance=0))

        res = sp.local("responses", params.requests.map(f_process_request))
        destination = sp.set_type_expr(params.callback, sp.TContract(BALANCE_OF_RESPONSE_TYPE))
        sp.transfer(res.value, sp.mutez(0), destination)

    @sp.entry_point(check_no_incoming_transfer=True)
    def transfer(self, params):
        sp.verify(~self.is_paused(), message=Error.ErrorMessage.paused())
        sp.set_type(params, TRANSFER_FUNCTION_TYPE)
        sp.for transfer in params:
            current_from = transfer.from_
            sp.for tx in transfer.txs:
                sender_verify = (current_from == sp.sender)
                message = Error.Fa2ErrorMessage.not_operator()
                sender_verify |= (self.operator_set.is_member(self.data.operators,
                                                              current_from,
                                                              sp.sender,
                                                              tx.token_id))
                sp.verify(sender_verify, message=message)
                # Tzip-12 allows transfer of 0 token. In this case nothing happens but the whole transaction doesn't fail.
                sp.verify(tx.amount <= 1, Error.Fa2ErrorMessage.insufficient_balance())
                # Be sure the token exists
                sp.verify(self.data.ledger.contains(tx.token_id),  message=Error.Fa2ErrorMessage.token_undefined())

                sp.if tx.amount == 1:
                    sp.verify(self.data.ledger[tx.token_id] == current_from, Error.Fa2ErrorMessage.insufficient_balance())
                    self.data.ledger[tx.token_id] = tx.to_

                    # Update sender balance
                    self.update_voting_power(sp.record(address=current_from, is_receive=False))

                    # Update receiver balance
                    self.update_voting_power(sp.record(address=tx.to_, is_receive=True))

                    event = sp.record(from_=current_from, to_=tx.to_, token_id=tx.token_id)
                    sp.emit(event, with_type=True, tag="transfer")


    @sp.entry_point(check_no_incoming_transfer=True)
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
                        message=Error.Fa2ErrorMessage.not_operator()
                    )
                    self.operator_set.add(self.data.operators,
                                          upd.owner,
                                          upd.operator,
                                          upd.token_id)
                with arg.match("remove_operator") as upd:
                    sp.verify(
                        (upd.owner == sp.sender) | self.is_administrator(sp.sender),
                        message=Error.Fa2ErrorMessage.not_operator()
                    )
                    self.operator_set.remove(self.data.operators,
                                             upd.owner,
                                             upd.operator,
                                             upd.token_id)

########################################################################################################################
# Dedicated entry points
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def mutez_transfer(self, params):
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        sp.set_type(params.destination, sp.TAddress)
        sp.set_type(params.amount, sp.TMutez)
        sp.send(params.destination, params.amount)

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_metadata(self, key, value):
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        self.data.metadata[key] = value

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_extra_token_metadata(self, token_id, key, value):
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        sp.if ~self.data.extra_token_metadata.contains(token_id):
            self.data.extra_token_metadata[token_id] = sp.record(token_id=token_id, token_info=sp.map(l={}, tkey=sp.TString, tvalue=sp.TBytes))
        self.data.extra_token_metadata[token_id].token_info[key] = value

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_pause(self, params):
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        self.data.paused = params

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_next_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        self.data.next_administrator = sp.some(params)

    @sp.entry_point(check_no_incoming_transfer=True)
    def validate_new_administrator(self):
        sp.verify(self.data.next_administrator.is_some(), message=Error.ErrorMessage.no_next_admin())
        sp.verify(sp.sender == self.data.next_administrator.open_some(), message=Error.ErrorMessage.not_admin())
        self.data.administrator = self.data.next_administrator.open_some()
        self.data.next_administrator = sp.none

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_sale_contract_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        self.data.sale_contract_administrator = params

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_artwork_administrator(self, params):
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        self.data.artwork_administrator = params

    @sp.entry_point(check_no_incoming_transfer=True)
    def add_new_oracles_deposit(self, params):
        sp.set_type(params, sp.TBytes)
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        self.data.project_oracles_deposits[self.data.project_oracles_number_of_deposits] = params
        self.data.project_oracles_number_of_deposits = self.data.project_oracles_number_of_deposits + 1

    @sp.entry_point(check_no_incoming_transfer=True)
    def update_artwork_data(self, params):
        sp.verify(self.is_artwork_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        sp.set_type(params, UPDATE_ARTWORK_METADATA_FUNCTION_TYPE)
        sp.for artwork_metadata in params:
            sp.verify(self.data.ledger.contains(sp.fst(artwork_metadata)), message=Error.Fa2ErrorMessage.token_undefined())
            info = sp.local('info', sp.snd(self.data.token_metadata.get(sp.fst(artwork_metadata), message=Error.Fa2ErrorMessage.token_undefined())))
            sp.verify(info.value.get(REVEALED_METADATA, message=Error.Fa2ErrorMessage.token_undefined()) == sp.utils.bytes_of_string("false"), message=Error.ErrorMessage.token_revealed())

            my_map = sp.local('my_map', sp.update_map(sp.snd(self.data.token_metadata[sp.fst(artwork_metadata)]), REVEALED_METADATA, sp.some(sp.utils.bytes_of_string("true"))))
            my_map.value = sp.update_map(my_map.value, ARTIFACTURI_METADATA, sp.some((sp.snd(artwork_metadata)).artifact_uri))
            my_map.value = sp.update_map(my_map.value, DISPLAYURI_METADATA, sp.some((sp.snd(artwork_metadata)).display_uri))
            my_map.value = sp.update_map(my_map.value, THUMBNAILURI_METADATA, sp.some((sp.snd(artwork_metadata)).thumbnail_uri))
            my_map.value = sp.update_map(my_map.value, ATTRIBUTES_METADATA, sp.some((sp.snd(artwork_metadata)).attributes))
            my_map.value = sp.update_map(my_map.value, ATTRIBUTES_METADATA, sp.some((sp.snd(artwork_metadata)).attributes))

            formats = sp.local(FORMATS_METADATA, self.create_format_metadata((sp.snd(artwork_metadata)).artifact_uri,
                                                                             (sp.snd(artwork_metadata)).display_uri,
                                                                             (sp.snd(artwork_metadata)).thumbnail_uri,
                                                                             (sp.snd(artwork_metadata)).artifact_size,
                                                                             (sp.snd(artwork_metadata)).display_size,
                                                                             (sp.snd(artwork_metadata)).thumbnail_size))
            my_map.value = sp.update_map(my_map.value, FORMATS_METADATA, sp.some(formats.value))

            self.data.token_metadata[sp.fst(artwork_metadata)] = sp.pair(sp.fst(artwork_metadata), my_map.value)

            event = sp.fst(artwork_metadata)
            sp.emit(event, with_type=True, tag="update_artwork_data")


    @sp.entry_point(check_no_incoming_transfer=True)
    def set_royalties_field(self, params):
        # Verify type
        sp.set_type(params, sp.TBytes)

        # Asserts
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())

        # Set the royalties field for NFTs not minted yet
        self.data.royalties = params

    @sp.entry_point(check_no_incoming_transfer=True)
    def set_royalties_minted_tokens(self, params):
        # Verify type
        sp.set_type(params, sp.TList(TOKEN_ID))

        # Asserts
        sp.verify(self.is_administrator(sp.sender), message=Error.ErrorMessage.not_admin())

        # Change NFTs token metadata
        sp.for token in params:
            sp.verify(self.data.ledger.contains(token), message=Error.Fa2ErrorMessage.token_undefined())
            info = sp.local('info', sp.snd(self.data.token_metadata.get(token, message=Error.Fa2ErrorMessage.token_undefined())))
            info.value.get(ROYALTIES_METADATA, message=Error.Fa2ErrorMessage.token_undefined())

            my_map = sp.local('my_map', sp.update_map(sp.snd(self.data.token_metadata[token]), ROYALTIES_METADATA, sp.some(self.data.royalties)))
            self.data.token_metadata[token] = sp.pair(token, my_map.value)

    @sp.entry_point(check_no_incoming_transfer=True)
    def mint(self, params):
        sp.set_type(params, sp.TAddress)
        sp.verify(self.is_sale_contract_administrator(sp.sender), message=Error.ErrorMessage.not_admin())
        # We don't check for pauseness because we're the admin.
        sp.verify(self.data.minted_tokens < self.data.max_supply, message=Error.ErrorMessage.no_land_available())

        self.data.ledger[self.data.minted_tokens] = params
        self.build_token_metadata(self.data.minted_tokens)

        self.data.minted_tokens = self.data.minted_tokens + 1

        # Update voting power
        self.update_voting_power(sp.record(address=params, is_receive=True))

        # Send event
        event = sp.record(sender=sp.sender, receiver=params)
        sp.emit(event, with_type=True, tag="mint")

########################################################################################################################
# Onchain views
########################################################################################################################
    @sp.onchain_view()
    def get_voting_power(self, params):
        sp.set_type(params, sp.TPair(sp.TAddress, sp.TNat))
        address, level = sp.match_pair(params)

        result = sp.local('result', sp.nat(0))

        sp.if self.data.voting_power_highest_index.contains(address):
            upper_bound = sp.local('upper_bound', self.data.voting_power_highest_index.get(address, message=Error.ErrorMessage.balance_inconsistency()))
            lower_bound = sp.local('lower_bound', sp.nat(0))

            sp.if upper_bound.value == 0:
                root_elem = sp.local('root_elem', self.data.voting_power.get(sp.pair(address, upper_bound.value),
                                                                             message=Error.ErrorMessage.balance_inconsistency()))
                sp.if root_elem.value.level <= level:
                    result.value = root_elem.value.value

            sp.else:
                finished = sp.local('finished', sp.bool(False))
                # Binary search tree
                sp.while ~finished.value:
                    interval = sp.local('interval', sp.is_nat(upper_bound.value - lower_bound.value).open_some(message=Error.ErrorMessage.internal_error()))

                    sp.if interval.value == 1:
                        finished.value = True
                        upper_elem = sp.local('upper_elem', self.data.voting_power.get(sp.pair(address, upper_bound.value),
                                                                                       message=Error.ErrorMessage.balance_inconsistency()))
                        sp.if upper_elem.value.level <= level:
                            result.value = upper_elem.value.value
                        sp.else:
                            lower_elem = sp.local('lower_elem', self.data.voting_power.get(sp.pair(address, lower_bound.value),
                                                                         message=Error.ErrorMessage.balance_inconsistency()))
                            sp.if lower_elem.value.level <= level:
                                result.value = lower_elem.value.value
                    sp.else:
                        middle = sp.local('middle', (interval.value / 2) + lower_bound.value)
                        elem = sp.local('elem', self.data.voting_power.get(sp.pair(address, middle.value),
                                                               message=Error.ErrorMessage.balance_inconsistency()))

                        sp.if elem.value.level == level:
                            finished.value = True
                            result.value = elem.value.value
                        sp.else:
                            sp.if elem.value.level > level:
                                upper_bound.value = middle.value
                            sp.else:
                                lower_bound.value = middle.value
                    sp.verify(upper_bound.value > lower_bound.value, message=Error.ErrorMessage.internal_error())

        sp.result(result.value)

    @sp.onchain_view()
    def get_total_voting_power(self):
        """Get how many tokens are in this FA2 contract onchain.
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
    def does_token_exist(self, token_id):
        """Aks whether a token exists.
        """
        sp.set_type(token_id, sp.TNat)
        sp.result(self.data.ledger.contains(token_id))

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
            sp.if self.data.ledger.get(i.value, message=Error.Fa2ErrorMessage.token_undefined()) == params:
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
            sp.if (sp.snd(self.data.token_metadata.get(i.value, message=Error.Fa2ErrorMessage.token_undefined())))[REVEALED_METADATA] == sp.utils.bytes_of_string("false"):
                token_list.value.push(i.value)
            i.value = i.value + 1
        sp.result(token_list.value)

    @sp.offchain_view(pure=True)
    def max_supply(self, token_id):
        """Get the max supply for one token_id.
        """
        sp.set_type(token_id, sp.TNat)
        sp.if token_id < self.data.minted_tokens:
            sp.result(sp.nat(1))
        sp.else:
            sp.failwith(message=Error.Fa2ErrorMessage.insufficient_balance())

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
    def get_balance(self, request):
        """Get balance as defined in TZIP-012.
        """
        sp.set_type(
            request, sp.TRecord(
                owner=sp.TAddress,
                token_id=sp.TNat
            ).layout(("owner", "token_id")))
        sp.if self.data.ledger.get(request.token_id, message=Error.Fa2ErrorMessage.token_undefined()) == request.owner:
            sp.result(sp.nat(1))
        sp.else:
            sp.result(sp.nat(0))

    @sp.offchain_view(pure=True)
    def get_project_oracles_deposit(self, params):
        """Get oracle deposit using the deposit index"""
        sp.set_type(params, sp.TNat)
        sp.verify(params < self.data.project_oracles_number_of_deposits)
        sp.result(self.data.project_oracles_deposits[params])

    @sp.offchain_view(pure=True)
    def get_project_oracles_number_of_deposits(self):
        """Get number of oracle deposits"""
        sp.result(self.data.project_oracles_number_of_deposits)

    @sp.offchain_view(pure=True)
    def token_metadata(self, token_id):
        """Get token metadata
        """
        sp.set_type(token_id, sp.TNat)
        sp.verify(token_id < self.data.max_supply)
        sp.verify(self.data.ledger.contains(token_id), message=Error.Fa2ErrorMessage.token_undefined())

        sp.result(self.data.token_metadata.get(token_id, message=Error.Fa2ErrorMessage.token_undefined()))

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

    @sp.private_lambda(with_storage="read-write", with_operations=False, wrap_call=True)
    def update_voting_power(self, params):
        sp.set_type(params, sp.TRecord(address=sp.TAddress, is_receive=sp.TBool))

        sp.if ~params.is_receive:
            sp.verify(self.data.voting_power_highest_index.contains(params.address), message=Error.ErrorMessage.balance_inconsistency())

        highest_index = sp.local('highest_index', self.data.voting_power_highest_index.get(params.address, sp.nat(0)))

        sp.if params.is_receive & ~self.data.voting_power_highest_index.contains(params.address):
            self.data.voting_power_highest_index[params.address] = 0
            self.data.voting_power[sp.pair(params.address, 0)] = sp.record(level=sp.level, value=1)
        sp.else:
            current_value = sp.local('current_value', self.data.voting_power.get(sp.pair(params.address, highest_index.value),
                                                                     message=Error.ErrorMessage.balance_inconsistency()))
            sp.verify(current_value.value.level <= sp.level, message=Error.ErrorMessage.balance_inconsistency())

            sp.if current_value.value.level != sp.level:
                highest_index.value = highest_index.value + 1
                self.data.voting_power_highest_index[params.address] = highest_index.value

            new_value = sp.local('new_value', current_value.value.value + 1)
            sp.if ~params.is_receive:
                new_value.value = sp.is_nat(current_value.value.value - 1).open_some(Error.ErrorMessage.balance_inconsistency())

            self.data.voting_power[sp.pair(params.address, highest_index.value)] = sp.record(level=sp.level, value=new_value.value)

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
                                                       tvalue=sp.TBytes))

        x = sp.local('x', token_id)
        token_id_string = sp.local('token_id_string', sp.bytes('0x'))
        sp.if x.value == 0:
            token_id_string.value = sp.concat([token_id_string.value, nat_to_bytes.value[0]])
        sp.else:
            sp.while 0 < x.value:
                token_id_string.value = sp.concat([nat_to_bytes.value[x.value % 10], token_id_string.value])
                x.value //= 10

        name = sp.concat([self.name_prefix, token_id_string.value])

        formats = sp.local('formats', self.create_format_metadata(self.data.generic_image_ipfs,
                                                                  self.data.generic_image_ipfs_display,
                                                                  self.data.generic_image_ipfs_thumbnail,
                                                                  self.artifact_file_size_generic,
                                                                  self.display_file_size_generic,
                                                                  self.thumbnail_file_size_generic))

        meta_map = sp.map(l={
            NAME_METADATA: name,
            SYMBOL_METADATA: self.symbol,
            DECIMALS_METADATA: sp.utils.bytes_of_string(DECIMALS),
            LANGUAGE_METADATA: self.language,
            DESCRIPTION_METADATA: self.description,
            DATE_METADATA: sp.pack(sp.now),
            ARTIFACTURI_METADATA: self.data.generic_image_ipfs,
            DISPLAYURI_METADATA: self.data.generic_image_ipfs_display,
            THUMBNAILURI_METADATA: self.data.generic_image_ipfs_thumbnail,
            ATTRIBUTES_METADATA: self.attributes_generic,
            RIGHTS_METADATA: self.rights,
            ISTRANSFERABLE_METADATA: sp.utils.bytes_of_string(ISTRANSFERABLE),
            ISBOOLEANAMOUNT_METADATA: sp.utils.bytes_of_string(ISBOOLEANAMOUNT),
            SHOULDPREFERSYMBOL_METADATA: sp.utils.bytes_of_string(SHOULDPREFERSYMBOL),
            CREATORS_METADATA: self.creators,
            PROJECTNAME_METADATA: self.project_name,
            FORMATS_METADATA: formats.value,
            WHAT3WORDSFILE_METADATA: self.data.what3words_file_ipfs,
            WHAT3WORDID_METADATA: token_id_string.value,
            REVEALED_METADATA: sp.utils.bytes_of_string(REVEALED),
            ROYALTIES_METADATA: self.data.royalties,
        })

        self.data.token_metadata[token_id] = sp.pair(token_id, meta_map)

    def create_format_metadata_per_uri(self, link, type, size, name, dimensions, unit):
        value = FORMAT_OPEN_CURLYBRACKET + FORMAT_URI + FORMAT_QUOTE + link + FORMAT_QUOTE + \
                FORMAT_COMMA + FORMAT_MIMETYPE + type + \
                FORMAT_COMMA + FORMAT_FILESIZE + size + \
                FORMAT_COMMA + FORMAT_FILENAME + name + \
                FORMAT_COMMA + FORMAT_DIMENSIONS + FORMAT_OPEN_CURLYBRACKET + FORMAT_VALUE + dimensions + \
                FORMAT_COMMA + FORMAT_UNIT + unit + FORMAT_CLOSE_CURLYBRACKET + FORMAT_CLOSE_CURLYBRACKET
        return value


    def create_format_metadata(self, artifact_link, display_link, thumbnail_link, artifact_size, display_size, thumbnail_size):
        value = FORMAT_OPEN_SQUAREBRACKET + \
                self.create_format_metadata_per_uri(artifact_link, self.artifact_file_type, artifact_size,
                                                    self.artifact_file_name, self.artifact_dimensions,
                                                    self.artifact_file_unit) + \
                FORMAT_COMMA + \
                self.create_format_metadata_per_uri(display_link, self.display_file_type, display_size,
                                                    self.display_file_name, self.display_dimensions,
                                                    self.display_file_unit) + \
                FORMAT_COMMA + \
                self.create_format_metadata_per_uri(thumbnail_link, self.thumbnail_file_type, thumbnail_size,
                                                    self.thumbnail_file_name, self.thumbnail_dimensions,
                                                    self.thumbnail_file_unit) + \
                FORMAT_CLOSE_SQUAREBRACKET
        return value



