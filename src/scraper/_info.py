BASIC_DATA_STATS = [
    'mp',
    'fg',
    'fga',
    'fg_pct',
    'fg3',
    'fg3a',
    'fg3_pct',
    'ft',
    'fta',
    'ft_pct',
    'orb',
    'drb',
    'trb',
    'ast',
    'stl',
    'blk',
    'tov',
    'pf',
    'pts',
    'plus_minus'
]

ADV_DATA_STATS = [
    # 'mp' # --> repeated,
    'ts_pct',
    'efg_pct',
    'fg3a_per_fga_pct', # --> Rename
    'fta_per_fga_pct', # --> Rename
    'orb_pct',
    'drb_pct',
    'trb_pct',
    'ast_pct',
    'stl_pct',
    'blk_pct',
    'tov_pct',
    'usg_pct',
    'off_rtg',
    'def_rtg',
    'bpm'
]

RENAME_COLUMNS = {
    'ts_pct': 'ts',
    'usg_pct': 'usg',
    'fga3_per_fga_pct': 'fg3_rate',
    'fta_per_fga_pct': 'fta_rate',
}