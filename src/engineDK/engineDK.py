import numpy as np
import pandas as pd

import itertools

from functools import cache
from tqdm.notebook import tqdm

# from .checker import Checker
# from .generator import Generator

from typing import Any
from collections.abc import Sequence

from .checker import Checker


class EngineDK:

    def __init__(self, data: pd.DataFrame, **kwargs):
        """
        Takes pandas.DataFrame as input with columns: [name, pos, salary, fpts]
        Indexed by name
        Creates optimal lineups
        """
        df = data.copy(deep=True)
        self.PAST = kwargs.get('past', True)

        if 'opp' in df.columns:
            # If ValueError, check to see if self.data.empty
            df['game'] = df[['team', 'opp']].apply(lambda row: '-'.join(sorted([row.iloc[0], row.iloc[1]])), axis=1)
        
        positions = ['PG', 'SG', 'SF', 'PF', 'C']
        for pos in positions:
            df[pos] = df['pos'].map(lambda pos_: int(pos in pos_))
        
        # Tuple of each position of players
        self.pos_players = {pos: tuple(df.loc[df[pos] == 1].index) for pos in positions}

        df = df.drop(positions, axis=1)
        self.labels = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL']
        self.checker = Checker(df, past=self.PAST)

        self.sum_cols = sum([
            ['fpts', 'salary'],
            kwargs.get('sum_cols', list())
        ], list())

        return None

        

    def flatten(cls, nestedSeq: Sequence[Sequence[Any,...], ...], **kwargs) -> list[Any,...]:
        """
        Takes 2d sequence and returns all values in 1d
        Example: [(a,b,c), (a,y,z), (a,b,z)] -> [a, b, c, a, y, z, a, b, z]
        TODO: kwargs to add functinoality
            - unique: [(a,b,c), (a,y,z), (a,b,z)] -> [a, b, c, y, z]
            - counts dict -> {a: 3, b: 2, z: 2, c: 1, z: 1} (recursive)
            - etc
        """
        if kwargs.get('unique', False):
            return set(cls.flatten(nestedSeq))

        return [element for innerSeq in nestedSeq for element in innerSeq]

    
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

        return tuple([tuple(combo) for combo in itertools.combinations(names,k)])

    def cross_combos(self, *args) -> tuple[tuple[str,...], ...]:
        """
        Takes unspecified number of arguments, where arg[i] is 2d sequence
        Returns cartesian product of args
        Example:
            - cross_combos(((a,b), (a,c)), ((d,e), (d,f))) -> ((a, b, d, e), (a, b, d, f), (a, c, d, e), (a, c, d, f))
            - cross_combos(((a, b), (a, c)), ((d,),)) -> ((a, b, d), (a, c, d))
        """
        return tuple([sum(combo, tuple()) for combo in itertools.product(*args)])

    def create_lineups(self, **kwargs):
        """
        Creates lineups in proper format
        """

        pg = self.combos(self.pos_players['PG'], 1)
        sg = self.combos(self.pos_players['SG'], 1)
        sf = self.combos(self.pos_players['SF'], 1)
        pf = self.combos(self.pos_players['PF'], 1)
        c = self.combos(self.pos_players['C'], 1)

        g = self.combos(sum([
            self.pos_players['PG'],
            self.pos_players['SG']
        ], tuple()), 1)

        f  = self.combos(sum([
            self.pos_players['SF'],
            self.pos_players['PF']
        ], tuple()), 1)

        util = self.combos(sum([
            self.pos_players[pos_] for pos_ in ('PG', 'SG', 'SF', 'PF', 'C')
        ], tuple()), 1)


        pg_sg = tuple([ combo for combo in self.cross_combos(pg, sg) if self.checker.check_guards(combo)])
        pg_sg_sf = tuple([ combo for combo in self.cross_combos(pg, sg, sf) if self.checker.check_pg_sg_sf(combo) ])
        pg_sg_sf_pf = tuple([ combo for combo in self.cross_combos(pg_sg_sf, pf) if self.checker.check(combo) ])

        # sf_pf = tuple([ combo for combo in self.cross_combos(sf, pf) if self.checker.check_forwards(combo)])
        # pg_sg_sf_pf = tuple([ combo for combo in self.cross_combos(pg_sg, sf_pf) if self.checker.check(combo)])
        
        pg_sg_sf_pf_c = tuple([ combo for combo in self.cross_combos(pg_sg_sf_pf, c) if self.checker.check(combo)])
        pg_sg_sf_pf_c_g = tuple([ combo for combo in self.cross_combos(pg_sg_sf_pf_c, g) if self.checker.check(combo)])
        pg_sg_sf_pf_c_g_f = tuple([ combo for combo in self.cross_combos(pg_sg_sf_pf_c_g, f) if self.checker.check(combo)])

        lineups = tuple([lineup for lineup in self.cross_combos(pg_sg_sf_pf_c_g_f, util) if self.checker.check(lineup)])

        lineups_df = pd.DataFrame(lineups, columns=self.labels)

        lineups_df['lineup'] = lineups_df[self.labels].apply(tuple, axis=1)
        lineups_df['ordered'] = lineups_df['lineup'].map(lambda lu: tuple(sorted(lu)))

        lineups_df = (lineups_df
                      .drop_duplicates('ordered')
                      .drop('ordered', axis=1)
                     )

        lineups_df['fpts'] = lineups_df['lineup'].map(lambda lu: self.checker.score(lu))
        lineups_df['salary'] = lineups_df['lineup'].map(lambda lu: self.checker.cost(lu)) # May be redundant

        if len(self.sum_cols) > 2:
            for col in self.sum_cols[2:]:
                lineups_df[col] = lineups_df['lineup'].map(lambda names: sum([self.checker.pvalue(name, col) for name in names]))

        if 'top_n' in kwargs:

            return (lineups_df
                    .sort_values('fpts', ascending=False)
                    .head(kwargs['top_n'])
                    .reset_index(drop=True)
                   )

        return (lineups_df
                .sort_values('fpts', ascending=False)
                .reset_index(drop=True)
               )








