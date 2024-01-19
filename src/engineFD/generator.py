"""
FanDuel generator file
Creates all possible lineups
Form:
    - 2 PG
    - 2 SG
    - 2 SF
    - 2 PF
    - 1 C
"""


import numpy as np
import pandas as pd

import itertools

from collections.abc import Sequence
from typing import Any

class Generator:
    def __init__(self, players: dict[str, tuple[str,...]], checker) -> None:
        """
        Class to deal with the generation of lineups, including checking if valid or not
        Parameters:
            - Dictionary containing position players
            - Checker object to do checking of lineups
        """
        
        self.players = players
        self.checker = checker

    def flatten(self, seq_2d: Sequence[Sequence[Any,...], ...]) -> tuple[Any, ...]:
        """
        Takes a 2 dimensional sequence and flattens all elements into one single tuple containing all values
        """
        return tuple([element for inner_seq in seq_2d for element in inner_seq])

    def combos(self, names: Sequence[str,...], k: int) -> tuple[tuple[str,...], ...]:
        """
        Takes sequence of names, usually all players at position
        Special case for if k = 1, where returns names but as 2d instead of 1d
        If k != 1, uses self.checker to see if valid combination (according to rules in checker.py)
        Returns tuple of nCk combinations, where:
            - n = len(names)
            - k = len(element_i) for tuple element in returned tuple (2d)
        Example:
            - combos((a,b,c,d), 1) -> ((a,), (b,), (c,), (d,))
            - combos((a,b,c,d), 2) -> ((a,b), (a,c), (a,d), (b,c), (b,d), (c,d))
        """
        if k == 1:
            return tuple([(name,) for name in names])

        return tuple([tuple(combo) for combo in itertools.combinations(names,k) if self.checker.check(tuple(combo))])

    def cross_combos(self, *args) -> tuple[tuple[str,...], ...]:
        """
        Takes unspecified number of arguments, where arg[i] is 2d sequence
        Returns cartesian product of args
        Example:
            - cross_combos(((a,b), (a,c)), ((d,e), (d,f))) -> ((a, b, d, e), (a, b, d, f), (a, c, d, e), (a, c, d, f))
            - cross_combos(((a, b), (a, c)), ((d,),)) -> ((a, b, d), (a, c, d))
        """
        return tuple([sum(combo, tuple()) for combo in itertools.product(*args) if self.checker.check(sum(combo, tuple()))])

    def pos_pairs(self, pos: str) -> tuple[tuple[str,str], ...]:
        """
        Takes a position as input where it is any position but C (since only one Center in build)
        Returns a tuple of all possible pairs at that position
        """
        return self.combos(self.players[pos], 2)


    def guards(self) -> tuple[tuple[str,str,str,str], ...]:
        """
        Creates a combination of 4 guards where 2 PG and 2 SG
        """
        return tuple([ combo for combo in self.cross_combos(self.pos_pairs('PG'), self.pos_pairs('SG')) if self.checker.check(combo)])

    def forwards(self) -> tuple[tuple[str,str,str,str], ...]:
        """
        Creates a combination of 4 forwards where 2 SF and 2 PF
        """
        return tuple([combo for combo in self.cross_combos(self.pos_pairs('SF'), self.pos_pairs('PF')) if self.checker.check(combo)])

    def no_center(self) -> tuple[tuple[str,str,str,str,str,str,str,str], ...]:
        """
        Creates tuples of len() = 8, where all parts of lineup but center
        """
        return self.cross_combos(self.guards(), self.forwards())

    def lineups(self) -> tuple[tuple[str,str,str,str,str,str,str,str,str], ...]:
        """
        Creates full lineups with all position constraints satisfied
        """

        # Center never lt 5_000

        centers = tuple([name for name in self.players['C'] if self.checker.pvalue(name, 'salary') >= 4_800]) if not self.checker.PAST else self.players['C']
        
        return tuple([lineup for lineup in self.cross_combos(self.no_center(), self.combos(centers, 1)) if self.checker.check(lineup)])








        