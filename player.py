import pandas as pd

class Player:
    def __init__(self, row):
        if 'Name' not in row:
            print('Invalid row', row)
            return
        self.name = row['Name']
        self.main_position = row['Position']
        self.alt_positions = [row['AltPos1'], row['AltPos2'], row['AltPos3']]  # list of alternative positions
        self.alt_positions = [pos for pos in self.alt_positions if pd.notna(pos)]  # remove NaN values
        self.performance_scores = {
            'LB': row['percfb'], 
            'RB': row['percfb'],
            'CB': row['perccb'], 
            'LM': row['percwng'],
            'LW': row['percwng'],
            'RM': row['percwng'],
            'RW': row['percwng'],
            'CDM': row['perccdm'],
            'CM': row['perccm'],
            'CAM': row['perccam'],
            'LAM': row['perclam'],
            'RAM': row['percram'],
            'CF': row['perccf'],
            'ST': row['percst'],
            'GK': row['percgk']
        }
        self.cost = row['Cost']
        self.club = row['Club']
        self.nationality = row['Nationality']
        self.league = row['League']
        self.rank = row['rank']
        self.DAId = row['DAId']
        self.ID = row['ID']
        self.selected_position = None
    
    def __eq__(self, other):
        if isinstance(other, Player):
            return self.name == other.name  # Assuming name is a unique identifier
        return False
