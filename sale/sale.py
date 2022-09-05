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
            "version": "1.0.2"
            , "description": (
                "Angry Teenagers Crowdsale contract"
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
# process_presale
########################################################################################################################
    @sp.entry_point
    def process_presale(self, params):
        sp.verify(self.is_administrator(), Error.ErrorMessage.unauthorized_user())
        sp.verify(~self.is_any_event_open(), Error.ErrorMessage.sale_event_already_open())
        sp.set_type(params, sp.TAddress)

        tokens = sp.view("all_tokens", params, sp.unit).open_some(Error.ErrorMessage.invalid_parameter())

        sp.for token in tokens:
            is_burn = sp.view("is_token_burned", params, token).open_some(Error.ErrorMessage.invalid_parameter())

            burn_list = sp.local("burn_list", sp.list(l={}, t=sp.TNat))

            sp.if ~is_burn:
                owner = sp.view("get_token_owner", params, token).open_some(Error.ErrorMessage.invalid_parameter())
                self.mint_internal(amount=1, address=owner)
                burn_list.push(token)

            presale_contract_handle = sp.contract(
                sp.TList(sp.TNat),
                params,
                "burn"
            ).open_some("Interface mismatch")

            presale_contract_arg = burn_list
            self.call(presale_contract_handle, presale_contract_arg)


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
