import datetime


TODAY = datetime.date.today()
YESTERDAY = TODAY - datetime.timedelta(days=1)
# Dictionary of start and end dates indexed by season
SEASON_DATES = {
    '2018-2019': ['2018-10-16', '2019-06-13'],
    '2019-2020': ['2019-10-22', '2020-10-11'], # Covid year
    '2020-2021': ['2020-12-22', '2021-07-20'], # Covid year
    '2021-2022': ['2021-10-19', '2022-06-16'],
    '2022-2023': ['2022-10-18', '2023-06-12'],
    '2023-2024': ['2023-10-24', YESTERDAY.isoformat()] # pd.date_range is inclusive of both
}

# Includes play-in from time it started
PLAYOFF_DATES = {
    '2018-2019': ['2019-04-13', '2019-06-13'],
    '2019-2020': ['2020-08-15', '2020-10-11'],
    '2020-2021': ['2021-05-18', '2021-07-20'], # Play-In started
    '2021-2022': ['2022-04-12', '2022-06-16'],
    '2022-2023': ['2023-04-11', '2023-06-12'],
    '2023-2024': ['2024-04-11', '2024-06-12'] # Will not work until season start
}