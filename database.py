# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 04:15:53 2025

@author: M1
"""

import pandas as pd
import sqlite3

df_all = pd.read_csv('all_cases.csv')
df_fixed = pd.read_csv('fixed_cases.csv')

conn = sqlite3.connect('cases.db')

df_all.to_sql('all_cases', conn, if_exists='replace', index=False)
df_fixed.to_sql('fixed_cases', conn, if_exists='replace', index=False)

conn.commit()
conn.close()

