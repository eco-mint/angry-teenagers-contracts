import smartpy as sp

Error = sp.io.import_script_from_url("file:./helper/errors.py")

########################################################################################################################
########################################################################################################################
# State machine
########################################################################################################################
########################################################################################################################

# See a definition of the state machine in the Notion spec
# https://www.notion.so/ecomint/Angry-Teenager-NFT-contracts-b1efe7fb4fad48c89777a07ccd356ad2

# No events are opened
STATE_NO_EVENT_OPEN_0 = 0
# An event is opened where the user can register in the allowlist.
# For this, he needs to be added first to the pre allowlist by the admin
STATE_EVENT_PRIV_ALLOWLIST_REG_1 = 1
# No event are opened but the allowlist is already filled during a previous private allowlist registration event
STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2 = 2
# An event is opened where every user can register to the allowlist assuming there is enough space remaining
STATE_EVENT_PUB_ALLOWLIST_REG_3 = 3
# No event are opened but allowlist has been filled during the a public event
STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4 = 4
# An event is opened where only users in the allowlist can mint tokens
STATE_EVENT_PRESALE_5 = 5
# An event is opened where any users can mint tokens limited with the max supply per user and the max total supply
# allocated to the sale
STATE_EVENT_PUBLIC_SALE_6 = 6

########################################################################################################################
########################################################################################################################
# Types definition
########################################################################################################################
##################################################################################################################
FA2_UPDATE_TOKEN_METADATA_PARAM_TYPE = sp.TRecord(token_id=sp.TNat,metadata=sp.TBytes)
FA2_MINT_PARAM_TYPE = sp.TAddress

ADMIN_FILL_ALLOWLIST_PARAM_TYPE=sp.TSet(sp.TAddress)
ADMIN_FILL_PRE_ALLOWLIST_PARAM_TYPE=sp.TSet(sp.TAddress)
ADMIN_OPEN_EVENT_PRIVATE_ALLOWLIST_REGISTRATION_PARAM_TYPE = sp.TRecord(price=sp.TMutez)
ADMIN_OPEN_EVENT_PUBLIC_ALLOWLIST_REGISTRATION_PARAM_TYPE = sp.TRecord(max_space=sp.TNat, price=sp.TMutez)
ADMIN_OPEN_PRE_SALE_PARAM_TYPE=sp.TRecord(max_supply=sp.TNat, max_per_user=sp.TNat, price=sp.TMutez)
ADMIN_OPEN_PUBLIC_SALE_PARAM_TYPE=sp.TRecord(max_supply=sp.TNat, max_per_user=sp.TNat, price=sp.TMutez)
ADMIN_OPEN_PUBLIC_SALE_WITH_ALLOWLIST_PARAM_TYPE=sp.TRecord(max_supply=sp.TNat, max_per_user=sp.TNat, price=sp.TMutez, mint_right=sp.TBool, mint_discount=sp.TMutez)
ADMIN_UPDATE_TOKEN_METADATA_PARAM_TYPE = sp.TList(FA2_UPDATE_TOKEN_METADATA_PARAM_TYPE)

########################################################################################################################
########################################################################################################################
# Class AngryTeenager Sale (the contract)
########################################################################################################################
########################################################################################################################
class AngryTeenagersSale(sp.Contract):
    def __init__(self, admin, multisig_fund_address, metadata):
        self.init_type(
            sp.TRecord(
                administrator=sp.TAddress,
                next_administrator=sp.TOption(sp.TAddress),
                multisig_fund_address=sp.TAddress,
                fa2=sp.TAddress,
                state=sp.TNat,
                allowlist=sp.TSet(sp.TAddress),
                pre_allowlist=sp.TSet(sp.TAddress),
                event_price=sp.TMutez,
                event_max_supply=sp.TNat,
                event_max_per_user=sp.TNat,
                event_user_balance=sp.TBigMap(sp.TAddress, sp.TNat),
                public_allowlist_max_space=sp.TNat,
                public_allowlist_space_taken=sp.TNat,
                public_sale_allowlist_config=sp.TRecord(used=sp.TBool, discount=sp.TMutez, minting_rights=sp.TBool),
                token_minted_in_event=sp.TNat,
                metadata=sp.TBigMap(sp.TString, sp.TBytes)
            )
        )

        self.init(
            administrator=admin,
            next_administrator=sp.none,
            multisig_fund_address=multisig_fund_address,
            fa2=sp.address('KT1XmD6SKw6CFoxmGseB3ttws5n8sTXYkKkq'),

            state=sp.nat(STATE_NO_EVENT_OPEN_0),

            allowlist=sp.set(l={}, t=sp.TAddress),
            pre_allowlist=sp.set(l={}, t=sp.TAddress),

            event_price=sp.mutez(0),
            event_max_supply=sp.nat(0),
            event_max_per_user=sp.nat(0),

            event_user_balance=sp.big_map(l={}, tkey=sp.TAddress, tvalue=sp.TNat),

            public_allowlist_max_space=sp.nat(0),
            public_allowlist_space_taken=sp.nat(0),
            public_sale_allowlist_config=sp.record(used=sp.bool(False), discount=sp.mutez(0), minting_rights=sp.bool(False)),

            token_minted_in_event=sp.nat(0),

            metadata=metadata
        )
        list_of_views = [
            self.get_mint_token_available
        ]

        metadata_base = {
            "name": "Angry Teenagers CrowdSale"
            ,
            "version": "1.1.1"
            , "description": (
                "Angry Teenagers Crowdsale contract"
            )
            , "interfaces": ["TZIP-016"]
            , "authors": [
                "EcoMint LTD <www.angryteenagers.xyz>"
            ]
            , "homepage": "https://www.angryteenagers.xyz"
            , "views": list_of_views
        }
        self.init_metadata("metadata_base", metadata_base)

########################################################################################################################
# off-chain function
########################################################################################################################
    @sp.offchain_view(pure=True)
    def get_mint_token_available(self, params):
        """
        Return the number of token an address can mint"""
        # This may be a problem and makes it harder to be consistent. The total supply is defined by the lands available.
        # We can add some protection with a view.
        sp.set_type(params, sp.TAddress)

        user_balance = sp.local("user_balance", self.data.event_user_balance.get(params, 0))

        sp.if self.data.state == STATE_EVENT_PRESALE_5:
            sp.if ~self.data.allowlist.contains(params):
                sp.result(0)
            sp.else:
                sp.if self.data.token_minted_in_event >= self.data.event_max_supply:
                    sp.result(0)
                sp.else:
                    sp.if user_balance.value >= self.data.event_max_per_user:
                        sp.result(0)
                    sp.else:
                        remaining_user = self.data.event_max_per_user - user_balance.value
                        remaining_event = self.data.event_max_supply - self.data.token_minted_in_event
                        sp.if remaining_user < remaining_event:
                            sp.result(remaining_user)
                        sp.else:
                            sp.result(remaining_event)

        sp.else:
            sp.if self.data.state == STATE_EVENT_PUBLIC_SALE_6:
                sp.if ~(self.data.allowlist.contains(params) & self.data.public_sale_allowlist_config.minting_rights):
                    sp.if self.data.token_minted_in_event >= self.data.event_max_supply:
                        sp.result(0)
                    sp.else:
                        sp.if user_balance.value >= self.data.event_max_per_user:
                            sp.result(0)
                        sp.else:
                            remaining_user = self.data.event_max_per_user - user_balance.value
                            remaining_event = self.data.event_max_supply - self.data.token_minted_in_event
                            sp.if remaining_user < remaining_event:
                                sp.result(remaining_user)
                            sp.else:
                                sp.result(remaining_event)
                sp.else:
                    sp.if user_balance.value >= self.data.event_max_per_user:
                        sp.result(0)
                    sp.else:
                        sp.result(self.data.event_max_per_user - user_balance.value)
            sp.else:
                sp.result(0)


########################################################################################################################
# admin_fill_allowlist
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def admin_fill_allowlist(self, params):
        """Admin fill the allowlist"""
        sp.set_type(params, ADMIN_FILL_ALLOWLIST_PARAM_TYPE)

        # Only for admin
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2) |
                  (self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4),
                  message=Error.ErrorMessage.sale_event_already_open())

        sp.for item in params.elements():
            sp.if ~self.data.allowlist.contains(item):
                self.data.allowlist.add(item)

########################################################################################################################
# admin_fill_pre_allowlist
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def admin_fill_pre_allowlist(self, params):
        """Add a set of addresses to the pre_allowlist_entry"""
        sp.set_type(params, ADMIN_FILL_PRE_ALLOWLIST_PARAM_TYPE)

        # Only for admin
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        # This can be called only in state STATE_NO_EVENT_OPEN_0
        sp.verify(self.data.state == STATE_NO_EVENT_OPEN_0, message=Error.ErrorMessage.sale_event_already_open())

        sp.for item in params.elements():
            sp.if ~self.data.pre_allowlist.contains(item):
                self.data.pre_allowlist.add(item)

########################################################################################################################
# admin_open_event_private_allowlist
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def open_event_priv_allowlist_reg(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        # This can be called only in state STATE_NO_EVENT_OPEN_0
        sp.verify(self.data.state == STATE_NO_EVENT_OPEN_0, message=Error.ErrorMessage.sale_event_already_open())

        sp.set_type(params, ADMIN_OPEN_EVENT_PRIVATE_ALLOWLIST_REGISTRATION_PARAM_TYPE)

        self.data.event_price=params.price

        # Go to state STATE_EVENT_PRIV_ALLOWLIST_REG_1
        self.data.state = STATE_EVENT_PRIV_ALLOWLIST_REG_1

        sp.emit(params, with_type=True, tag="open_event_priv_allowlist_reg")

########################################################################################################################
# pay_to_enter_allowlist_priv
########################################################################################################################
    @sp.entry_point
    def pay_to_enter_allowlist_priv(self):
        # Only in state STATE_EVENT_PRIV_ALLOWLIST_REG_1
        sp.verify(self.data.state == STATE_EVENT_PRIV_ALLOWLIST_REG_1, message=Error.ErrorMessage.sale_event_already_open())

        # Must be on the pre_allowlist
        sp.verify(self.data.pre_allowlist.contains(sp.sender), message=Error.ErrorMessage.forbidden_operation())
        sp.verify(sp.amount == self.data.event_price)
        self.redirect_fund(sp.amount)
        self.data.pre_allowlist.remove(sp.sender)
        self.data.allowlist.add(sp.sender)

        sp.emit(sp.sender, with_type=True, tag="pay_to_enter_allowlist_priv")

########################################################################################################################
# open_event_pub_allowlist_reg
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def open_event_pub_allowlist_reg(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        # This can be called only in state STATE_NO_EVENT_OPEN_0 or STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2
        sp.verify((self.data.state == STATE_NO_EVENT_OPEN_0) | (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2), Error.ErrorMessage.sale_event_already_open())
        sp.verify(params.max_space > 0, message=Error.ErrorMessage.invalid_parameter())

        sp.set_type(params, ADMIN_OPEN_EVENT_PUBLIC_ALLOWLIST_REGISTRATION_PARAM_TYPE)

        self.data.public_allowlist_max_space = params.max_space
        self.data.public_allowlist_space_taken = 0
        self.data.event_price=params.price

        # Go to state STATE_EVENT_PUB_ALLOWLIST_REG_3
        self.data.state = STATE_EVENT_PUB_ALLOWLIST_REG_3

        sp.emit(params, with_type=True, tag="open_event_pub_allowlist_reg")


########################################################################################################################
# pay_to_enter_allowlist_pub
########################################################################################################################
    @sp.entry_point
    def pay_to_enter_allowlist_pub(self):
        # Only in state STATE_EVENT_PUB_ALLOWLIST_REG_3
        sp.verify(self.data.state == STATE_EVENT_PUB_ALLOWLIST_REG_3, message=Error.ErrorMessage.sale_event_already_open())

        # Not already in the list
        sp.verify(~self.data.allowlist.contains(sp.sender), message=Error.ErrorMessage.forbidden_operation())

        # Enough space remaining
        sp.verify(self.data.public_allowlist_space_taken < self.data.public_allowlist_max_space,
                  message=Error.ErrorMessage.sale_no_space_remaining())

        sp.verify(sp.amount == self.data.event_price)
        self.redirect_fund(sp.amount)

        self.data.public_allowlist_space_taken = self.data.public_allowlist_space_taken + 1
        self.data.allowlist.add(sp.sender)

        sp.if self.data.public_allowlist_space_taken >= self.data.public_allowlist_max_space:
            self.stop_internal_event()

        sp.emit(sp.sender, with_type=True, tag="pay_to_enter_allowlist_pub")


########################################################################################################################
# open_pre_sale
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def open_pre_sale(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2) |
                  (self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4), message=Error.ErrorMessage.sale_event_already_open())

        # check parameters
        sp.set_type(params, ADMIN_OPEN_PRE_SALE_PARAM_TYPE)
        sp.verify(params.max_supply > 0, message=Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_per_user > 0, message=Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_supply > params.max_per_user, message=Error.ErrorMessage.invalid_parameter())

        self.start_sale_init(params.max_supply, params.max_per_user, params.price)

        self.data.state = STATE_EVENT_PRESALE_5

        sp.emit(params, with_type=True, tag="open_pre_sale")


########################################################################################################################
# open_pub_sale
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def open_pub_sale(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4) |
                  (self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2),
                  message=Error.ErrorMessage.sale_event_already_open())

        # check parameters
        sp.set_type(params, ADMIN_OPEN_PRE_SALE_PARAM_TYPE)
        sp.verify(params.max_supply > 0, message=Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_per_user > 0, message=Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_supply > params.max_per_user, message=Error.ErrorMessage.invalid_parameter())

        self.data.public_sale_allowlist_config.used = False
        self.data.public_sale_allowlist_config.discount = sp.mutez(0)
        self.data.public_sale_allowlist_config.minting_rights = False

        self.start_sale_init(params.max_supply, params.max_per_user, params.price)

        self.data.state = STATE_EVENT_PUBLIC_SALE_6

        sp.emit(params, with_type=True, tag="open_pub_sale")


########################################################################################################################
# open_pub_sale_with_allowlist
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def open_pub_sale_with_allowlist(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4) |
                  (self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2),
                  message=Error.ErrorMessage.sale_event_already_open())

        # check parameters
        sp.set_type(params, ADMIN_OPEN_PUBLIC_SALE_WITH_ALLOWLIST_PARAM_TYPE)
        sp.verify(params.max_supply > 0, message=Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_per_user > 0, message=Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_supply > params.max_per_user, message=Error.ErrorMessage.invalid_parameter())
        sp.verify(params.price >= params.mint_discount, message=Error.ErrorMessage.invalid_parameter())

        self.data.public_sale_allowlist_config.used = True
        self.data.public_sale_allowlist_config.discount = params.mint_discount
        self.data.public_sale_allowlist_config.minting_rights = params.mint_right

        self.start_sale_init(params.max_supply, params.max_per_user, params.price)

        self.data.state = STATE_EVENT_PUBLIC_SALE_6

        sp.emit(params, with_type=True, tag="open_pub_sale_with_allowlist")


########################################################################################################################
# set_metadata
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def set_metadata(self, key, value):
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())
        self.data.metadata[key] = value

########################################################################################################################
# user_mint
########################################################################################################################
    @sp.entry_point
    def user_mint(self, params):
        sp.set_type(params, sp.TRecord(amount=sp.TNat, address=sp.TAddress))

        sp.verify(params.amount > 0, message=Error.ErrorMessage.sale_no_token())
        sp.verify(params.amount <= self.data.event_max_per_user, message=Error.ErrorMessage.sale_no_token())

        sp.if self.data.state == STATE_EVENT_PRESALE_5:
            self.mint_pre_sale(params)
        sp.else:
            sp.if self.data.state == STATE_EVENT_PUBLIC_SALE_6:
                self.mint_public_sale(params)
            sp.else:
                sp.failwith(Error.ErrorMessage.forbidden_operation())

        event = sp.record(sender=sp.sender, receiver=params.address, amount=params.amount)
        sp.emit(event, with_type=True, tag="mint")


########################################################################################################################
# close_any_open_event
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def close_any_open_event(self):
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())

        sp.verify(self.is_any_event_open(), message=Error.ErrorMessage.sale_no_event_open())
        self.stop_internal_event()

        sp.emit(self.data.state, with_type=True, tag="close_any_open_event")

########################################################################################################################
# mint_and_give
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def mint_and_give(self, params):
        """Give away some reserved NFTs"""
        sp.set_type(params, sp.TRecord(amount=sp.TNat, address=sp.TAddress))
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())
        # All events must be closed
        sp.verify(~self.is_any_event_open(), message=Error.ErrorMessage.sale_event_already_open())

        # Mint token(s) and transfer them to user
        self.mint_internal(amount=params.amount, address=params.address)

        event = sp.record(sender=sp.sender, receiver=params.address, amount=params.amount)
        sp.emit(event, with_type=True, tag="mint_and_give")

########################################################################################################################
# set_next_administrator
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def set_next_administrator(self, params):
        """Change admin. Only the admin can change to another admin"""
        sp.set_type(params, sp.TAddress)
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.not_admin())
        self.data.next_administrator = sp.some(params)

########################################################################################################################
# validate_new_administrator
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def validate_new_administrator(self):
        sp.verify(self.data.next_administrator.is_some(), message=Error.ErrorMessage.no_next_admin())
        sp.verify(sp.sender == self.data.next_administrator.open_some(), message=Error.ErrorMessage.not_admin())
        self.data.administrator = self.data.next_administrator.open_some()
        self.data.next_administrator = sp.none

########################################################################################################################
# set_multisig_fund_address
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def set_multisig_fund_address(self, params):
        """Change the addresses where Tez are transfered. Reserve to Admin"""
        sp.set_type(params, sp.TAddress)
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())
        self.data.multisig_fund_address = params

########################################################################################################################
# register_fa2
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def register_fa2(self, params):
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())
        sp.set_type(params, sp.TAddress)
        self.data.fa2 = params

########################################################################################################################
# clear_allowlist
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def clear_allowlist(self):
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())
        sp.verify(~self.is_any_event_open(), message=Error.ErrorMessage.sale_event_already_open())
        self.clear_storage()
        self.data.state = STATE_NO_EVENT_OPEN_0
        self.data.allowlist = sp.set(l={}, t=sp.TAddress)
        self.data.pre_allowlist = sp.set(l={}, t=sp.TAddress)

        sp.emit(sp.unit, with_type=True, tag="clear_allowlist")

########################################################################################################################
# admin_process_presale
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def admin_process_presale(self, params):
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())
        sp.verify(~self.is_any_event_open(), message=Error.ErrorMessage.sale_event_already_open())
        sp.set_type(params, sp.TAddress)

        tokens = sp.local('tokens', sp.view("all_tokens", params, sp.unit).open_some(message=Error.ErrorMessage.invalid_parameter()))

        burn_list = sp.local("burn_list", sp.list(l={}, t=sp.TNat))
        sp.for token in tokens.value:
            is_burn = sp.local('is_burn', sp.view("is_token_burned", params, token).open_some(message=Error.ErrorMessage.invalid_parameter()))

            sp.if ~is_burn.value:
                owner = sp.local('owner', sp.view("get_token_owner", params, token).open_some(message=Error.ErrorMessage.invalid_parameter()))
                self.mint_internal(amount=1, address=owner.value)
                burn_list.value.push(token)

        presale_contract_handle = sp.contract(
            sp.TList(sp.TNat),
            params,
            "burn"
        ).open_some("Interface mismatch")

        presale_contract_arg = burn_list.value
        self.call(presale_contract_handle, presale_contract_arg)


########################################################################################################################
# mutez_transfer
########################################################################################################################
    @sp.entry_point(check_no_incoming_transfer=True)
    def mutez_transfer(self, params):
        sp.verify(self.is_administrator(), message=Error.ErrorMessage.unauthorized_user())
        sp.set_type(params.destination, sp.TAddress)
        sp.set_type(params.amount, sp.TMutez)
        sp.send(params.destination, params.amount)

########################################################################################################################
# Helpers
########################################################################################################################
    def call(self, destination, arg):
        sp.transfer(arg, sp.mutez(0), destination)

    def is_administrator(self):
        return sp.sender == self.data.administrator

    def clear_storage(self):
        self.data.event_price = sp.mutez(0)
        self.data.event_max_supply = sp.nat(0)
        self.data.event_max_per_user = sp.nat(0)
        self.data.event_user_balance = sp.big_map(l={}, tkey=sp.TAddress, tvalue=sp.TNat)
        self.data.public_allowlist_max_space = sp.nat(0)
        self.data.public_allowlist_space_taken = sp.nat(0)
        self.data.public_sale_allowlist_config.used = False
        self.data.public_sale_allowlist_config.discount = sp.mutez(0)
        self.data.public_sale_allowlist_config.minting_rights = False
        self.data.token_minted_in_event = sp.nat(0)

    def stop_internal_event(self):
        self.clear_storage()
        sp.if self.data.state == STATE_EVENT_PRIV_ALLOWLIST_REG_1:
            self.data.state = STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2
        sp.else:
            sp.if (self.data.state == STATE_EVENT_PUB_ALLOWLIST_REG_3) | (self.data.state == STATE_EVENT_PRESALE_5) | (self.data.state == STATE_EVENT_PUBLIC_SALE_6):
                self.data.state = STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4
            sp.else:
                self.data.state = STATE_NO_EVENT_OPEN_0

    def mint_internal(self, amount, address):
        # Mint token(s) and transfer them to user
        minted = sp.local("minted", sp.nat(0))
        sp.while minted.value < amount: 
            sp.transfer(address, sp.mutez(0), sp.contract(FA2_MINT_PARAM_TYPE,
                                          self.data.fa2, entry_point="mint").open_some())
            minted.value = minted.value + 1

    def start_sale_init(self, max_supply, max_per_user, price):
        self.data.event_user_balance = sp.big_map(l={}, tkey=sp.TAddress, tvalue=sp.TNat)
        self.data.token_minted_in_event = 0
        self.data.event_max_supply = max_supply
        self.data.event_max_per_user = max_per_user
        self.data.event_price = price

    def is_any_event_open(self):
        return (self.data.state == STATE_EVENT_PRIV_ALLOWLIST_REG_1) | \
               (self.data.state == STATE_EVENT_PUB_ALLOWLIST_REG_3) | \
               (self.data.state == STATE_EVENT_PRESALE_5) | \
               (self.data.state == STATE_EVENT_PUBLIC_SALE_6)

    def check_amount_and_transfer_tez(self, amount_requested, token_price):
        sp.verify(sp.amount == sp.mul(amount_requested, token_price)
                  , message=Error.ErrorMessage.invalid_amount())
        # Transfer Tez received from user
        self.redirect_fund(sp.amount)

    def mint_pre_sale(self, params):
        # Pre-sale. Must be on the allow list
        sp.verify(self.data.allowlist.contains(params.address), message=Error.ErrorMessage.forbidden_operation())

        # Enough supply
        sp.verify(self.data.token_minted_in_event + params.amount <= self.data.event_max_supply,
                  message=Error.ErrorMessage.sale_no_token())

        # User minted his token already ?
        user_balance = sp.local("user_balance", self.data.event_user_balance.get(params.address, 0))

        sp.verify(user_balance.value + params.amount <= self.data.event_max_per_user,
                  message=Error.ErrorMessage.sale_no_token())

        # User gave the right amount of Tez. If yes transfer these Tez to the transfer address
        self.check_amount_and_transfer_tez(params.amount, self.data.event_price)
        self.mint_internal(params.amount, params.address)

        self.data.event_user_balance[params.address] = user_balance.value + params.amount
        self.data.token_minted_in_event = self.data.token_minted_in_event + params.amount

    def mint_public_sale(self, params):
        sp.if ~(self.data.allowlist.contains(params.address) & self.data.public_sale_allowlist_config.minting_rights):
            sp.verify(self.data.token_minted_in_event + params.amount <= self.data.event_max_supply,
                      message=Error.ErrorMessage.sale_no_token())
            self.data.token_minted_in_event = self.data.token_minted_in_event + params.amount

        # User minted his token already ?
        user_event_balance = sp.local("user_event_balance", self.data.event_user_balance.get(params.address, 0))

        sp.verify(user_event_balance.value + params.amount <= self.data.event_max_per_user,
                  message=Error.ErrorMessage.forbidden_operation())

        # User gave the right amount of Tez. If yes transfer these Tez to the transfer address
        sp.if self.data.allowlist.contains(params.address):
            self.check_amount_and_transfer_tez(params.amount,
                                               self.data.event_price - self.data.public_sale_allowlist_config.discount)
        sp.else:
            self.check_amount_and_transfer_tez(params.amount, self.data.event_price)

        self.mint_internal(params.amount, params.address)

        self.data.event_user_balance[params.address] = user_event_balance.value + params.amount

    def redirect_fund(self, amount):
        sp.if amount > sp.mutez(0):
            sp.send(self.data.multisig_fund_address, amount)
