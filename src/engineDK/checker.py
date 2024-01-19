import numpy as np
import pandas as pd

import itertools
from functools import cache

from typing import Any
### Checker 8 games
class Checker:

    def __init__(self, data: pd.DataFrame, **kwargs) -> None:
        """
        Checker object to validate lineups
        Takes contest data as required parameter
        """

        # Flag to determine what to check for
        self.PAST = kwargs.get('past', True)
        # print(f'Past flag: {self.PAST}\n')

        # Cheapest salary in pool
        self.minimum_salary = min(data['salary'])

        # Make dictionary
        self.data = {name: {value: data.loc[name, value] for value in data.columns} for name in data.index}

        mincost = 48_500 if self.PAST else 49_500

        self.mincost, self.maxcost = mincost, 50_000
        self.cost_range = self.maxcost - self.mincost

        self.n_games = int(len(data['team'].drop_duplicates()) / 2)

        salaries = data.sort_values('salary')['salary']

        min_PG_sal = min(data.loc[data['pos'].isin(['PG/SG', 'SG/PG', 'PG', 'SF/PG', 'PG/SF', 'PG/PF', 'PF/PG']), 'salary'])
        min_SG_sal = min(data.loc[data['pos'].isin(['SF/SG', 'SG/SF', 'SG', 'SG/PG', 'PG/SG']), 'salary'])
        min_SF_sal = min(data.loc[data['pos'].isin(['SF/SG', 'SG/SF', 'SF', 'SF/PF', 'PF/SF', 'PG/SF', 'SF/PG']), 'salary'])
        min_PF_sal = min(data.loc[data['pos'].isin(['SF/PF', 'PF/C', 'PF', 'PF/PG', 'PG/PF']), 'salary'])
        min_C_sal = min(data.loc[data['pos'].isin(['C', 'PF/C', 'C/PF']), 'salary'])

        cheapest_4_sals = list(salaries)[:4]

        self.TEAM_MAX = 3
        self.TEAM_MAX_PLAYERS = dict()

        

        self.pg_sg_max_cost = (self.maxcost - (min_SF_sal + min_PF_sal + sum(cheapest_4_sals[:3]) + min_C_sal)) - self.cost_range
        self.sf_pf_max_cost = (self.maxcost - (min_PG_sal + min_SG_sal + sum(cheapest_4_sals[:3]) + min_C_sal)) - self.cost_range
        self.pg_sg_sf_max_cost = (self.maxcost - (min_PF_sal + min_C_sal + sum(cheapest_4_sals[:3]))) - self.cost_range

        # print(f'PG-SG max cost: {self.pg_sg_max_cost}')
        # print(f'SF-PF max cost: {self.sf_pf_max_cost}')
        # print(f'PG-SG-SF max cost: {self.pg_sg_sf_max_cost}')
        # Only one position specific since still need a center
        self.four_max_cost = (self.maxcost - ( sum(cheapest_4_sals[:3]) + min_C_sal )) - self.cost_range

        
        self.five_max_cost = (self.maxcost - sum(cheapest_4_sals[:3])) - self.cost_range        
        self.six_max_cost = (self.maxcost - sum(cheapest_4_sals[:2])) - self.cost_range
        self.seven_max_cost = (self.maxcost - cheapest_4_sals[0]) - self.cost_range
        
        # self.eight_cost_range = range(self.eight_min_cost, self.eight_max_cost+1, 100)

    @cache
    def pvalue(self, name: str, value: str):
        """
        Returns the value for player
        Cached to only call once per name,value pair
        """
        return self.data[name][value]

    @cache
    def order(self, names: tuple[str,...]|str) -> tuple[str,...]:
        """
        Orders tuple of names to minimize cacheing for assortment
        Doesn't matter how sorted as long as consistent
        Sometimes just a single string
        """
        return tuple(set(sorted(names))) if isinstance(names, tuple) else names

    @cache
    def rc_pvalues(self, names: tuple[str,...], value: str) -> tuple[Any,...]:
        """
        Returns tuple of mapping of names to value
        Recursive to optimize memoization
        Example:
            - rc_pvalues(['Nikola Jokic', 'Steph Curry'], 'salary') -> [10_000, 9_500]
        """
        head, *tail = names

        # Recursive base case
        if len(names) == 1:
            return (self.pvalue(head, value), )
            
        return sum([
            (self.pvalue(head, value),),
            self.rc_pvalues(self.order(tuple(tail)), value)
        ], tuple())

    @cache
    def pvalues(self, names: tuple[str,...], value: str) -> tuple[Any,...]:
        return self.rc_pvalues(names, value)

# ------------------------------- Mappers / shorthand -------------------------------
# Improves code readability
# All different calls to rc_pvalues to get different types of tuples of player values
    
    @cache
    def positions(self, names: tuple[str,...]) -> tuple[str,...]:
        """
        Returns tuple of positions for each player
        """
        return self.pvalues(names, 'pos')

    @cache
    def salaries(self, names: tuple[str,...]) -> tuple[str,...]:
        """
        Returns tuple of salaries for each player
        """
        return self.pvalues(names, 'salary')

    @cache
    def teams(self, names: tuple[str,...]) -> tuple[str,...]:
        """
        Returns tuple of teams for each player
        """
        return self.pvalues(names, 'team')

    @cache
    def games(self, names: tuple[str,...]) -> tuple[str,...]:
        """
        Returns tuple of games for players
        """
        return self.pvalues(names, 'game')

# ------------------------------- Operations -------------------------------
# Numerical operations for certain aspects of checking
    
    @cache
    def rc_sumvalues(self, names: tuple[str,...], value: str) -> float|int:
        """
        Returns sum of values for all values of players in names
        Recursive to optimize for memoization
        Example:
            - rc_sumvalues(['Nikola Jokic', 'Steph Curry'], 'salary') -> 19_500
        """
        head, *tail = names

        # Base case
        if len(names) == 1:
            return self.pvalue(head, value)

        return sum([
            self.pvalue(head, value),
            self.rc_sumvalues(self.order(tuple(tail)), value)
        ])

    @cache
    def sumvalues(self, names: tuple[str,...], value: str) -> float|int:
        """
        Non-recursive version of above
        """
        return sum(self.rc_pvalues(names, value))

    @cache
    def cost(self, names: tuple[str,...]) -> int:
        """
        Returns the cost of players in names
        """
        return self.rc_sumvalues(names, 'salary')

    @cache
    def score(self, names: tuple[str,...]) -> int:
        """
        Returns the cost of players in names
        """
        return self.rc_sumvalues(names, 'fpts')

    @cache
    def n_teams(self, names: tuple[str,...]) -> int:
        """
        Returns the total number of teams present for players in names
        """
        return len(set(self.teams(names)))


# ------------------------------- Checker functions -------------------------------
# Checking for various issues in combination of names


    @cache
    def check_guards(self, names: tuple[str,str]) -> bool:
        """
        Checks to make sure pair of PG/SG are good
        Duplicate check will already have been performed
        No teammates here, only time teammates good is 2 of G/F/C
        """

        if len(set(names)) != len(names):
            return False

        if self.cost(names) > self.pg_sg_max_cost:
            return False

        if not self.PAST:
    
            teams = self.teams(names)
            if len(set(teams)) == 1:
                if self.TEAM_MAX_PLAYERS.get(teams[0], self.TEAM_MAX) < 2:
                    return False
            
        
        return True

    @cache
    def check_forwards(self, names: tuple[str,str]) -> bool:
        """
        Checks to make sure pair of SF/PF are good
        Duplicate check will already have been performed
        No teammates here, only time teammates good is 2 of G/F/C
        """

        if len(set(names)) != len(names):
            return False
        
        if self.cost(names) > self.sf_pf_max_cost:
            return False

        if not self.PAST:
            teams = self.teams(names)
            if len(set(teams)) == 1:
                if self.TEAM_MAX_PLAYERS.get(teams[0], self.TEAM_MAX) < 2:
                    return False

        return True

    @cache
    def check_pg_sg_sf(self, names: tuple[str,str,str]) -> bool:

        if len(set(names)) != len(names):
            return False

        if self.cost(names) > self.pg_sg_sf_max_cost:
            return False

        if not self.PAST:
            teams = self.teams(names)
            if len(set(teams)) == 1:
                if self.TEAM_MAX_PLAYERS.get(teams[0], self.TEAM_MAX) < 2:
                    return False


        return True


    
    @cache
    def check_teams(self, names: tuple[str,...]) -> bool:
        teams = self.teams(names)

        if self.PAST:
            counts = [teams.count(team) for team in set(teams)]
            return max(counts) <= self.TEAM_MAX

        for team in set(teams):
            if teams.count(team) > self.TEAM_MAX_PLAYERS.get(team, self.TEAM_MAX):
                return False

        return True

    @cache
    def check2(self, names: tuple[str,str]) -> bool:
        """
        For both guard and forward duos for now
        """

        if self.PAST:
            return True
        
        return self.n_teams(names) == 2

    @cache
    def check4(self, names: tuple[str,str,str,str]) -> bool:
        """
        Checks to make sure 4 players are good together, duplicates already checked
        Checks involved here:
            - Teammate rules
            - Affordability
        Will be PG/SG/SF/PF
        """

        if self.PAST:
            return self.cost(names) <= self.four_max_cost and self.n_teams(names) > 1

        if self.cost(names) > self.four_max_cost or self.n_teams(names) == 1:
            return False

        if not self.check_teams(names):
            return False
        
        # if self.n_teams(names) < 3:
        #     return False

        # if self.cost(names) > self.four_max_cost:
        #     return False

        # if not self.check_teams(names):
        #     return False

        # if not self.check_games(names):
        #     return False

        # #Check teammates
        # if not self.check_teammates(names):
        #     return False

        # # if not self.check_salaries(names):
        # #     return False
            
        return True

    @cache
    def check5(self, names: tuple[str,str,str,str]) -> bool:
        """
        Checks to make sure 4 players are good together, duplicates already checked
        Checks involved here:
            - Teammate rules
            - Affordability
        Will be PG/SG/SF/PF/C
        """

        if self.PAST:
            return self.cost(names) <= self.five_max_cost and self.n_teams(names) > 1

        if self.cost(names) > self.five_max_cost or self.n_teams(names) == 1:
            return False

        if not self.check_teams(names):
            return False

        return True

    @cache
    def check6(self, names: tuple[str,str,str,str]) -> bool:
        """
        Checks to make sure 4 players are good together, duplicates already checked
        Checks involved here:
            - Teammate rules
            - Affordability
        Will be PG/SG/SF/PF/C/G
        """

        if self.PAST:
            return self.cost(names) <= self.six_max_cost and self.n_teams(names) > 1

        if self.cost(names) > self.six_max_cost or self.n_teams(names) == 1:
            return False

        if not self.check_teams(names):
            return False

        return True

    @cache
    def check7(self, names: tuple[str,str,str,str]) -> bool:
        """
        Checks to make sure 4 players are good together, duplicates already checked
        Checks involved here:
            - Teammate rules
            - Affordability
        Will be PG/SG/SF/PF/C/G/F
        """

        if self.PAST:
            return self.cost(names) <= self.seven_max_cost and self.n_teams(names) > 1

        if self.cost(names) > self.seven_max_cost or self.n_teams(names) < 3:
            return False

        if not self.check_teams(names):
            return False

        return True

    # @cache
    # def check8(self, names: tuple[str,str,str,str,str,str,str,str]) -> bool:
    #     """
    #     Checks to make sure 8 players are good together, including checking for duplicates
    #     For past, only checking if eligible lineups

    #     """
    #     if self.PAST:
    #         if self.cost(names) not in self.eight_cost_range:
    #             return False

    #         teams = self.teams(names)
    #         return max([teams.count(team) for team in set(teams)]) <= 4

    #     if self.cost(names) not in self.eight_cost_range:
    #         return False

    #     # if not self.check_salaries(names):
    #     #     return False

    #     if not self.check_teams(names):
    #         return False

    #     if not self.check_games(names):
    #         return False

    #     #Check teammates -> most involved function so better if last
    #     if not self.check_teammates(names):
    #         return False

    #     return True


    @cache
    def follows_rules(self, names: tuple[str,str,str,str,str,str,str,str]) -> bool:
        """
        Follows contest rules, added to below for now
        """

        if self.PAST:
            return all([
                self.mincost <= self.cost(names) <= self.maxcost,
                # len(set([game for game in self.games(names)])) > 1
            ])

        return self.mincost <= self.cost(names) <= self.maxcost

    @cache
    def check_lineup(self, names: tuple[str,str,str,str,str,str,str,str]) -> bool:
        if self.PAST:
            return self.follows_rules(names)

        return self.follows_rules(names) and self.check_teams(names) #self.n_teams(names) > 2 # for now


    @cache
    def ignore(self, names: tuple[str,...]) -> bool:
        """
        Always returns true, used as passing as default
        """
        return True
    
    @cache
    def check(self, names: tuple[str,...]) -> bool:
        
        #Check for duplicates
        if len(names) != len(set(names)):
            return False

        return {
            2: self.check2,
            4: self.check4,
            5: self.check5,
            6: self.check6,
            7: self.check7,
            8: self.check_lineup
        }.get(len(names), self.ignore)(self.order(names))

        

        
        



