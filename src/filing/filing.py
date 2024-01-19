import os
import glob
import datetime

import pandas as pd

class Filing:

    def __init__(self, season: str, **kwargs):
        """
        Creates a filing object to save, load, organize, and track data effectively on local machine
        Takes season as single parameter in order to determine starting point for filing operations
        """
        self.site = kwargs.get('site', 'draftkings')
        self.season = season
        # self.data_dir = os.getcwd().replace('src', 'data')
        self.data_dir = os.getcwd().split('/src')[0] + '/data' # Better this way than above incase src isn't last directory
        self.season_dir = os.path.join(self.data_dir, season)
        self.boxscores_dir = os.path.join(self.season_dir, 'boxscores')
        self.contests_dir = os.path.join(self.season_dir, 'contest-files', self.site, 'main-slate')
        
        # Check to make sure if directories exist, if not create them before doing any further operations
        for directory in (self.data_dir, self.season_dir, self.boxscores_dir):
            if not os.path.exists(directory):
                os.mkdir(directory)

    def clean_name(self, name: str) -> str:
        """
        Standardizes name across sites
        TODO: Make universal utilities module rather than repeat this function in various classes
        """
        return ' '.join(name.split(' ')[:2]).replace('.', '')


    def save_boxscore(self, df: pd.DataFrame) -> None:
        """
        Saves boxscore as csv (later on can configure different formats)
        Saves in form of {date}_{team}.csv --> Will never have duplication issues
            - date will be in .isoformat() so _ better than - in order to quickly separate team from date if necessary
            - filename.split('_')[0] == date
            - filename.split('_')[1].split('.')[0] for team without ".csv"
        TODO: Generalize -> save(self, data_category, df, **kwargs) to save things other than boxscores 
        """
        
        filename = f'{df["date"].iloc[0]}_{df["team"].iloc[0]}.csv'
        
        fpath = os.path.join(self.boxscores_dir, filename)
        df.to_csv(fpath, index=False)

        return

    def load_boxscores(self) -> pd.DataFrame:
        """
        Loads boxscores already saved on local machine into massive pandas dataframe
        TODO: Add ability to pass methods to perform on resulting dataframe as parameters
        """
        
        if hasattr(self, 'combined'):
            return self.combined
        
        self.combined = (pd
                         .concat([
                             pd.read_csv(file) # Can take further operations on right here
                             for file in glob.glob(self.boxscores_dir + '/*.csv')
                         ])
                        )
        
        return self.combined


    def load_contests(self) -> pd.DataFrame:
        """
        Loads contest files already saved on local machine into massive pandas dataframe with parameters set in constructor
        TODO: Add ability to pass methods to perform on resulting dataframe as parameters
        """
        
        if hasattr(self, 'contests'):
            return self.contests
        
        self.contests = (pd
                         .concat([
                             pd.read_csv(file) # Can take further operations on right here
                             for file in glob.glob(self.contests_dir + '/*.csv')
                         ])
                        )
        
        return self.contests

    @classmethod
    def extract_date_from_file(cls, file: str) -> str:
        """
        Extracts date from file path
        """
        return file.split('/')[-1].split('_')[0]

    @classmethod
    def sort_dates(cls, dates: list[str,...]):
        """
        Sorts a list of dates in str format
        Could probably get away without datetime conversions since format of dates
            - Done this way to be more correct
            - If date format is changed can simply change that argument and would still work
        """
        return [ datetime.datetime.strftime(dto, '%Y-%m-%d') for dto in sorted([datetime.datetime.strptime(date_str, '%Y-%m-%d') for date_str in dates], reverse=True) ]

    def most_recent_boxscore_date(self) -> str:
        """
        Returns the last date that boxscores have been scraped for in boxscores directory
        Purpose of this is to more quickly scrape/update data rather than start from beginning (season start date) each time
        """
        return self.sort_dates([self.extract_date_from_file(file) for file in glob.glob(self.boxscores_dir + '/*.csv')])[0]
        
        
        