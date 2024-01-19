import numpy as np
import pandas as pd

import itertools

from functools import cache
from tqdm.notebook import tqdm

from .checker import Checker
from .generator import Generator

class EngineFD:

    def __init__(self, data: pd.DataFrame, **kwargs) -> None:
        """
        Main-Slate engine for fanduel
        Takes as input the abbreviated contest files (only select columns)
        """

        POSITIONS = ('PG', 'SG', 'SF', 'PF', 'C')

        self.data = data.copy(deep=True)

        if 'opp' in self.data.columns:
            # If ValueError, check to see if self.data.empty
            self.data['game'] = self.data[['team', 'opp']].apply(lambda row: '-'.join(sorted([row.iloc[0], row.iloc[1]])), axis=1)

        self.labels = ['PG', 'PG', 'SG', 'SG', 'SF', 'SF', 'PF', 'PF', 'C']
        self.sum_cols = sum([
            ['fpts', 'salary'],
            kwargs.get('sum_cols', list())
        ], list())

        # Dictionary that will have form: {pos: tuple(...players at that position...)}
        self.pos_players = dict()

        # Get players for each position
        # Can have overlap / duplicates (Example: Anthony Davis is PF and C)
        for pos in POSITIONS:
            self.data[pos] = self.data['pos'].map(lambda pos_: int(pos in pos_))
            self.pos_players[pos] = tuple(self.data.loc[self.data[pos] == 1].index)
            self.data = self.data.drop(pos, axis=1)

        self.checker = Checker(self.data, **kwargs)
        self.generator = Generator(self.pos_players, self.checker)

    def create_lineups(self, **kwargs):

        lineups = pd.DataFrame(self.generator.lineups(), columns=self.labels)

        lineups['lineup'] = lineups[self.labels].apply(tuple, axis=1)
        lineups['lineup'] = lineups['lineup'].map(lambda x: self.checker.order(x))


        lineups['salary'] = lineups['lineup'].map(lambda x: self.checker.cost(x))
        lineups['fpts'] = lineups['lineup'].map(lambda names: sum([self.checker.pvalue(name, 'fpts') for name in names]))

        # if 'e_fpts' in self.sum_cols:
        if len(self.sum_cols) > 2:
            for col in self.sum_cols[2:]:
                lineups[col] = lineups['lineup'].map(lambda names: sum([self.checker.pvalue(name, col) for name in names]))
        
        lineups = lineups.sort_values('fpts', ascending=False)

        lineups = (lineups
                   .drop_duplicates(subset=['lineup']) # Same team in different order
                   .drop('lineup', axis=1)
                  )

        if 'top_n' in kwargs:

            return (lineups
                    .sort_values('fpts', ascending=False)
                    .head(kwargs['top_n'])
                    .reset_index(drop=True)
                   )

        return lineups
        
            