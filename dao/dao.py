import smartpy as sp

Error = sp.io.import_script_from_url("file:./helper/errors.py")
Proposal = sp.io.import_script_from_url("file:dao/helper/dao_proposal.py")
VoteValue = sp.io.import_script_from_url("file:dao/helper/dao_vote_value.py")
PollOutcome = sp.io.import_script_from_url("file:dao/helper/dao_poll_outcome.py")
PollType = sp.io.import_script_from_url("file:dao/helper/dao_poll_type.py")

################################################################
################################################################
# Local types: type onoly used by this contract
################################################################
################################################################

PROPOSE_CALLBACK_TYPE = sp.TRecord(id=sp.TNat, snapshot_block=sp.TNat)
POLL_MANAGER_TYPE = sp.TMap(sp.TNat, sp.TRecord(name=sp.TString, address=sp.TAddress))
OUTCOMES_TYPE = sp.TBigMap(sp.TNat, PollOutcome.HISTORICAL_OUTCOME_TYPE)

################################################################
################################################################
# Constants
################################################################
################################################################

# Voting strategy called "majority". Works with a configurable quorum
# and a supermajority thresold.
VOTE_TYPE_MAJORITY=0
# Voting strategy called "opt out". Mainly used to unblock ATs funds.
VOTE_TYPE_OPT_OUT=1

################################################################
################################################################
# State Machine
################################################################
################################################################

# NONE: No vote in progress.
NONE=0
# STARTING_VOTE: The contract requested to start to the appropriate
# voting strategy and wait for the answer.
STARTING_VOTE=1
# VOTE_ONGOING: Vote is started.
VOTE_ONGOING=2
# ENDING_VOTE: The contract requested to end the vote to the appropriate
# voting strategy and wait for the answer.
ENDING_VOTE=3

################################################################
################################################################
# Class
################################################################
################################################################
class AngryTeenagersDao(sp.Contract):
    def __init__(self,
                 admin,
                 metadata,
                 poll_manager,
                 outcomes=sp.big_map(l={}, tkey=sp.TNat, tvalue=PollOutcome.HISTORICAL_OUTCOME_TYPE)):
      self.init_type(
          sp.TRecord(
              state = sp.TNat,
              ongoing_poll = sp.TOption(PollType.POLL_TYPE),
              angry_teenager_fa2 = sp.TOption(sp.TAddress),
              poll_manager = POLL_MANAGER_TYPE,
              next_proposal_id = sp.TNat,
              admin = sp.TAddress,
              outcomes = OUTCOMES_TYPE,
              metadata= sp.TBigMap(sp.TString, sp.TBytes)
          )
      )

      self.init(
          state = sp.nat(NONE),
          ongoing_poll = sp.none,
          angry_teenager_fa2 = sp.none,
          poll_manager = poll_manager,
          next_proposal_id = sp.nat(0),
          admin = admin,
          outcomes = outcomes,
          metadata = metadata
      )

      list_of_views = [
          self.get_number_of_historical_outcomes
          , self.get_historical_outcome_data
          , self.is_poll_in_progress
          , self.get_current_poll_data
          , self.get_contract_state
      ]

      metadata_base = {
          "name": "Angry Teenagers DAO"
          ,
          "version": "1.0.4"
          , "description": (
              "Angry Teenagers DAO."
          )
          , "interfaces": ["TZIP-016"]
          , "authors": [
              "EcoMint LTD <www.angryteenagers.xyz>"
          ]
          , "homepage": "https://www.angryteenagers.xyz"
          , "views": list_of_views
      }
      self.init_metadata("metadata_base", metadata_base)

################################################################
################################################################
# Interface
################################################################
################################################################

########################################################################################################################
# delegate
########################################################################################################################
    @sp.entry_point
    def delegate(self, baker):
        sp.verify_equal(sp.sender, sp.self_address, Error.ErrorMessage.dao_only_for_dao())
        sp.set_delegate(baker)

########################################################################################################################
# default
########################################################################################################################
    @sp.entry_point
    def default(self):
        pass

########################################################################################################################
# set_metadata
########################################################################################################################
    @sp.entry_point
    def set_metadata(self, k, v):
        sp.verify(sp.sender == self.data.admin, message = Error.ErrorMessage.unauthorized_user())
        self.data.metadata[k] = v

########################################################################################################################
# set_administrator
########################################################################################################################
    @sp.entry_point
    def set_administrator(self, params):
        sp.verify(sp.sender == self.data.admin, message = Error.ErrorMessage.unauthorized_user())
        self.data.admin = params

########################################################################################################################
# add_voting_strategy
########################################################################################################################
    @sp.entry_point
    def add_voting_strategy(self, params):
        sp.verify(self.data.state == NONE, Error.ErrorMessage.dao_vote_in_progress())
        sp.verify((sp.self_address == sp.sender) | (self.data.admin == sp.sender), Error.ErrorMessage.unauthorized_user())
        sp.set_type(params, sp.TRecord(id=sp.TNat, name=sp.TString, address=sp.TAddress))
        sp.verify(~self.data.poll_manager.contains(params.id), Error.ErrorMessage.dao_already_registered())
        self.data.poll_manager[params.id] = sp.record(name=params.name, address=params.address)

########################################################################################################################
# register_angry_teenager_fa2
########################################################################################################################
    @sp.entry_point
    def register_angry_teenager_fa2(self, address):
        sp.verify(self.data.admin == sp.sender, Error.ErrorMessage.unauthorized_user())
        sp.verify(~self.data.angry_teenager_fa2.is_some(), Error.ErrorMessage.dao_already_registered())
        self.data.angry_teenager_fa2 = sp.some(address)

########################################################################################################################
# propose: Inject a new proposal
########################################################################################################################
    @sp.entry_point
    def propose(self, proposal):
        # Check the type
        sp.set_type(proposal, Proposal.PROPOSAL_TYPE)

        # Asserts
        sp.verify(sp.sender == self.data.admin, Error.ErrorMessage.unauthorized_user())
        sp.verify(self.data.state == NONE, Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(self.data.angry_teenager_fa2.is_some(), Error.ErrorMessage.dao_not_registered())
        sp.verify(~self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_vote_in_progress())
        sp.verify(self.data.poll_manager.contains(proposal.voting_strategy), Error.ErrorMessage.dao_invalid_voting_strat())

        # Create the poll with the proposal
        self.data.ongoing_poll = sp.some(
            sp.record(
                proposal=proposal,
                proposal_id=self.data.next_proposal_id,
                author=sp.sender,
                voting_strategy_address=self.data.poll_manager[proposal.voting_strategy].address,
                voting_id=sp.nat(0),
                snapshot_block=sp.nat(0)
            )
        )

        # Get the total voting power in the ATs collection at the moment
        total_available_voters = sp.view("get_total_voting_power",
                               self.data.angry_teenager_fa2.open_some(Error.ErrorMessage.dao_not_registered()),
                               sp.unit,
                               t=sp.TNat).open_some(Error.ErrorMessage.dao_invalid_token_view())
        sp.verify(total_available_voters > 0, Error.ErrorMessage.dao_no_voting_power())

        # Change the state of the contract accordingly
        self.data.state = STARTING_VOTE

        # Call voting strategy to start the poll
        self.call_voting_strategy_start(total_available_voters)

########################################################################################################################
# propose_callback
########################################################################################################################
    @sp.entry_point
    def propose_callback(self, params):
        # Check the type
        sp.set_type(params, PROPOSE_CALLBACK_TYPE)

        # Asserts
        sp.verify(self.data.state == STARTING_VOTE, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.open_some().voting_strategy_address == sp.sender, Error.ErrorMessage.dao_invalid_voting_strat())

        # Update the poll data
        self.data.ongoing_poll = sp.some(
            sp.record(
                proposal=self.data.ongoing_poll.open_some().proposal,
                proposal_id=self.data.ongoing_poll.open_some().proposal_id,
                author=self.data.ongoing_poll.open_some().author,
                voting_strategy_address=self.data.ongoing_poll.open_some().voting_strategy_address,
                voting_id=params.id,
                snapshot_block=params.snapshot_block
            )
        )

        # Change the state of the contract accordingly
        self.data.state = VOTE_ONGOING

########################################################################################################################
# vote: Send
########################################################################################################################
    @sp.entry_point
    def vote(self, params):
        # Check type
        sp.set_type(params, VoteValue.VOTE_VALUE)

        # Asserts
        sp.verify(self.data.state == VOTE_ONGOING, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(params.proposal_id == self.data.ongoing_poll.open_some().proposal_id, Error.ErrorMessage.dao_no_invalid_proposal())

        # Find the user voting power before sending the votes
        voting_power = sp.view("get_voting_power",
                               self.data.angry_teenager_fa2.open_some(Error.ErrorMessage.dao_not_registered()),
                               sp.pair(sp.sender, self.data.ongoing_poll.open_some().snapshot_block),
                               t=sp.TNat).open_some(Error.ErrorMessage.dao_invalid_token_view())
        sp.verify(voting_power > 0, Error.ErrorMessage.dao_no_voting_power())

        # Call the appropriate voting strategy
        self.call_voting_strategy_vote(voting_power, sp.sender, params.vote_value)

########################################################################################################################
# end
########################################################################################################################
    @sp.entry_point
    def end(self, proposal_id):
        # Check type
        sp.set_type(proposal_id, sp.TNat)

        # Asserts
        # Everybody can call this function to avoid a vote been blocked by the admin or anybody else
        sp.verify(self.data.state == VOTE_ONGOING, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.open_some().proposal_id == proposal_id, Error.ErrorMessage.dao_no_invalid_proposal())

        # Change the state of contract
        self.data.state = ENDING_VOTE

        # Call the appropriate voting strategy
        self.call_voting_strategy_end()

########################################################################################################################
# end_callback
########################################################################################################################
    @sp.entry_point
    def end_callback(self, params):
        # Check type
        sp.set_type(params, sp.TRecord(voting_id=sp.TNat, voting_outcome=sp.TNat))

        # Asserts
        sp.verify(self.data.state == ENDING_VOTE, Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.verify(self.data.ongoing_poll.open_some().voting_strategy_address == sp.sender, Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(~self.data.outcomes.contains(self.data.next_proposal_id), Error.ErrorMessage.dao_invalid_voting_strat())
        sp.verify(params.voting_id == self.data.ongoing_poll.open_some().voting_id, Error.ErrorMessage.dao_invalid_voting_strat())

        # Execute the lambda if the vote is passed and the lambda exists
        sp.if (params.voting_outcome == PollOutcome.POLL_OUTCOME_PASSED) & (self.data.ongoing_poll.open_some().proposal.proposal_lambda.is_some()):
            operations = self.data.ongoing_poll.open_some().proposal.proposal_lambda.open_some()(sp.unit)
            sp.set_type(operations, sp.TList(sp.TOperation))
            sp.add_operations(operations)

        # Change the state of contract
        self.data.state = NONE

        # Record the result of the vote
        self.data.outcomes[self.data.next_proposal_id] = sp.record(outcome = params.voting_outcome, poll_data = self.data.ongoing_poll.open_some())

        # Close the vote
        self.data.ongoing_poll = sp.none
        self.data.next_proposal_id = self.data.next_proposal_id + 1

########################################################################################################################
# mutez_transfer
########################################################################################################################
    @sp.entry_point
    def mutez_transfer(self, params):
        # Check type
        sp.set_type(params.destination, sp.TAddress)
        sp.set_type(params.amount, sp.TMutez)

        # Asserts
        sp.verify_equal(sp.sender, sp.self_address, Error.ErrorMessage.dao_only_for_dao())

        # Send mutez
        sp.send(params.destination, params.amount)

################################################################
################################################################
# Helper functions
################################################################
################################################################
    def call(self, c, x):
        sp.transfer(x, sp.mutez(0), c)

    def call_voting_strategy_start(self, total_available_voters):
        voteContractHandle = sp.contract(
            sp.TRecord (total_available_voters=sp.TNat),
            self.data.ongoing_poll.open_some().voting_strategy_address,
            "start"
        ).open_some("Interface mismatch")

        voteContractArg = sp.record(total_available_voters=total_available_voters)
        self.call(voteContractHandle, voteContractArg)

    def call_voting_strategy_vote(self, votes, address, vote_value):
        voteContractHandle = sp.contract(
            sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, voting_id=sp.TNat),
            self.data.ongoing_poll.open_some().voting_strategy_address,
            "vote"
        ).open_some("Interface mismatch")

        voteContractArg = sp.record(
                votes=votes, address=address, vote_value=vote_value, voting_id=self.data.ongoing_poll.open_some().voting_id
            )
        self.call(voteContractHandle, voteContractArg)

    def call_voting_strategy_end(self):
        voteContractHandle = sp.contract(
            sp.TNat,
            self.data.ongoing_poll.open_some().voting_strategy_address,
            "end"
        ).open_some("Interface mismatch")

        voteContractArg = self.data.ongoing_poll.open_some().voting_id
        self.call(voteContractHandle, voteContractArg)

########################################################################################################################
########################################################################################################################
# Offchain views
########################################################################################################################
########################################################################################################################
    @sp.offchain_view(pure=True)
    def get_number_of_historical_outcomes(self):
        """Get how many historical outcomes are stored in the DAO.
        """
        sp.result(self.data.next_proposal_id)

    @sp.offchain_view(pure=True)
    def get_historical_outcome_data(self, id):
        """Get all historical outcomes ids.
        """
        sp.verify(self.data.outcomes.contains(id), Error.ErrorMessage.dao_invalid_outcome_id())
        sp.result(self.data.outcomes[id])

    @sp.offchain_view(pure=True)
    def is_poll_in_progress(self):
        """Is there a poll ins progress ?
        """
        sp.result(self.data.ongoing_poll.is_some())

    @sp.offchain_view(pure=True)
    def get_current_poll_data(self):
        """Get all current poll data if it exists.
        """
        sp.verify(self.data.ongoing_poll.is_some(), Error.ErrorMessage.dao_no_vote_open())
        sp.result(self.data.ongoing_poll.open_some())

    @sp.offchain_view(pure=True)
    def get_contract_state(self):
        """Get contract state
        """
        sp.result(self.data.state)
