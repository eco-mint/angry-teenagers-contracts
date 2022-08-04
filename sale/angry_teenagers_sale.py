import smartpy as sp

Error = sp.io.import_script_from_url("file:angry_teenagers_errors.py")

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
ADMIN_OPEN_EVENT_PRIVATE_ALLOWLIST_REGISTRATION_PARAM_TYPE = sp.TRecord(price=sp.TMutez, use_deadline=sp.TBool, deadline=sp.TTimestamp)
ADMIN_OPEN_EVENT_PUBLIC_ALLOWLIST_REGISTRATION_PARAM_TYPE = sp.TRecord(max_space=sp.TNat, price=sp.TMutez, use_deadline=sp.TBool, deadline=sp.TTimestamp)
ADMIN_OPEN_PRE_SALE_PARAM_TYPE=sp.TRecord(max_supply=sp.TNat, max_per_user=sp.TNat, price=sp.TMutez, use_deadline=sp.TBool, deadline=sp.TTimestamp)
ADMIN_OPEN_PUBLIC_SALE_PARAM_TYPE=sp.TRecord(max_supply=sp.TNat, max_per_user=sp.TNat, price=sp.TMutez, use_deadline=sp.TBool, deadline=sp.TTimestamp)
ADMIN_OPEN_PUBLIC_SALE_WITH_ALLOWLIST_PARAM_TYPE=sp.TRecord(max_supply=sp.TNat, max_per_user=sp.TNat, price=sp.TMutez, use_deadline=sp.TBool, deadline=sp.TTimestamp, mint_right=sp.TBool, mint_discount=sp.TMutez)
ADMIN_UPDATE_TOKEN_METADATA_PARAM_TYPE = sp.TList(FA2_UPDATE_TOKEN_METADATA_PARAM_TYPE)
ADMIN_TRANSFER_ADDRESSES_TYPE = sp.TList(sp.TPair(sp.TAddress, sp.TNat))

########################################################################################################################
########################################################################################################################
# Class AngryTeenager Sale (the contract)
########################################################################################################################
########################################################################################################################
class AngryTeenagersSale(sp.Contract):
    def __init__(self, admin, transfer_addresses, metadata):
        self.init(
            administrator=admin,
            transfer_addresses=transfer_addresses,
            fa2=sp.address('KT1XmD6SKw6CFoxmGseB3ttws5n8sTXYkKkq'),

            state=sp.nat(STATE_NO_EVENT_OPEN_0),

            allowlist=sp.set(l={}, t=sp.TAddress),
            pre_allowlist=sp.set(l={}, t=sp.TAddress),

            event_price=sp.mutez(0),
            event_max_supply=sp.nat(0),
            event_max_per_user=sp.nat(0),

            event_deadline=sp.timestamp(0),
            event_use_deadline=sp.bool(False),
            event_user_balance=sp.big_map(l={}, tkey=sp.TAddress, tvalue=sp.TNat),

            public_allowlist_max_space=sp.nat(0),
            public_allowlist_space_taken=sp.nat(0),
            public_sale_allowlist_config=sp.record(used=sp.bool(False), discount=sp.mutez(0), minting_rights=sp.bool(False)),

            token_index=sp.nat(0),
            token_minted_in_event=sp.nat(0),

            metadata=metadata
        )
        list_of_views = [
            self.get_mint_token_available
        ]

        metadata_base = {
            "version": "1.0"
            , "description": (
                "Angry Teenagers Crowdsale"
            )
            , "interfaces": ["TZIP-016", "TZIP-021"]
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
# off-chain function
########################################################################################################################
    @sp.offchain_view(pure=True)
    def get_mint_token_available(self, params):
        """
        Return the number of token an address can mint"""
        # This may be a problem and makes it harder to be consistent. The total supply is defined by the lands available.
        # We can add some protection with a view.
        sp.set_type(params, sp.TAddress)

        user_balance = sp.local('balance', 0)
        sp.if self.data.event_user_balance.contains(params):
            user_balance.value = self.data.event_user_balance[params]

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
    @sp.entry_point
    def admin_fill_allowlist(self, params):
        """Admin fill the allowlist"""
        sp.set_type(params, ADMIN_FILL_ALLOWLIST_PARAM_TYPE)

        # Only for admin
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2) |
                  (self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4),
                  Error.ErrorMessage.sale_event_already_open())

        sp.for item in params.elements():
            sp.if ~self.data.allowlist.contains(item):
                self.data.allowlist.add(item)

########################################################################################################################
# admin_fill_pre_allowlist
########################################################################################################################
    @sp.entry_point
    def admin_fill_pre_allowlist(self, params):
        """Add a set of addresses to the pre_allowlist_entry"""
        sp.set_type(params, ADMIN_FILL_PRE_ALLOWLIST_PARAM_TYPE)

        # Only for admin
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        # This can be called only in state STATE_NO_EVENT_OPEN_0
        sp.verify(self.data.state == STATE_NO_EVENT_OPEN_0, Error.ErrorMessage.sale_event_already_open())

        sp.for item in params.elements():
            sp.if ~self.data.pre_allowlist.contains(item):
                self.data.pre_allowlist.add(item)

########################################################################################################################
# admin_open_event_private_allowlist
########################################################################################################################
    @sp.entry_point
    def open_event_priv_allowlist_reg(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        # This can be called only in state STATE_NO_EVENT_OPEN_0
        sp.verify(self.data.state == STATE_NO_EVENT_OPEN_0, Error.ErrorMessage.sale_event_already_open())

        sp.set_type(params, ADMIN_OPEN_EVENT_PRIVATE_ALLOWLIST_REGISTRATION_PARAM_TYPE)

        sp.if params.use_deadline:
            sp.verify(params.deadline > sp.now, Error.ErrorMessage.sale_invalid_deadline())

        self.data.event_price=params.price
        self.data.event_use_deadline = params.use_deadline
        self.data.event_deadline = params.deadline

        # Go to state STATE_EVENT_PRIV_ALLOWLIST_REG_1
        self.data.state = STATE_EVENT_PRIV_ALLOWLIST_REG_1

########################################################################################################################
# pay_to_enter_allowlist_priv
########################################################################################################################
    @sp.entry_point
    def pay_to_enter_allowlist_priv(self):
        self.check_event_duration()
        # Only in state STATE_EVENT_PRIV_ALLOWLIST_REG_1
        sp.verify(self.data.state == STATE_EVENT_PRIV_ALLOWLIST_REG_1, Error.ErrorMessage.sale_event_already_open())

        # Must be on the pre_allowlist
        sp.verify(self.data.pre_allowlist.contains(sp.sender), Error.ErrorMessage.forbidden_operation())
        sp.verify(sp.amount == self.data.event_price)
        self.redirect_fund(sp.amount)
        self.data.pre_allowlist.remove(sp.sender)
        self.data.allowlist.add(sp.sender)

########################################################################################################################
# open_event_pub_allowlist_reg
########################################################################################################################
    @sp.entry_point
    def open_event_pub_allowlist_reg(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        # This can be called only in state STATE_NO_EVENT_OPEN_0 or STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2
        sp.verify((self.data.state == STATE_NO_EVENT_OPEN_0) | (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2), Error.ErrorMessage.sale_event_already_open())
        sp.verify(params.max_space > 0, Error.ErrorMessage.invalid_parameter())
        sp.if params.use_deadline:
            sp.verify(params.deadline > sp.now, Error.ErrorMessage.sale_invalid_deadline())

        sp.set_type(params, ADMIN_OPEN_EVENT_PUBLIC_ALLOWLIST_REGISTRATION_PARAM_TYPE)

        self.data.public_allowlist_max_space = params.max_space
        self.data.public_allowlist_space_taken = 0
        self.data.event_price=params.price
        self.data.event_use_deadline = params.use_deadline
        self.data.event_deadline = params.deadline

        # Go to state STATE_EVENT_PUB_ALLOWLIST_REG_3
        self.data.state = STATE_EVENT_PUB_ALLOWLIST_REG_3

########################################################################################################################
# pay_to_enter_allowlist_pub
########################################################################################################################
    @sp.entry_point
    def pay_to_enter_allowlist_pub(self):
        self.check_event_duration()

        # Only in state STATE_EVENT_PUB_ALLOWLIST_REG_3
        sp.verify(self.data.state == STATE_EVENT_PUB_ALLOWLIST_REG_3, Error.ErrorMessage.sale_event_already_open())

        # Not already in the list
        sp.verify(~self.data.allowlist.contains(sp.sender), Error.ErrorMessage.forbidden_operation())

        # Enough space remaining
        sp.verify(self.data.public_allowlist_space_taken < self.data.public_allowlist_max_space,
                  Error.ErrorMessage.sale_no_space_remaining())

        sp.verify(sp.amount == self.data.event_price)
        self.redirect_fund(sp.amount)

        self.data.public_allowlist_space_taken = self.data.public_allowlist_space_taken + 1
        self.data.allowlist.add(sp.sender)

        sp.if self.data.public_allowlist_space_taken >= self.data.public_allowlist_max_space:
            self.stop_internal_event()

########################################################################################################################
# open_pre_sale
########################################################################################################################
    @sp.entry_point
    def open_pre_sale(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2) |
                  (self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4), Error.ErrorMessage.sale_event_already_open())

        # check parameters
        sp.set_type(params, ADMIN_OPEN_PRE_SALE_PARAM_TYPE)
        sp.verify(params.max_supply > 0, Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_per_user > 0, Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_supply > params.max_per_user, Error.ErrorMessage.invalid_parameter())
        sp.if params.use_deadline:
            sp.verify(params.deadline > sp.now, Error.ErrorMessage.sale_invalid_deadline())

        self.start_sale_init(params.max_supply, params.max_per_user, params.price, params.use_deadline, params.deadline)

        self.data.state = STATE_EVENT_PRESALE_5

########################################################################################################################
# open_pub_sale
########################################################################################################################
    @sp.entry_point
    def open_pub_sale(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4) |
                  (self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2),
                  Error.ErrorMessage.sale_event_already_open())

        # check parameters
        sp.set_type(params, ADMIN_OPEN_PRE_SALE_PARAM_TYPE)
        sp.verify(params.max_supply > 0, Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_per_user > 0, Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_supply > params.max_per_user, Error.ErrorMessage.invalid_parameter())
        sp.if params.use_deadline:
            sp.verify(params.deadline > sp.now, Error.ErrorMessage.sale_invalid_deadline())

        self.data.public_sale_allowlist_config.used = False
        self.data.public_sale_allowlist_config.discount = sp.mutez(0)
        self.data.public_sale_allowlist_config.minting_rights = False

        self.start_sale_init(params.max_supply, params.max_per_user, params.price, params.use_deadline, params.deadline)

        self.data.state = STATE_EVENT_PUBLIC_SALE_6

########################################################################################################################
# open_pub_sale_with_allowlist
########################################################################################################################
    @sp.entry_point
    def open_pub_sale_with_allowlist(self, params):
        # Only for admin
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        sp.verify((self.data.state == STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4) |
                  (self.data.state == STATE_NO_EVENT_OPEN_0) |
                  (self.data.state == STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2),
                  Error.ErrorMessage.sale_event_already_open())

        # check parameters
        sp.set_type(params, ADMIN_OPEN_PUBLIC_SALE_WITH_ALLOWLIST_PARAM_TYPE)
        sp.verify(params.max_supply > 0, Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_per_user > 0, Error.ErrorMessage.invalid_parameter())
        sp.verify(params.max_supply > params.max_per_user, Error.ErrorMessage.invalid_parameter())
        sp.verify(params.price >= params.mint_discount, Error.ErrorMessage.invalid_parameter())
        sp.if params.use_deadline:
            sp.verify(params.deadline > sp.now, Error.ErrorMessage.sale_invalid_deadline())

        self.data.public_sale_allowlist_config.used = True
        self.data.public_sale_allowlist_config.discount = params.mint_discount
        self.data.public_sale_allowlist_config.minting_rights = params.mint_right

        self.start_sale_init(params.max_supply, params.max_per_user, params.price, params.use_deadline, params.deadline)

        self.data.state = STATE_EVENT_PUBLIC_SALE_6

########################################################################################################################
# set_metadata
########################################################################################################################
    @sp.entry_point
    def set_metadata(self, k, v):
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        self.data.metadata[k] = v

########################################################################################################################
# user_mint
########################################################################################################################
    @sp.entry_point
    def user_mint(self, params):
        self.check_event_duration()
        sp.set_type(params, sp.TNat)

        sp.verify(params > 0, Error.ErrorMessage.sale_no_token())
        sp.verify(params <= self.data.event_max_per_user, Error.ErrorMessage.sale_no_token())

        sp.if self.data.state == STATE_EVENT_PRESALE_5:
            self.mint_pre_sale(params)
        sp.else:
            sp.if self.data.state == STATE_EVENT_PUBLIC_SALE_6:
                self.mint_public_sale(params)
            sp.else:
                sp.failwith(Error.ErrorMessage.forbidden_operation())

########################################################################################################################
# close_any_open_event
########################################################################################################################
    @sp.entry_point
    def close_any_open_event(self):
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())

        sp.verify(self.is_any_event_open(), Error.ErrorMessage.sale_no_event_open())
        self.stop_internal_event()

########################################################################################################################
# mint_and_give
########################################################################################################################
    @sp.entry_point
    def mint_and_give(self, params):
        """Give away some reserved NFTs"""
        sp.set_type(params, sp.TRecord(amount=sp.TNat, address=sp.TAddress))
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        # All events must be closed
        sp.verify(~self.is_any_event_open(), Error.ErrorMessage.sale_event_already_open())

        # Mint token(s) and transfer them to user
        self.mint_internal(amount=params.amount, address=params.address)

########################################################################################################################
# set_administrator
########################################################################################################################
    @sp.entry_point
    def set_administrator(self, params):
        """Change admin. Only the admin can change to another admin"""
        sp.set_type(params, sp.TAddress)
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        self.data.administrator = params

########################################################################################################################
# set_transfer_addresses
########################################################################################################################
    @sp.entry_point
    def set_transfer_addresses(self, params):
        """Change the addresses where Tez are transfered. Reserve to Admin"""
        sp.set_type(params, ADMIN_TRANSFER_ADDRESSES_TYPE)
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        total = sp.local("total", sp.nat(0))
        self.data.transfer_addresses = params
        sp.for address in params:
            sp.verify(sp.snd(address) > 0, Error.ErrorMessage.invalid_amount())
            total.value = total.value + sp.snd(address)
        sp.verify(total.value == 100, Error.ErrorMessage.invalid_amount())

########################################################################################################################
# set_fa2_administrator
########################################################################################################################
    @sp.entry_point
    def set_fa2_administrator(self, params):
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        sp.set_type(params, sp.TAddress)
        contract_params = sp.contract(sp.TAddress, self.data.fa2, entry_point="set_administrator").open_some()
        data_to_send = params
        sp.transfer(data_to_send, sp.mutez(0), contract_params)

########################################################################################################################
# register_fa2
########################################################################################################################
    @sp.entry_point
    def register_fa2(self, params):
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        sp.set_type(params, sp.TAddress)
        self.data.fa2 = params

########################################################################################################################
# clear_allowlist
########################################################################################################################
    @sp.entry_point
    def clear_allowlist(self):
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        sp.verify(~self.is_any_event_open(), Error.ErrorMessage.sale_event_already_open())
        self.clear_storage()
        self.data.state = STATE_NO_EVENT_OPEN_0
        self.data.allowlist = sp.set(l={}, t=sp.TAddress)
        self.data.pre_allowlist = sp.set(l={}, t=sp.TAddress)


########################################################################################################################
# mutez_transfer
########################################################################################################################
    @sp.entry_point
    def mutez_transfer(self, params):
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        sp.set_type(params.destination, sp.TAddress)
        sp.set_type(params.amount, sp.TMutez)
        sp.send(params.destination, params.amount)

########################################################################################################################
# Helpers
########################################################################################################################
    def is_administrator(self):
        return sp.sender == self.data.administrator

    def clear_storage(self):
        self.data.event_price = sp.mutez(0)
        self.data.event_max_supply = sp.nat(0)
        self.data.event_max_per_user = sp.nat(0)
        self.data.event_use_deadline = False
        self.data.event_deadline =sp.timestamp(0)
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

    def check_event_duration(self):
        sp.if self.is_any_event_open():
            sp.if self.data.event_use_deadline:
                sp.if sp.now >= self.data.event_deadline:
                    self.stop_internal_event()

    def mint_internal(self, amount, address):
        # Mint token(s) and transfer them to user
        minted = sp.local("minted", sp.nat(0))
        sp.while minted.value < amount:
            contract_params = sp.contract(FA2_MINT_PARAM_TYPE,
                                          self.data.fa2, entry_point="mint").open_some()
            sp.transfer(address, sp.mutez(0), contract_params)
            minted.value = minted.value + 1

        self.data.token_index = self.data.token_index + amount

    def start_sale_init(self, max_supply, max_per_user, price, use_deadline, deadline):
        self.data.event_user_balance = sp.big_map(l={}, tkey=sp.TAddress, tvalue=sp.TNat)
        self.data.token_minted_in_event = 0
        self.data.event_max_supply = max_supply
        self.data.event_max_per_user = max_per_user
        self.data.event_price = price
        self.data.event_use_deadline = use_deadline
        self.data.event_deadline = deadline

    def is_any_event_open(self):
        return (self.data.state == STATE_EVENT_PRIV_ALLOWLIST_REG_1) | \
               (self.data.state == STATE_EVENT_PUB_ALLOWLIST_REG_3) | \
               (self.data.state == STATE_EVENT_PRESALE_5) | \
               (self.data.state == STATE_EVENT_PUBLIC_SALE_6)

    def check_amount_and_transfer_tez(self, amount_requested, token_price):
        sp.verify(sp.amount == sp.mul(amount_requested, token_price)
                  , Error.ErrorMessage.invalid_amount())
        # Transfer Tez received from user
        self.redirect_fund(sp.amount)

    def mint_pre_sale(self, params):
        # Pre-sale. Must be on the allow list
        sp.verify(self.data.allowlist.contains(sp.sender), Error.ErrorMessage.forbidden_operation())

        # Enough supply
        sp.verify(self.data.token_minted_in_event + params <= self.data.event_max_supply,
                  Error.ErrorMessage.sale_no_token())

        # User minted his token already ?
        sp.if self.data.event_user_balance.contains(sp.sender):
            sp.verify(self.data.event_user_balance[sp.sender] + params <= self.data.event_max_per_user,
                      Error.ErrorMessage.sale_no_token())

        # User gave the right amount of Tez. If yes transfer these Tez to the transfer address
        self.check_amount_and_transfer_tez(params, self.data.event_price)
        self.mint_internal(params, sp.sender)

        sp.if self.data.event_user_balance.contains(sp.sender):
            self.data.event_user_balance[sp.sender] = self.data.event_user_balance[sp.sender] + params
        sp.else:
            self.data.event_user_balance[sp.sender] = params

        self.data.token_minted_in_event = self.data.token_minted_in_event + params

    def mint_public_sale(self, params):
        sp.if ~(self.data.allowlist.contains(sp.sender) & self.data.public_sale_allowlist_config.minting_rights):
            sp.verify(self.data.token_minted_in_event + params <= self.data.event_max_supply,
                      Error.ErrorMessage.sale_no_token())
            self.data.token_minted_in_event = self.data.token_minted_in_event + params

        # User minted his token already ?
        sp.if self.data.event_user_balance.contains(sp.sender):
            sp.verify(self.data.event_user_balance[sp.sender] + params <= self.data.event_max_per_user,
                      Error.ErrorMessage.forbidden_operation())

        # User gave the right amount of Tez. If yes transfer these Tez to the transfer address
        sp.if self.data.allowlist.contains(sp.sender):
            self.check_amount_and_transfer_tez(params,
                                               self.data.event_price - self.data.public_sale_allowlist_config.discount)
        sp.else:
            self.check_amount_and_transfer_tez(params, self.data.event_price)

        self.mint_internal(params, sp.sender)

        sp.if self.data.event_user_balance.contains(sp.sender):
            self.data.event_user_balance[sp.sender] = self.data.event_user_balance[sp.sender] + params
        sp.else:
            self.data.event_user_balance[sp.sender] = params

    def redirect_fund(self, amount):
        sp.for item in self.data.transfer_addresses:
            (address, percent) = sp.match_pair(item)
            (quotient, remainder) = sp.match_pair(sp.ediv(sp.mul(amount, percent), 100).open_some())
            sp.send(address, quotient)

########################################################################################################################
########################################################################################################################
# Testing
########################################################################################################################
##################################################################################################################
# Unit Test ------------------------------------------------------------------------------------------------------------
Angry_Teenager_NFT = sp.io.import_script_from_url("file:./nft/angry_teenagers_nft.py")

########################################################################################################################
# Helper class for unit testing
########################################################################################################################
class TestHelper():
    class FundReceiverAccount(sp.Contract):
        def __init__(self):
            self.init()

    def create_scenario(name):
        scenario = sp.test_scenario()
        scenario.h1(name)
        scenario.table_of_contents()
        return scenario

    def create_contracts(scenario, admin, john):
        c1 = AngryTeenagersSale(admin.address, sp.list([sp.pair(admin.address, sp.nat(85)), sp.pair(john.address, sp.nat(15))]), sp.utils.metadata_of_url("https://example.com"))
        scenario += c1
        c2  = Angry_Teenager_NFT.AngryTeenagers(administrator=admin.address,
                                               royalties_bytes=sp.utils.bytes_of_string('{"decimals": 2, "shares": { "tz1b7np4aXmF8mVXvoa9Pz68ZRRUzK9qHUf5": 10}}'),
                                               metadata=sp.utils.metadata_of_url("https://example.com"),
                                               generic_image_ipfs=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                                               generic_image_ipfs_thumbnail=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBDH"),
                                               project_oracles_stream=sp.utils.bytes_of_string("ceramic://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYAAA"),
                                               what3words_file_ipfs=sp.utils.bytes_of_string("ipfs://QmWkrkZj562duMGVwwaUtPo7iH1zPtLYKB2u9M7EfUYBD3"),
                                               total_supply=5236)
        scenario += c2
        c1.register_fa2(c2.address).run(valid=True, sender=admin)
        c2.set_administrator(c1.address).run(valid=True, sender=admin)

        scenario.h2("Contracts:")
        scenario.p("c1: This sale contract to test")
        scenario.p("c2: The underlying FA2 contract (tested in ./contracts/nft/angry_teenagers_nft.py)")

        return c1, c2

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
# Description: Test the storage is initialized as expected.
# ----------------------------------------------------------------------------------------------------------------------
# Created contracts:
#   c1: This sale contract
#   c2: The underlying FA2 contract (tested in ./contracts/nft/angry_teenagers_nft.py)
# Created accounts:
#   admin
#   alice
#   bob
#   john
# ----------------------------------------------------------------------------------------------------------------------
# Scenario:
# 1. Create contracts and accounts
# 2.
# ----------------------------------------------------------------------------------------------------------------------
def unit_test_initial_storage(is_default = True):
    @sp.add_test(name="unit_test_initial_storage", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_initial_storage")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the storage is initialized as expected.")

        scenario.p("1. Read each entry of the storage of the c1 contract and check it is initialized as expected")
        scenario.verify(c1.data.administrator == admin.address)
        scenario.verify(c1.data.fa2 == c2.address)
        scenario.verify(c1.data.metadata[""] == sp.utils.bytes_of_string("https://example.com"))

        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        scenario.verify(sp.len(c1.data.pre_allowlist) == 0)

        scenario.verify(c1.data.event_price == sp.mutez(0))
        scenario.verify(c1.data.event_max_supply == sp.nat(0))
        scenario.verify(c1.data.event_max_per_user == sp.nat(0))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

        scenario.verify(c1.data.public_allowlist_max_space == sp.nat(0))
        scenario.verify(c1.data.public_allowlist_space_taken == sp.nat(0))
        scenario.verify(c1.data.public_sale_allowlist_config == sp.record(used=sp.bool(False), discount=sp.mutez(0),
                                                 minting_rights=sp.bool(False)))

        scenario.verify(c1.data.token_index == sp.nat(0))
        scenario.verify(c1.data.token_minted_in_event == sp.nat(0))

########################################################################################################################
# unit_test_admin_fill_allowlist
########################################################################################################################
def unit_test_admin_fill_allowlist(is_default = True):
    @sp.add_test(name="unit_test_admin_fill_allowlist", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_admin_fill_allowlist")
        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint used to fill the allowlist. (Who: Only for admin)")
        scenario.p("1. Verify the state of the contract is as expected (see state machine at the top of this file)")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

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
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))
        scenario.verify(sp.len(c1.data.pre_allowlist) == 0)

        scenario.p("5. Add another entry successfully to the allowlist and make the same verification than in step 5")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, john.address], t=sp.TAddress)).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))
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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the entrypoint used to fill the pre-allowlist (Who: Only for admin).")

        scenario.p("1. Verify the state of the contract is as expected (see state machine at the top of this file)")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

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
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))
        scenario.verify(sp.len(c1.data.pre_allowlist) == 2)
        scenario.verify(c1.data.pre_allowlist.contains(alice.address))
        scenario.verify(c1.data.pre_allowlist.contains(bob.address))
        scenario.verify(sp.len(c1.data.allowlist) == 0)

        scenario.p("5. Add another entry successfully to the pre-allowlist and make the same verification than in step 5")
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, john.address], t=sp.TAddress)).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))
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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_event_priv_allowlist_reg entrypoint. (Who: Only for admin).")
        scenario.p("This entrypoint opens an event where users in the pre-allowlist can register to the allowlist. The amount of XTZ to pay to enter to register to given as a parameter to this entrypoint. Deadline can be used. In this case, the event closes alone when the deadline is met.")

        scenario.p("1. Verify the state of the contract is as expected (see state machine at the top of this file)")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p(
            "2. Try to call the entrypoint with non-admin users. Verify it fails and the state of the contract stays unchanged.")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=bob)
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=alice)
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=john)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("3. Open successfully the event with the admin. Check the state of the contract is as expected.")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(c1.data.event_price == sp.tez(10))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

        scenario.p("4. Check event can be closed and then the state of the contract returns to the expected state.")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_WITH_PRIV_ALLOWLIST_READY_2))
        scenario.verify(c1.data.event_price == sp.tez(0))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

########################################################################################################################
# unit_test_pay_to_enter_allowlist_priv
########################################################################################################################
def unit_test_pay_to_enter_allowlist_priv(is_default = True):
    @sp.add_test(name="unit_test_pay_to_enter_allowlist_priv", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_pay_to_enter_allowlist_priv")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the pay_to_enter_allowlist_priv entrypoint. (Who: Only for the users in the pre-allowlist).")
        scenario.p("Users in the pre-allowlist can call this entrypoint and pay the configured XTZ price to register into the allowlist.")

        scenario.p("1. Fill the pre-allowlist")
        c1.admin_fill_pre_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Verify the state of the contract")
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)

        scenario.p("3. Open the event to register into the allowlist for users in the pre-allowlist")
        scenario.p("4. Verify that:")
        scenario.p("4.1. Only users that pay the right amount of XTZ can register to the allowlist")
        scenario.p("4.2. Only users that are on the pre-allowlist can register into the allowlist")
        scenario.p("4.3. When users in the pre-allowlist pays the expected price, they are registered in the allowlist")
        c1.pay_to_enter_allowlist_priv().run(valid=False, sender=alice)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(5), sender=alice)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        c1.pay_to_enter_allowlist_priv().run(valid=True, amount=sp.tez(10), sender=alice)
        c1.pay_to_enter_allowlist_priv().run(valid=True, amount=sp.tez(10), sender=bob)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PRIV_ALLOWLIST_REG_1))
        scenario.verify(sp.len(c1.data.allowlist) == 2)
        scenario.verify(c1.data.allowlist.contains(alice.address))
        scenario.verify(c1.data.allowlist.contains(bob.address))
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(10), sender=john)
        c1.pay_to_enter_allowlist_priv().run(valid=False, amount=sp.tez(10), sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PRIV_ALLOWLIST_REG_1))
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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_event_pub_allowlist_reg entrypoint. (Who: Only for the admin).")
        scenario.p("This entrypoint is used to open an event where any users can take a space in the allowlist by paying a price in XTZ (parameters to this entrypoint) as long as space are remaining. One user gets one spot max. A deadline can be defined to automatically close the event.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check only the admin can open this event")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(
            valid=False, sender=bob)
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(
            valid=False, sender=alice)
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(
            valid=False, sender=john)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("3. Check this entrypoint fails if the number of space allowed is 0")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=0, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(
            valid=False, sender=admin)

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=10,price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(
            valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PUB_ALLOWLIST_REG_3))
        scenario.verify(c1.data.public_allowlist_max_space == 10)
        scenario.verify(c1.data.public_allowlist_space_taken == 0)
        scenario.verify(c1.data.event_price == sp.tez(10))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.public_allowlist_max_space == 0)
        scenario.verify(c1.data.public_allowlist_space_taken == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

########################################################################################################################
# unit_test_pay_to_enter_allowlist_pub
########################################################################################################################
def unit_test_pay_to_enter_allowlist_pub(is_default = True):
    @sp.add_test(name="unit_test_pay_to_enter_allowlist_pub", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_pay_to_enter_allowlist_pub")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the pay_to_enter_allowlist_pub entrypoint. (Who: For all users).")
        scenario.p("This entrypoint is used by any users to register in the allowlist when the associated event (public allowlist registration) is used by paying the configured XTZ price. Users have only one spot in the allowlist.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Open the public allowlist registration event")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=2,price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(
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
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.public_allowlist_max_space == 0)
        scenario.verify(c1.data.public_allowlist_space_taken == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_pre_sale entrypoint. (Who: Only for the admin)")
        scenario.p("This entrypoint is used by the admin to open a pre-sale event. During a pre-sale, only users in the allowlist can mint tokens.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check that only admin can open a pre-sale")
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=bob)
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=alice)

        scenario.p("3. Check pre-sale can only be opened with consistent parameters")
        c1.open_pre_sale(sp.record(max_supply=0, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=admin)
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=0, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=admin)
        c1.open_pre_sale(sp.record(max_supply=2, max_per_user=6, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_pre_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PRESALE_5))
        scenario.verify(c1.data.event_max_supply == 6)
        scenario.verify(c1.data.event_max_per_user == 2)
        scenario.verify(c1.data.event_price == sp.tez(10))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.event_max_supply == 0)
        scenario.verify(c1.data.event_max_per_user == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

########################################################################################################################
# unit_test_open_pub_sale
########################################################################################################################
def unit_test_open_pub_sale(is_default = True):
    @sp.add_test(name="unit_test_open_pub_sale", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_open_pub_sale")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_pub_sale entrypoint. (Who: Only for the admin)")
        scenario.p("This entrypoint is used by the admin to open a public-sale event without the use of the allowlist.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check that only admin can open a public-sale")
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=bob)
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=alice)

        scenario.p("3. Check public-sale can only be opened with consistent parameters")
        c1.open_pub_sale(sp.record(max_supply=0, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=admin)
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=0, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=admin)
        c1.open_pub_sale(sp.record(max_supply=2, max_per_user=6, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_pub_sale(sp.record(max_supply=6, max_per_user=2, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PUBLIC_SALE_6))
        scenario.verify(c1.data.event_max_supply == 6)
        scenario.verify(c1.data.event_max_per_user == 2)
        scenario.verify(c1.data.event_price == sp.tez(10))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)
        scenario.verify(c1.data.public_sale_allowlist_config.used == False)
        scenario.verify(c1.data.public_sale_allowlist_config.discount == sp.tez(0))
        scenario.verify(c1.data.public_sale_allowlist_config.minting_rights == False)

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.event_max_supply == 0)
        scenario.verify(c1.data.event_max_per_user == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)

########################################################################################################################
# unit_test_open_pub_sale_with_allowlist
########################################################################################################################
def unit_test_open_pub_sale_with_allowlist(is_default = True):
    @sp.add_test(name="unit_test_open_pub_sale_with_allowlist", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_open_pub_sale_with_allowlist")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the open_pub_sale_with_allowlist entrypoint. (Who: Only for the admin)")
        scenario.p("This entrypoint is used by the admin to open a public-sale event with an allowlist.")

        scenario.p("1. Check the state of the contract is as expected")
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("2. Check that only admin can open a public-sale with allowlist")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           use_deadline=False,
                                                           deadline=sp.timestamp(0),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=bob)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           use_deadline=False,
                                                           deadline=sp.timestamp(0),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=alice)

        scenario.p("3. Check public-sale with allowlist can only be opened with consistent parameters")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=0,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           use_deadline=False,
                                                           deadline=sp.timestamp(0),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=admin)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=0,
                                                           price=sp.tez(10),
                                                           use_deadline=False,
                                                           deadline=sp.timestamp(0),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=admin)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=2,
                                                           max_per_user=6,
                                                           price=sp.tez(10),
                                                           use_deadline=False,
                                                           deadline=sp.timestamp(0),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(0))).run(valid=False, sender=admin)
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=2,
                                                           max_per_user=6,
                                                           price=sp.tez(10),
                                                           use_deadline=False,
                                                           deadline=sp.timestamp(0),
                                                           mint_right=False,
                                                           mint_discount=sp.tez(11))).run(valid=False, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_OPEN_0))

        scenario.p("4. Open the event successfully and:")
        scenario.p("4.1. Check the state of the contract is as expected")
        scenario.p("4.2. Check the event is configured as expected")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=6,
                                                           max_per_user=2,
                                                           price=sp.tez(10),
                                                           use_deadline=False,
                                                           deadline=sp.timestamp(0),
                                                           mint_right=True,
                                                           mint_discount=sp.tez(5))).run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_EVENT_PUBLIC_SALE_6))
        scenario.verify(c1.data.event_max_supply == 6)
        scenario.verify(c1.data.event_max_per_user == 2)
        scenario.verify(c1.data.event_price == sp.tez(10))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)
        scenario.verify(c1.data.public_sale_allowlist_config.used == True)
        scenario.verify(c1.data.public_sale_allowlist_config.discount == sp.tez(5))
        scenario.verify(c1.data.public_sale_allowlist_config.minting_rights == True)

        scenario.p("5. Close the event and:")
        scenario.p("5.1. Check the state of the contract is as expected")
        scenario.p("5.2. Check the event is closed as expected")
        c1.close_any_open_event().run(valid=True, sender=admin)
        scenario.verify(c1.data.state == sp.nat(STATE_NO_EVENT_WITH_PUB_ALLOWLIST_READY_4))
        scenario.verify(c1.data.event_max_supply == 0)
        scenario.verify(c1.data.event_max_per_user == 0)
        scenario.verify(c1.data.event_price == sp.tez(0))
        scenario.verify(c1.data.event_deadline == sp.timestamp(0))
        scenario.verify(c1.data.event_use_deadline == False)
        scenario.verify(c1.data.public_sale_allowlist_config.used == False)
        scenario.verify(c1.data.public_sale_allowlist_config.discount == sp.tez(0))
        scenario.verify(c1.data.public_sale_allowlist_config.minting_rights == False)

########################################################################################################################
# unit_test_set_fa2_administrator_function
########################################################################################################################
def unit_test_set_fa2_administrator_function(is_default=True):
    @sp.add_test(name="unit_test_set_fa2_administrator_function", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_fa2_administrator_function")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the set_fa2_administrator_function entrypoint. (Who: Only for the admin)")
        scenario.p("This function is used to set the admin of the underlying FA2 contract. A FA2 contract needs to be registered.")

        scenario.p("1. Check initial storage points on the expected admin address")
        scenario.verify(c2.data.administrator == c1.address)

        scenario.p("2. Check only admin can call this entrypoint")
        c1.set_fa2_administrator(bob.address).run(valid=False, sender=alice)
        c1.set_fa2_administrator(bob.address).run(valid=False, sender=bob)
        c1.set_fa2_administrator(bob.address).run(valid=False, sender=john)

        scenario.p("3. Check administrator of FA2 contract in the FA2 contract storage is as expected after a change")
        c1.set_fa2_administrator(bob.address).run(valid=True, sender=admin)
        scenario.verify(c2.data.administrator == bob.address)

########################################################################################################################
# unit_test_mint_and_give
########################################################################################################################
def unit_test_mint_and_give(is_default=True):
    @sp.add_test(name="unit_test_mint_and_give", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mint_and_give")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the mint_and_give entrypoint. (Who: Only for the admin)")
        scenario.p("This function is used by the admin to mint and give tokens when no sales event are opened.")

        scenario.p("1. Check only admin can call this entrypoint")
        c1.mint_and_give(sp.record(amount=1, address=bob.address)).run(valid=False, sender=alice)
        c1.mint_and_give(sp.record(amount=2, address=bob.address)).run(valid=True, sender=admin)

        scenario.p("2. Open a public safe")
        c1.open_pub_sale(sp.record(max_supply=100,
                                                           max_per_user=80,
                                                           price=sp.tez(10),
                                                           use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)

        scenario.p("3. Check this entrypoint cannot be called when a sale is opened")
        c1.mint_and_give(sp.record(amount=2, address=bob.address)).run(valid=False, sender=admin)
        c1.user_mint(80).run(valid=True, amount=sp.mutez(800000000), sender=alice)

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
# unit_test_set_administrator
########################################################################################################################
def unit_test_set_administrator(is_default = True):
    @sp.add_test(name="unit_test_set_administrator", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_administrator")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

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
        scenario.verify(c1.data.administrator == bob.address)

########################################################################################################################
# unit_test_set_transfer_addresses
########################################################################################################################
def unit_test_set_transfer_addresses(is_default=True):
    @sp.add_test(name="unit_test_set_transfer_addresses", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_set_transfer_addresses")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the set_transfer_addresses entrypoint. (Who: Only for the admin)")
        scenario.p("The transfer addresses are used to redirect the fund received when a user mints a NFTs to wallet.")

        scenario.p("1. Check that only the admin can call this entrypoint")
        correct_param = sp.list([sp.pair(alice.address, 10), sp.pair(john.address, 90)])
        c1.set_transfer_addresses(correct_param).run(valid=False, sender=john)
        c1.set_transfer_addresses(correct_param).run(valid=False, sender=bob)
        c1.set_transfer_addresses(correct_param).run(valid=False, sender=alice)

        scenario.p("2. Check some invalid calls")
        c1.set_transfer_addresses(sp.list([sp.pair(alice.address, 15), sp.pair(john.address, 90)])).run(valid=False, sender=admin)
        c1.set_transfer_addresses(sp.list([sp.pair(alice.address, 99)])).run(valid=False, sender=admin)
        c1.set_transfer_addresses(sp.list([sp.pair(alice.address, 2), sp.pair(john.address, 19), sp.pair(bob.address, 80)])).run(valid=False, sender=admin)

        scenario.p("3. Change successfully the transfer address to Alice account and verify the storage is updated accordingly")
        c1.set_transfer_addresses(correct_param).run(valid=True, sender=admin)
        c1.set_transfer_addresses(sp.list([sp.pair(alice.address, 1), sp.pair(john.address, 19), sp.pair(bob.address, 80)])).run(valid=True, sender=admin)

########################################################################################################################
# unit_test_register_fa2
########################################################################################################################
def unit_test_register_fa2(is_default=True):
    @sp.add_test(name="unit_test_register_fa2", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_register_fa2")

        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_public_sale entrypoint. (Who: for all users)")
        scenario.p("This entrypoint is called by users to mint NFTs when a public sale is opened.")

        scenario.p("1. Check users cannot mint when event is not opened")
        c1.user_mint(8).run(valid=False, sender=alice)

        scenario.p("2. Start a public sale event without allowlist with a max supply of NFTs to mint and max NFTs to mint per user")
        c1.open_pub_sale(sp.record(max_supply=50,
                                            max_per_user=23,
                                            price=sp.tez(10),
                                            use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)

        scenario.p("3. Verify a users cannot mint more than allowed")
        c1.user_mint(24).run(valid=False, amount=sp.tez(240), sender=alice)

        scenario.p("4. Verify a user cannot mint 0 NFT")
        c1.user_mint(0).run(valid=False, amount=sp.tez(10), sender=alice)

        scenario.p("5. Verify a user cannot mint if he doesn't provide the right amount of XTZ")
        c1.user_mint(10).run(valid=False, amount=sp.mutez(0), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(100000), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(99999999), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(2123456), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(5555), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(100000001), sender=alice)

        scenario.p("7. Mint some NFTs")
        c1.user_mint(10).run(valid=True, amount=sp.tez(100), sender=alice)
        scenario.verify(c1.balance == sp.mutez(0))
        c1.user_mint(5).run(valid=True, amount=sp.tez(50), sender=john)
        scenario.verify(c1.balance == sp.mutez(0))
        c1.user_mint(3).run(valid=True, amount=sp.tez(30), sender=admin)
        scenario.verify(c1.balance == sp.tez(0))
        c1.user_mint(1).run(valid=True, amount=sp.tez(10), sender=bob)
        scenario.verify(c1.balance == sp.tez(0))
        # Only 31 token remaining in the current sale
        c1.user_mint(10).run(valid=True, amount=sp.tez(100), sender=alice)
        c1.user_mint(15).run(valid=True, amount=sp.tez(150), sender=bob)
        c1.user_mint(5).run(valid=True, amount=sp.tez(50), sender=bob)
        c1.user_mint(2).run(valid=False, amount=sp.tez(20), sender=alice)

        scenario.p("7. Verify users cannot mint more than total allocated supply")
        c1.user_mint(2).run(valid=False, amount=sp.tez(20), sender=alice)
        c1.user_mint(24).run(valid=False, amount=sp.tez(240), sender=john)

        scenario.p("8. One is still mintable. Mint it.")
        c1.user_mint(1).run(valid=True, amount=sp.tez(10), sender=alice)

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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_pre_sale entrypoint.  (Who: for all users in the allowlist)")
        scenario.p("This entrypoint is called by users to mint NFTs when a pre-sale is opened. to mint during pre-sale, a user needs to be registered in the allowlist.")

        scenario.p("1. Fill the allowlist")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address, john.address, admin.address], t=sp.TAddress)).\
            run(valid=True, sender=admin)

        scenario.p("2. Verify this entrypoint cannot be called when the associated event is not opened")
        c1.user_mint(8).run(valid=False, sender=alice)

        scenario.p("3. Start the pre-sale event")
        c1.open_pre_sale(sp.record(max_supply=50, max_per_user=23, price=sp.tez(10), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True,
                                                                                                          sender=admin)

        scenario.p("4. Verify users cannot mint more than the number of defined NFT per users")
        c1.user_mint(24).run(valid=False, amount=sp.tez(240), sender=alice)

        scenario.p("5. Verify cannot mint if not in the allowlist")
        c1.user_mint(10).run(valid=False, amount=sp.tez(100), sender=gabe)

        scenario.p("6. Verify user cannot mint 0 NFT")
        c1.user_mint(0).run(valid=False, amount=sp.tez(10), sender=alice)

        scenario.p("7. Verify user cannot mint if he does not provide the expected amount of XTZ")
        c1.user_mint(10).run(valid=False, amount=sp.mutez(0), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(100000), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(99999999), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(2123456), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(5555), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(100000001), sender=alice)

        scenario.p("8. Mint some NFTs")
        c1.user_mint(10).run(valid=True, amount=sp.tez(100), sender=alice)
        # Mint some more
        c1.user_mint(5).run(valid=True, amount=sp.tez(50), sender=john)
        scenario.verify(c1.balance == sp.mutez(0))
        # And again
        c1.user_mint(3).run(valid=True, amount=sp.tez(30), sender=admin)
        scenario.verify(c1.balance == sp.tez(0))
        c1.user_mint(1).run(valid=True, amount=sp.tez(10), sender=bob)
        scenario.verify(c1.balance == sp.tez(0))
        # Only 31 token remaining in the current sale
        c1.user_mint(10).run(valid=True, amount=sp.tez(100), sender=alice)
        c1.user_mint(15).run(valid=True, amount=sp.tez(150), sender=bob)
        c1.user_mint(5).run(valid=True, amount=sp.tez(50), sender=bob)
        c1.user_mint(2).run(valid=False, amount=sp.tez(20), sender=alice)

        scenario.p("8. Verify users cannot mint more than the total allocated supply")
        c1.user_mint(2).run(valid=False, amount=sp.tez(20), sender=alice)
        c1.user_mint(24).run(valid=False, amount=sp.tez(240), sender=john)

        scenario.p("9. One is still mintable. Mint it.")
        c1.user_mint(1).run(valid=True, amount=sp.tez(10), sender=alice)

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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_public_sale_with_allowlist_discount entrypoint.  (Who: for all users)")
        scenario.p("This entrypoint is called by users to mint NFTs when a public sale is opened using the allowlist and the associated discount. Any users can miint during the public sale but only the ones in the allowlist will have a discount.")

        scenario.p("1. Fill the allowlist")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Verify users cannot mint if no event are opened")
        c1.user_mint(8).run(valid=False, amount=sp.tez(80), sender=alice)

        scenario.p("3. Open a public sale with allowlist suing the discount feature")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=50,
                                            max_per_user=23,
                                            price=sp.tez(10),
                                            use_deadline=False,
                                            deadline=sp.timestamp(0),
                                            mint_right=False,
                                            mint_discount=sp.tez(5),
                                            )).run(valid=True, sender=admin)

        scenario.p("4. Verify users cannot mint more than the max numbers per user")
        c1.user_mint(24).run(valid=False, amount=sp.tez(120), sender=alice)

        scenario.p("5. Verify user cannot mint 0 NFT")
        c1.user_mint(0).run(valid=False, amount=sp.tez(5), sender=alice)

        scenario.p("6. Verify users can only mint if the they provide the right amount of XTZ")
        c1.user_mint(10).run(valid=False, amount=sp.mutez(0), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(100000), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(99999999), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(2123456), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(5555), sender=alice)
        c1.user_mint(10).run(valid=False, amount=sp.mutez(50000001), sender=alice)

        scenario.p("7. Mint some NFTs")
        scenario.p("8. Verify users in the allowlist get a discount")
        c1.user_mint(10).run(valid=True, amount=sp.tez(50), sender=alice)
        # Mint some more
        c1.user_mint(5).run(valid=True, amount=sp.tez(50), sender=john)
        scenario.verify(c1.balance == sp.mutez(0))
        # And again
        c1.user_mint(3).run(valid=True, amount=sp.tez(30), sender=admin)
        scenario.verify(c1.balance == sp.tez(0))
        c1.user_mint(1).run(valid=True, amount=sp.tez(5), sender=bob)
        scenario.verify(c1.balance == sp.tez(0))
        # Only 31 token remaining in the current sale
        c1.user_mint(10).run(valid=True, amount=sp.tez(50), sender=alice)
        c1.user_mint(15).run(valid=True, amount=sp.tez(75), sender=bob)
        c1.user_mint(5).run(valid=True, amount=sp.tez(25), sender=bob)
        c1.user_mint(2).run(valid=False, amount=sp.tez(10), sender=alice)

        scenario.p("9. Verify users cannot mint more than the total allocated supply")
        c1.user_mint(2).run(valid=False, amount=sp.tez(10), sender=alice)
        c1.user_mint(24).run(valid=False, amount=sp.tez(240), sender=john)

        scenario.p("9. One is still mintable. Mint it.")
        c1.user_mint(1).run(valid=True, amount=sp.tez(5), sender=alice)

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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the user_mint_during_public_sale_with_allowlist_mint_rights entrypoint.  (Who: for all users)")
        scenario.p("This entrypoint is called by users to mint NFTs when a public sale is opened using the allowlist and mint rights feature enabled. Any users can mint during the public sale. The ones in the allowlist have mint rights, meaning they can mint theirs NFTs (bounded by the defined max number of NFTs per user) even if all the total allocated supply is minted as long as the event is opened.")

        scenario.p("1. Fill the allowlist")
        c1.admin_fill_allowlist(sp.set(l=[alice.address, bob.address, nat.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Verify users cannot mint if no event are opened")
        c1.user_mint(8).run(valid=False, sender=alice)

        scenario.p("3. Start a public sale with minting rights enabled")
        c1.open_pub_sale_with_allowlist(sp.record(max_supply=100,
                                            max_per_user=30,
                                            price=sp.tez(10),
                                            use_deadline=False,
                                            deadline=sp.timestamp(0),
                                            mint_right=True,
                                            mint_discount=sp.tez(0),
                                            )).run(valid=True, sender=admin)

        scenario.p("4. Mint NFTs")
        c1.user_mint(30).run(valid=True, amount=sp.tez(300), sender=john)
        c1.user_mint(20).run(valid=True, amount=sp.tez(200), sender=nat)
        c1.user_mint(20).run(valid=True, amount=sp.tez(200), sender=ben)
        c1.user_mint(20).run(valid=True, amount=sp.tez(200), sender=gaston)
        c1.user_mint(30).run(valid=True, amount=sp.tez(300), sender=gabe)

        scenario.p("5. Verify users in the allowlist can always mint theirs NFTs even if all total supply is minted")
        c1.user_mint(10).run(valid=False, amount=sp.tez(100), sender=ben)
        c1.user_mint(10).run(valid=True, amount=sp.tez(100), sender=nat)
        c1.user_mint(30).run(valid=True, amount=sp.tez(300), sender=alice)
        c1.user_mint(20).run(valid=True, amount=sp.tez(200), sender=bob)
        c1.user_mint(10).run(valid=True, amount=sp.tez(100), sender=bob)

########################################################################################################################
# unit_test_mutez_transfer
########################################################################################################################
def unit_test_mutez_transfer(is_default=True):
    @sp.add_test(name="unit_test_mutez_transfer", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("unit_test_mutez_transfer")

        admin, alice, bob, john = TestHelper.create_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test the mutez_transfer entrypoint.  (Who: Only for the admin)")
        scenario.p("This entrypoint is called byt the admin to extract fund on the contract. Normally no funds are supposed to be held in the contract however if something bad happens or somebody makes a mistake transfer, we still want to have the ability to extract the fund.")

        scenario.p("1. Add fund to the contract")
        c1.set_fa2_administrator(c2.address).run(valid=True, sender=admin, amount=sp.mutez(300000000))

        scenario.p("2. Check that only the admin can call this entrypoint")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=alice)
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=False, sender=bob)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(200000000))).run(valid=False, sender=john)

        scenario.p("3. Check the function extracts the fund as expected")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(200000000))).run(valid=True, sender=admin)
        c1.mutez_transfer(sp.record(destination=admin.address, amount=sp.mutez(100000000))).run(valid=True, sender=admin)

        scenario.p("3. Check no fund are remaining")
        c1.mutez_transfer(sp.record(destination=alice.address, amount=sp.mutez(100000000))).run(valid=False, sender=admin)

########################################################################################################################
# module_test_pre_sale_public_sale_with_allowlist
########################################################################################################################
def module_test_pre_sale_public_sale_with_allowlist(is_default=True):
    @sp.add_test(name="module_test_pre_sale_public_sale_with_allowlist", is_default=is_default)
    def test():
        scenario = TestHelper.create_scenario("module_test_pre_sale_public_sale_with_allowlist")
        admin, alice, bob, john, nat, ben, gabe, gaston, chris = TestHelper.create_more_account(scenario)
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test a scenario with a pre-sale and then a public sale with allowlist")

        scenario.p("1. Fill the allowlist with alice account")
        c1.admin_fill_allowlist(sp.set(l=[alice.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("2. Fill the pre-allowlist with bob, nat and gaston accounts")
        c1.admin_fill_pre_allowlist(sp.set(l=[bob.address, nat.address, gaston.address], t=sp.TAddress)).run(valid=True, sender=admin)

        scenario.p("3. Verify non admin accounts cannot open the private allowlist registration event")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(3), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=bob)

        scenario.p("4. Open a private allowlist registration event")
        c1.open_event_priv_allowlist_reg(sp.record(price=sp.tez(3), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)

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
        c1.open_event_pub_allowlist_reg(sp.record(max_space=2, price=sp.tez(5), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=bob)

        scenario.p("15. Open the public allowlist registration event")
        c1.open_event_pub_allowlist_reg(sp.record(max_space=2, price=sp.tez(5), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)
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
        c1.open_pre_sale(sp.record(max_supply=50, max_per_user=15, price=sp.tez(100), use_deadline=False, deadline=sp.timestamp(0))).run(
            valid=False, sender=john)

        scenario.p("23. Successfully open a pre-sale event")
        c1.open_pre_sale(sp.record(max_supply=50, max_per_user=15, price=sp.tez(100), use_deadline=False, deadline=sp.timestamp(0))).run(
            valid=True, sender=admin)

        scenario.p("24. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(bob.address) == 15)
        scenario.verify(c1.get_mint_token_available(nat.address) == 15)
        scenario.verify(c1.get_mint_token_available(alice.address) == 15)
        scenario.verify(c1.get_mint_token_available(gabe.address) == 15)
        scenario.verify(c1.get_mint_token_available(admin.address) == 0)


        scenario.p("25. Verify users cannot mint more than the number of NFT mintable per user in this event")
        c1.user_mint(16).run(valid=False, amount=sp.tez(1600), sender=alice)


        scenario.p("26. Verify users shall pay the right amount of XTZ to mint")
        c1.user_mint(16).run(valid=False, amount=sp.tez(1495), sender=alice)
        c1.user_mint(15).run(valid=True, amount=sp.tez(1500), sender=alice)
        c1.user_mint(15).run(valid=True, amount=sp.tez(1500), sender=bob)
        scenario.verify(c1.get_mint_token_available(bob.address) == 0)

        scenario.p("27. Verify users cannot mint more than the total supply allocated in this event")
        c1.user_mint(10).run(valid=True, amount=sp.tez(1000), sender=nat)
        scenario.verify(c1.get_mint_token_available(nat.address) == 5)
        c1.user_mint(5).run(valid=True, amount=sp.tez(500), sender=gaston)
        # Not enough remaining
        c1.user_mint(6).run(valid=False, amount=sp.tez(600), sender=gabe)
        c1.user_mint(5).run(valid=True, amount=sp.tez(500), sender=gabe)

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
            use_deadline=False,
            deadline=sp.timestamp(0),
            mint_right=True,
            mint_discount=sp.tez(100))).run(valid=False, sender=ben)

        scenario.p("32. Successfully open a public sale with allowlist using the discount and mint right features")
        c1.open_pub_sale_with_allowlist(sp.record(
            max_supply=30,
            max_per_user=20,
            price=sp.tez(200),
            use_deadline=False,
            deadline=sp.timestamp(0),
            mint_right=True,
            mint_discount=sp.tez(100))).run(valid=True, sender=admin)

        scenario.p("33. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(alice.address) == 20)
        scenario.verify(c1.get_mint_token_available(john.address) == 20)
        scenario.verify(c1.get_mint_token_available(ben.address) == 20)

        scenario.p("34. Verify Alice can mint with a discount as she is in the allowlist")
        c1.user_mint(20).run(valid=False, amount=sp.tez(4000), sender=alice)
        c1.user_mint(21).run(valid=False, amount=sp.tez(2100), sender=alice)
        c1.user_mint(20).run(valid=True, amount=sp.tez(2000), sender=alice)

        scenario.p("35. Verify John can mint but without the discount as he is not in the allowlist")
        c1.user_mint(20).run(valid=False, amount=sp.tez(2000), sender=john)
        c1.user_mint(20).run(valid=True, amount=sp.tez(4000), sender=john)
        scenario.verify(c1.get_mint_token_available(john.address) == 0)
        c1.user_mint(10).run(valid=True, amount=sp.tez(2000), sender=ben)

        scenario.p("36. Check the offchain view get_mint_token_available returns the expected result")
        scenario.verify(c1.get_mint_token_available(alice.address) == 0)
        scenario.verify(c1.get_mint_token_available(ben.address) == 0)
        scenario.verify(c1.get_mint_token_available(nat.address) == 20)
        scenario.verify(c1.get_mint_token_available(bob.address) == 20)

        scenario.p("37. Verify there is no supply anymore for users not in the allowlist")
        c1.user_mint(1).run(valid=False, amount=sp.tez(200), sender=chris)

        scenario.p("38. Verify users in the allowlist can still mint using their mint rights")
        c1.user_mint(20).run(valid=True, amount=sp.tez(2000), sender=bob)
        scenario.verify(c1.get_mint_token_available(bob.address) == 0)
        c1.user_mint(10).run(valid=True, amount=sp.tez(1000), sender=nat)
        scenario.verify(c1.get_mint_token_available(nat.address) == 10)
        c1.user_mint(10).run(valid=True, amount=sp.tez(1000), sender=nat)
        scenario.verify(c1.get_mint_token_available(nat.address) == 0)

        scenario.p("39. Verify that even users with mint rights cannot mint more than the max number of NFT mintable per user")
        c1.user_mint(10).run(valid=False, amount=sp.tez(1000), sender=nat)

        scenario.p("40. Verify only admin can close the event")
        c1.close_any_open_event().run(valid=False, sender=nat)

        scenario.p("41. Successfully close the event")
        c1.close_any_open_event().run(valid=True, sender=admin)

        scenario.p("42. Verify users, even if in allowlist, cannot mint anymore when event is closed")
        c1.user_mint(20).run(valid=False, amount=sp.tez(2000), sender=gabe)

        scenario.p("43. Verify only admin can clear the allowlist")
        c1.clear_allowlist().run(valid=False, sender=bob)
        c1.clear_allowlist().run(valid=False, sender=alice)
        c1.clear_allowlist().run(valid=False, sender=john)
        c1.clear_allowlist().run(valid=False, sender=nat)

        scenario.p("44. Successfully clear the allowlist")
        c1.clear_allowlist().run(valid=True, sender=admin)

        scenario.p("45. Verify allowlist is cleared in the contract storage")
        scenario.verify(sp.len(c1.data.allowlist) == 0)
        scenario.verify(c1.data.state == STATE_NO_EVENT_OPEN_0)

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
        c1, c2 = TestHelper.create_contracts(scenario, admin, john)

        scenario.h2("Test a scenario with a a public sale without allowlist")

        scenario.p("1. Verify only admin can open a public sale")
        c1.open_pub_sale(sp.record(
            max_supply=30,
            max_per_user=20,
            price=sp.tez(200), use_deadline=False, deadline=sp.timestamp(0))).run(valid=False, sender=bob)

        scenario.p("2. Successfully open a public sale without allowlist")
        c1.open_pub_sale(sp.record(
            max_supply=30,
            max_per_user=20,
            price=sp.tez(200), use_deadline=False, deadline=sp.timestamp(0))).run(valid=True, sender=admin)

        scenario.p("3. Check users cannot mint more NFTs that the max number mintable per user in this event")
        c1.user_mint(21).run(valid=False, amount=sp.tez(4200), sender=alice)

        scenario.p("4. Check the user can mint the max number of NFT mintable per user in this event in one call")
        c1.user_mint(20).run(valid=True, amount=sp.tez(4000), sender=alice)
        c1.user_mint(20).run(valid=False, amount=sp.tez(4000), sender=john)
        c1.user_mint(10).run(valid=True, amount=sp.tez(2000), sender=ben)

        scenario.p("5. Check the user cannot mint more than the total allocated supply in this event")
        c1.user_mint(10).run(valid=False, amount=sp.tez(2000), sender=ben)

        scenario.p("6. Check users can mint exactly the total allocated supply in this event")
        c1.user_mint(20).run(valid=False, amount=sp.tez(4000), sender=chris)

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
unit_test_set_fa2_administrator_function()
unit_test_mint_and_give()
unit_test_set_administrator()
unit_test_set_transfer_addresses()
unit_test_register_fa2()
unit_test_user_mint_during_public_sale()
unit_test_user_mint_during_pre_sale()
unit_test_user_mint_during_public_sale_with_allowlist_discount()
unit_test_user_mint_during_public_sale_with_allowlist_mint_rights()
unit_test_mutez_transfer()
module_test_pre_sale_public_sale_with_allowlist()
module_test_public_sale()