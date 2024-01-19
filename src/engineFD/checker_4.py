import numpy as np
import pandas as pd

import itertools
from functools import cache

from typing import Any
### Checker 4 games
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

        mincost = 59_000

        self.mincost, self.maxcost = mincost, 60_000
        self.cost_range = self.maxcost - self.mincost

        self.n_games = int(len(data['team'].drop_duplicates()) / 2)
        self.TEAM_MAX = 3

        # Amount of teams that can have team_max players, see Checker.check_teams() for details
        self.NUM_TEAMS_TEAM_MAX = 1

        self.VALID_TEAM_DISTROS = [
            (1, 1, 1, 2, 2, 2),
            (1, 1, 1, 1, 2, 3),
            (1, 1, 1, 1, 1, 2, 2),
            (1, 1, 2, 2, 3)
        ]

        self.VALID_GAME_DISTROS = [
            (1, 2, 3, 3),
            (2, 2, 2, 3),
            (1, 2, 2, 4),
            (1, 1, 3, 4),
            (2, 3, 4) 
        ]

        # TODO: Export to own file
        self.BAD_TEAMMATES = (
            # Atlanta Hawks
            ('Trae Young', 'Saddiq Bey'),
            ('Dejounte Murray', 'Clint Capela'),
            ("De'Andre Hunter", 'Saddiq Bey'),
            ('Jalen Johnson', "De'Andre Hunter"),
            ("De'Andre Hunter", 'Bogdan Bogdanovic'),

            # Boston Celtics
            ('Jaylen Brown', 'Jayson Tatum'),

            # Chicago Bulls
            ('Coby White', 'Zach LaVine'),
            ('Coby White', 'Nikola Vucevic'),

            # Cleveland Cavaliers
            ('Donovan Mitchell', 'Darius Garland'),
            ('Donovan Mitchell', 'Jarrett Allen'),

            # New York Knicks
            ('RJ Barrett', 'Josh Hart'),
            ('Jalen Brunson', 'Josh Hart'),
            
            # Toronto Raptors
            ('Pascal Siakam', 'Scottie Barnes'),
            # ('Pascal Siakam', 'Jakob Poeltl'),

            # Sacramento Kings
            ('Kevin Huerter', 'Malik Monk'),
            ('Malik Monk', 'Harrison Barnes'),
            ('Malik Monk', 'Keegan Murray'),
        )

        self.BAD_TEAMMATES = tuple([tuple(sorted(duo)) for duo in self.BAD_TEAMMATES])

        salaries = data.sort_values('salary')['salary']

        # 5 cheapest salaries
        sum_min_5_sals = sum(list(salaries)[:5])

        self.four_max_cost = (60_000 - sum_min_5_sals) - self.cost_range

        # Want to figure out minimum cost for 8 players to be, adding center last so will be max_c_sal
        # min(8_players) = 60_000 - max_C_sal - self.cost_range
        # if max_C_sal + cost(8_players) < 60_000 - self.cost_range: reject

        # Optimal C never less than 5_300 for 7-game slate, will still consider less than for PAST results to test this
        C_salaries = data.loc[data['pos'].isin(['C/PF', 'PF/C', 'C']), 'salary']
        
        min_C_sal = C_salaries.min() #if self.PAST else 4_000
        max_C_sal = C_salaries.max()

        # Lower threshold of cost of eight players
        self.eight_min_cost = (60_000 - max_C_sal) - self.cost_range
        # Upper threshold off cost of eight players
        self.eight_max_cost = (60_000 - min_C_sal) - self.cost_range

        self.eight_cost_range = range(self.eight_min_cost, self.eight_max_cost+1, 100)

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
    def n_teams(self, names: tuple[str,...]) -> int:
        """
        Returns the total number of teams present for players in names
        """
        return len(set(self.teams(names)))


# ------------------------------- Checker functions -------------------------------
# Checking for various issues in combination of names

    @cache
    def check_teams(self, names: tuple[str,...]) -> bool:
        """
        Checks to make sure doesn't violate TEAM_MAX rules
        If past flag:
            - Check to make sure no more than preset TEAM_MAX
            - Do not want to have any additional checks in order to not drop potentially optimal lineups
            - Dealing with less input, so can handle greater load
        If not past flag:
            - Check to make sure no more than preset TEAM_MAX 
            - AND check to make sure no more than preset NUM_TEAMS_TEAM_MAX
            - Example:
                - NUM_TEAMS_TEAM_MAX, TEAM_MAX = 2,2
                - Check to make sure only two teams have two players, rest only 1 player
        """


        if self.PAST:
            return True
            
        teams = self.teams(names)
        n_teams = len(set(teams))

        if len(names) == 4:
            return n_teams > 1
        
        counts = [teams.count(team) for team in set(teams)]

        if max(counts) > self.TEAM_MAX:
            return False
        
        if len(names) == 9:
            distro = tuple(sorted(counts))
            return distro in self.VALID_TEAM_DISTROS

        # This is mostly to reduce throughput, can be tinkered with more easily since past optimals involve less input
        # if self.PAST:
        #     return max(counts) <= self.TEAM_MAX

        # How many of each counts of teams
        # First check to make sure no violations
        """
        - This naming is dope!!
        - Already checked to make sure no team violates having more players than TEAM_MAX
            -Example:
                - teams = [atl, bkn, cha, atl, bkn, den, nyk, no, gs]
                - counts = [2, 2, 1, 1, 1, 1, 1]
                - counts_of_counts = {2: 2, 1: 5}
        """

        counts_of_counts = {count_: counts.count(count_) for count_ in set(counts)}

        # Dont need to check gt self.TEAM_MAX since that would already return False
        if self.TEAM_MAX in counts_of_counts and counts_of_counts[self.TEAM_MAX] > self.NUM_TEAMS_TEAM_MAX:
            return False
        
        
        return True

    @cache
    def check_games(self, names: tuple[str,...]) -> bool:
        """
        - Determines how many games being played with lineup, used only for len(names) in (8,9)
        - Example:
            - Games: 1. atl_bkn, 2. cha_det, 3. den_okc, 4. gs_hou, 5. no_nyk, 6. dal_phi, 7. por_tor
            - Lineup teams: [atl, bkn, atl, cha, den, hou, no, dal, phi]
            - Lineup games: [1, 1, 1, 2, 3, 4, 5, 6, 6]
            - num_games: 6 (len(set(lineup_games)))
        """

        # Just to be safe at first
        if self.PAST or len(names) != 9:
            return True

        games = self.games(names)
        n_games = len(set(games))

        if n_games not in (3,4):
            return False

        counts = [games.count(game) for game in set(games)]
        distro = tuple(sorted(counts))
        
        return distro in self.VALID_GAME_DISTROS


    @cache
    def check_salaries(self, names: tuple[str,...]) -> bool:
        """
        Forces adjustments to get greater spread in salaries based on past performances
        Lot of builds funneled to include 2 4_000 - 5_000 guys
        Going to force either 1 < 4_000 or 0 < 5_000 guys
        """

        if self.PAST:
            return True

        sals = self.salaries(names)

        num_players = len(names)

        # if len(names) < 8:
            # Testing out
        num_lt4k = len([sal for sal in sals if sal < 4_000])

        if num_lt4k > 1:
            return False

        num_lt5k = len([sal for sal in sals if sal < 5_000])

        if num_players > 4 and num_lt5k > 4:
            return False

        if num_players == 8:

            if num_lt5k not in (0,1,2,3):
                return False
            
            num_lt6k = len([sal for sal in sals if sal < 6_000])
            if num_lt6k not in (2,3,4):
                return False

            num_lt7k = len([sal for sal in sals if sal < 7_000])
            if num_lt7k not in (3,4,5):
                return False
                

        # # No paying down for center so should overlap
        # if len(names) in (8,9):

            
        #     lt4k_present = len([sal for sal in sals if sal < 4_000])
        #     lt5k_gt4k_present = len([sal for sal in sals if 4_000 <= sal < 5_000])

        #     # one_4k = lt5k_gt4k_present == 1

        #     # if one_4k:
        #     #     return False
            
        #     # Having someone 4800 is ok if also someone less than 4000, but not ok if not
        #     if lt5k_gt4k_present and not lt4k_present:
        #         return False

        return True

    @cache
    def check_teammates(self, names: tuple[str,...]) -> bool:
        """
        Gets rid of teammates that correlate very badly with one another
        Be careful
        """

        if self.PAST:
            return True

        # if len(names) == 2:
        #     return tuple(sorted(names)) not in self.BAD_TEAMMATES

        # Duos of all players
        duos = [tuple(sorted(combo)) for combo in itertools.combinations(names, 2)]

        # Reduce to teammates
        duos = [duo for duo in duos if self.n_teams(duo) == 1]

        for duo in duos:
            if duo in self.BAD_TEAMMATES:
                return False

        return True
            

    @cache
    def check2(self, names: tuple[str,str]) -> bool:
        """
        Checks to make sure pair of players are good together, including checking for duplicates
        No teammates here, only time teammates good is 2 of G/F/C
        """

        if self.n_teams(names) == 1:
            return tuple(sorted(names)) not in self.BAD_TEAMMATES

        return True

    @cache
    def check4(self, names: tuple[str,str,str,str]) -> bool:
        """
        Checks to make sure 4 players are good together, duplicates already checked
        Checks involved here:
            - Teammate rules
            - Affordability
        """

        # Technically possible but extremely unlikely to have all four Gs or Fs in optimal, especially with MPE
        if self.n_teams(names) == 1:
            return False

        if self.cost(names) > self.four_max_cost:
            return False

        if not self.check_teams(names):
            return False

        if not self.check_teammates(names):
            return False

        # if not self.check_salaries(names):
        #     return False
            
        return True

    @cache
    def check8(self, names: tuple[str,str,str,str,str,str,str,str]) -> bool:
        """
        Checks to make sure 8 players are good together, including checking for duplicates
        For past, only checking if eligible lineups

        """
        if self.PAST:
            # if self.cost(names) > self.eight_max_cost:
            if self.cost(names) not in self.eight_cost_range:
                return False

            teams = self.teams(names)
            return max([teams.count(team) for team in set(teams)]) <= 4

        if self.cost(names) not in self.eight_cost_range:
            return False

        # if not self.check_salaries(names):
        #     return False

        if not self.check_teams(names):
            return False

        if not self.check_teammates(names):
            return False

        # if not self.check_games(names):
        #     return False

        return True


    @cache
    def follows_rules(self, names: tuple[str,str,str,str,str,str,str,str,str]) -> bool:
        """
        Follows contest rules, added to below for now
        """
        # return self.check9(names)
        teams = self.teams(names)
        return self.mincost <= self.cost(names) <= self.maxcost and max([teams.count(team) for team in set(teams)]) <= 4

    @cache
    def check9(self, names: tuple[str,str,str,str,str,str,str,str,str]) -> bool:
        """
        Checks to make sure 9 players are good together, including checking for duplicates and cost
        """
        
        if self.PAST:
            # PAST only cares about if rules are followed
            return self.follows_rules(names)

        if not self.follows_rules(names):
            return False

        # if not self.check_salaries(names):
        #     return False

        if not self.check_teams(names):
            return False

        if not self.check_games(names):
            return False

        if not self.check_teammates(names):
            return False

        return True

    

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

        #Check teammates
        # if not self.check_teams(names):
        #     return False
        

        # Check teammates for 2 games
        # if self.n_games == 2:
        #     if self.n_teams(names) != 4:
        #         return False

        return {
            2: self.check2,
            4: self.check4,
            8: self.check8,
            9: self.check9,
        }.get(len(names), self.ignore)(self.order(names))
        
        



