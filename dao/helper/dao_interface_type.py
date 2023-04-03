import smartpy as sp

END_CALLBACK_TYPE = sp.TRecord(vote_id=sp.TNat, voting_outcome=sp.TNat).layout(("vote_id", 
                                                                                ("voting_outcome")))
VOTING_STRATEGY_VOTE_TYPE = sp.TRecord(votes=sp.TNat, address=sp.TAddress, vote_value=sp.TNat, vote_id=sp.TNat).layout(("votes", 
                                                                                                                        ("address", 
                                                                                                                         ("vote_value", 
                                                                                                                          ("vote_id")))))