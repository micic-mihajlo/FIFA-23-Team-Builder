
import pandas as pd

import numpy as np
from player import Player


df = pd.read_excel('players_data.xlsx')
print(df.head())
print(pd.ExcelFile('players_data.xlsx').sheet_names)
print(df.columns)
