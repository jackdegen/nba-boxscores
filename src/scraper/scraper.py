import requests
import datetime
import time
import glob

import pandas as pd
pd.set_option('display.max_columns', 100)

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from tqdm.notebook import tqdm

# Local code
from filing import Filing

from ._conversions import (
    convert_teamname_to_initials,
    standardize_initials
)

from ._dates import (
    PLAYOFF_DATES,
    SEASON_DATES,
    # TODAY
)

from ._info import (
    ADV_DATA_STATS,
    BASIC_DATA_STATS,
    FOUR_FACTORS_DATA_STATS,
    RENAME_COLUMNS,
)

# Scraper currently is missing position

class Scraper:
    
    def __init__(self, year=2022):
        """
        Takes year as input, defaults to last complete season
        """
        self.year: int = int(year)
        self.season: str = f'{self.year}-{self.year+1}'

        # Initialize filing object
        self.filing = Filing(self.season)

        # By default, start_date will be start of season
        start_date, end_date = SEASON_DATES[self.season]

        # Check to see if any files in boxscores dir so no possible IndexError
        # If files in boxscores directory, then has been at least partially updated, get most recent date
        if len([file for file in glob.glob(self.filing.boxscores_dir + '/*.csv')]):
            # start_date = self.filing.most_recent_boxscore_date()
            start_date = datetime.datetime.strftime(datetime.datetime.strptime(self.filing.most_recent_boxscore_date(), '%Y-%m-%d') + datetime.timedelta(days=1), format='%Y-%m-%d')
        
        self.season_date_list = [ date_.strftime('%Y-%m-%d') for date_ in pd.date_range(start_date, end_date) ]

        # Initialize driver to render full webpages
        ff_options = Options()
        ff_options.add_argument('--headless')

        self.driver = webdriver.Firefox(options=ff_options)

    def clean_name(self, name: str) -> str:
        """
        Standardizes name across Basketball-Reference, FD, DK
        """
        clean = ' '.join(name.split(' ')[:2]).replace('.', '')
        # return standardize_name(clean)
        return clean

    def correct_stat(self, stat: str, stat_val: int|float|str):
        if not len(stat_val):
            return 0.0
        
        if stat == 'mp':
            # If team total column
            if ':' not in stat_val:
                return 0.0
            min_, sec = [float(val_) for val_ in stat_val.split(':')] #if len(stat_val.split(':')) == 2 else 0, float(mp)
            return min_+(sec/60)
    
        return float(stat_val)

    def get_game_boxscores(self, date: str, game_soup) -> None:
        """
        Takes BeautifulSoup data from specific game (single webpage) and loads all data into pandas DataFrame
        Will create 2 csv files for every instance function is run
        """

        scorebox = game_soup.find_all('div', class_='scorebox')[0]

        # More than four stats lol
        four_factors_table = game_soup.find('table', id='four_factors').find('tbody')
    
        four_factor_stats = {
            stat: [self.correct_stat(stat, tag.get_text()) for tag in four_factors_table.find_all('td', attrs={'data-stat': stat})]
            for stat in FOUR_FACTORS_DATA_STATS
        }

        away_team, home_team = [convert_teamname_to_initials(scorebox.find_all('strong')[i].get_text().replace('\n', '')) for i in range(2)]
        away_score, home_score =  [int(score.get_text().replace('\n','')) for score in scorebox.find_all('div', class_='scores')]
    
        total = away_score + home_score
    
        winner = away_team if away_score > home_score else home_team
    
        # Going to make individual csv file for each team rather than for each game
        
        for team in (away_team, home_team):
            # First just get info from above
            is_home = team == home_team
            is_winner = team == winner
    
            score = home_score if is_home else away_score
            opp_score = away_score if is_home else home_score
            
            opp = away_team if is_home else home_team
            
            # Load table data
            basic_stat_table = game_soup.find('table', id=f'box-{team}-game-basic')
            adv_stat_table = game_soup.find('table', id=f'box-{team}-game-advanced')
            
            names = [
                self.clean_name(tag.get_text()) for tag in basic_stat_table.find_all('th', attrs={'data-stat': 'player'})
                if tag.get_text() not in ('Starters', 'Reserves', 'Team Totals')
            ]
    
            # Minutes played used to determine how many people played, remove last one because that is team total
            mp = [td.get_text() for td in basic_stat_table.find_all('td', attrs={'data-stat': 'mp'})][:-1]
    
            total_players = len(names)
            
            active = names[:len(mp)]
            inactive = names[len(mp):]
    
            num_active = len(active)
    
            starters = sum([
                [1]*5,
                [0]*(num_active-5)
            ], [])

            # Standardizing here
            game_info = {
                'team': standardize_initials(team), 
                'opp': standardize_initials(opp), 
                'home': int(is_home), 
                'score': score, 
                'opp_score': opp_score,
                'winner': int(is_winner),
                'spread': score - opp_score,
                'total': total
            }
    
            player_info = {
                # 'name': names,
                'name': active,
                'starter': starters,
            }

            # Load team stats from four factors table
            team_index = 1 if is_home else 0
            team_stats = {stat: stat_vals[team_index] for stat, stat_vals in four_factor_stats.items()}
    
            # Remove last item from each list because that is team total
            basic_data = {
                stat: [self.correct_stat(stat, td.get_text()) for td in basic_stat_table.find_all('td', attrs={'data-stat': stat})][:-1]
                for stat in BASIC_DATA_STATS
            }
    
            adv_data = {
                stat: [self.correct_stat(stat, td.get_text()) for td in adv_stat_table.find_all('td', attrs={'data-stat': stat})][:-1]
                for stat in ADV_DATA_STATS
            }
    
            team_data = {
                **{'date': [date]*num_active},
                **player_info,
                **{key: [val]*num_active  for key, val in game_info.items()},
                **{f'team-{stat}': [stat_val]*num_active for stat, stat_val in team_stats.items()},
                **basic_data,
                **adv_data
            }

            # Playoffs have no bpm
            team_data = {k: v for k, v in team_data.items() if len(v)}
            
            # No bonuses added
            df = (pd
                  .DataFrame(team_data)
                  .rename(RENAME_COLUMNS, axis=1)
                  .assign(
                      dk_fpts=lambda df_: df_.pts + 0.5*df_.fg3 + 1.25*df_.trb + 1.5*df_.ast + 2.0*df_.stl + 2.0*df_.blk - 0.5*df_.tov,
                      fd_fpts=lambda df_: df_.pts + 1.2*df_.trb + 1.5*df_.ast + 3.0*df_.stl + 3.0*df_.blk - 1.0*df_.tov
                  )
                 )
            
            self.filing.save_boxscore(df)
        
        time.sleep(1)
        
        return None

    def get_season_boxscores(self) -> None:
        """
        Iterates through every boxscore for every game of every day
        Saves to data directory
        """
        
        print(f'Beginning scraping for {self.season} season\n')
        # Root of all URLs to games found by searching for links on page
        # See: game_url
        root_url = 'https://www.basketball-reference.com'
        
        # URL to page that contains all boxscores for single date
        date_games_url_template = 'https://www.basketball-reference.com/boxscores/?month={month}&day={day}&year={year}'

        # Dates in YYYY-MM-DD format
        for date in tqdm(self.season_date_list):
            
            year, month, day = date.split('-')
            
            date_games_url = date_games_url_template.format(month=month, day=day, year=year)
            date_games_soup = BeautifulSoup(
                requests.get(date_games_url).text,
                'html.parser'
            )

            game_divs = date_games_soup.find_all('div', class_='game_summary expanded nohover')

            if len(game_divs):
            # Naming is a little confusing
                for game_div in game_divs:
    
                    # URL to boxscore for game on that day
                    # By doing this way, don't have to worry about weird URL formatting, simply getting the link
                    game_url = root_url + game_div.find('a', text='Box Score')['href']
                    self.driver.get(game_url)
                    game_soup = BeautifulSoup(
                        # requests.get(game_url).text,
                        self.driver.page_source,
                        'html.parser'
                    )
    
                    self.get_game_boxscores(date, game_soup)
            
            # Need to sleep somewhere so requests do not get blocked
            # Selenium causes webscraper to be much slower --> might not need as much time
            # time.sleep(1)
        
        
        return