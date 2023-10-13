import os
import glob

import pandas as pd

class Filing:

    def __init__(self, season: str):
        """
        Creates a filing object to save, load, organize, and track data effectively on local machine
        Takes season as single parameter in order to determine starting point for filing operations
        """

        self.season = season
        self.data_dir = os.getcwd().replace('src', 'data')
        self.season_dir = os.path.join(self.data_dir, season)
        self.boxscores_dir = os.path.join(self.season_dir, 'boxscores')
        
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


    def save_boxscore(self, df: pd.DataFrame, away: str, home: str) -> None:
        """
        Saves boxscore as csv (later on can configure different formats)
        Saves in form of away-home.csv --> Will never have duplication issues
        TODO: Generalize -> save(self, data_category, df, **kwargs) to save things other than boxscores 
        """
        filename = f'{away}-{home}.csv'
        
        fpath = os.path.join(self.boxscores_dir, filename)
        df.to_csv(fpath, index=False)

        return

    def load_boxscores(self) -> pd.DataFrame:
        """
        Loads boxscores already saved on local machine into massive pandas dataframe
        """
        
        if hasattr(self, 'boxscores'):
            return self.boxscores
        
        combined = (pd
                    .concat([
                        pd.read_csv(file) # Can take further operations on right here
                        for file in glob.glob(self.boxscores_dir + '/*.csv')
                    ])
                   )
        self.boxscores = {team_: combined.loc[combined['team']==team_] for team_ in combined['team'].drop_duplicates()}
        
        return self.boxscores