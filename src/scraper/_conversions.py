# Initials are currently in Basketball-Reference format
# Changed with standardize_initials

INITS_TEAMS = {
    'ATL': 'Atlanta Hawks',
    'BRK': 'Brooklyn Nets',
    'BOS': 'Boston Celtics',
    'CHO': 'Charlotte Hornets',
    'CHI': 'Chicago Bulls',
    'CLE': 'Cleveland Cavaliers',
    'DAL': 'Dallas Mavericks',
    'DEN': 'Denver Nuggets',
    'DET': 'Detroit Pistons',
    'GSW': 'Golden State Warriors',
    'HOU': 'Houston Rockets',
    'IND': 'Indiana Pacers',
    'LAC': 'LA Clippers',
    'LAL': 'Los Angeles Lakers',
    'MEM': 'Memphis Grizzlies',
    'MIA': 'Miami Heat',
    'MIL': 'Milwaukee Bucks',
    'MIN': 'Minnesota Timberwolves',
    'NOP': 'New Orleans Pelicans',
    'NYK': 'New York Knicks',
    'OKC': 'Oklahoma City Thunder',
    'ORL': 'Orlando Magic',
    'PHI': 'Philadelphia 76ers',
    'PHO': 'Phoenix Suns',
    'POR': 'Portland Trail Blazers',
    'SAS': 'San Antonio Spurs',
    'SAC': 'Sacramento Kings',
    'TOR': 'Toronto Raptors',
    'UTA': 'Utah Jazz',
    'WAS': 'Washington Wizards'
}

TEAMS_INITS = {v: k for k, v in INITS_TEAMS.items()}

def convert_teamname_to_initials(team_str: str) -> str:
    return TEAMS_INITS[team_str]


TEAM_CONVERSIONS = {
    'SAS': 'SA',
    'NOP': 'NO',
    'NYK': 'NY',
    'GSW': 'GS',
    # 'PHX': 'PHO',
    'CHO': 'CHA',
    'BRK': 'BKN'
}

def standardize_initials(team_inits: str) -> str:
    return TEAM_CONVERSIONS.get(team_inits, team_inits)


# May need to convert names as well