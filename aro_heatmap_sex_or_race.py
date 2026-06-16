# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 08:56:19 2025

@author: M1
"""
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
import os

# --------------------------- SETTINGS ---------------------------
sns.set(style="whitegrid")
plt.rcParams.update({'figure.autolayout': True})
heatmap_cmap = 'coolwarm'
aro_clip = (-3, 3)

# ------------------------ SET SCRIPT CONTEXT ---------------------------
try:
    SCRIPT_DIR = os.path.dirname(__file__)
except NameError:
    SCRIPT_DIR = os.getcwd()

# Paths
db_path = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "cases.db"))
output_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(output_dir, exist_ok=True)

# --------------------------- LOAD DATA ---------------------------
conn = sqlite3.connect(db_path)
df_cpc_all = pd.read_sql_query("SELECT * FROM all_cases;", conn)
conn.close()

df_cpc_all = df_cpc_all[df_cpc_all['Sentence_System'] == 'Criminal Punishment Code'].copy()
df_unique_all = df_cpc_all.sort_values('sentence_years', ascending=False).drop_duplicates(subset='DCNumber')

# --------------------------- RACE MAPPING ---------------------------
race_map = {
    'White': 'White',
    'Black': 'Black',
    'Hispanic': 'Hispanic',
    'Asian': 'Other',
    'Indigenous / Pacific Islander': 'Other',
    'Other': 'Other'
}
df_unique_all['Race'] = df_unique_all['Race'].map(race_map).fillna('Other')

# --------------------------- POPULATION PROPORTIONS ---------------------------
sex_proportions = {'Male': 0.488, 'Female': 0.512}
race_proportions = {'White': 0.53, 'Black': 0.16, 'Hispanic': 0.26, 'Other': 0.05}

# --------------------------- ARO TABLE FUNCTION ---------------------------
def build_charge_group_table(df, group_col, group_props):
    count_table = df.groupby(['charge', group_col])['DCNumber'].nunique().unstack(fill_value=0)
    total_by_charge = count_table.sum(axis=1)

    expected_counts = pd.DataFrame(index=count_table.index, columns=count_table.columns)
    for group in count_table.columns:
        expected_counts[group] = total_by_charge * group_props.get(group, np.nan)

    aro_table = np.log((count_table + 1e-9) / (expected_counts + 1e-9))

    nested_data = {}
    for charge in count_table.index:
        nested_data[charge] = {}
        for group in count_table.columns:
            nested_data[charge][group] = {
                'count': int(count_table.loc[charge, group]),
                'ARO': float(aro_table.loc[charge, group]) if not pd.isna(aro_table.loc[charge, group]) else None
            }
    return pd.DataFrame.from_dict(nested_data, orient='index')

# --------------------------- FLATTEN FUNCTION ---------------------------
def flatten_group_table(nested_table, group_col):
    records = []
    for charge in nested_table.index:
        for group in nested_table.columns:
            cell = nested_table.loc[charge][group]
            records.append({
                'Charge': charge,
                group_col: group,
                'Count': cell['count'],
                'ARO': cell['ARO']
            })
    return pd.DataFrame(records)

# --------------------------- GENERATE FLAT TABLES ---------------------------
sex_table = build_charge_group_table(df_unique_all, 'Sex', sex_proportions)
race_table = build_charge_group_table(df_unique_all, 'Race', race_proportions)

df_sex = flatten_group_table(sex_table, 'Sex')
df_race = flatten_group_table(race_table, 'Race')
df_race = df_race[df_race['Race'].isin(['White', 'Black', 'Hispanic'])]

# --------------------------- YOUR DESIRED ROW ORDER ---------------------------
charge_order = [
    'FIRST_DEGREE_MURDER', 'SECOND_DEGREE_MURDER', 'THIRD_DEGREE_MURDER',
    'ATTEMPTED_MURDER', 'LAW_ENFORCEMENT_KILL', 'GENERAL_HOMICIDE',
    'FETAL_HOMICIDE', 'GENERAL_MANSLAUGHTER', 'NEGLIGENT_MANSLAUGHTER',
    'VEHICULAR_MANSLAUGHTER', 'DUI_BUI_MANSLAUGHTER'
]

# --------------------------- HEATMAP FUNCTION ---------------------------
def plot_aro_heatmap(df, group_col, title, filename):
    pivot_df = df.pivot(index='Charge', columns=group_col, values='ARO')
    pivot_df = pivot_df.clip(*aro_clip)

    # Reorder rows based on your specified order, drop missing charges automatically
    pivot_df = pivot_df.loc[[charge for charge in charge_order if charge in pivot_df.index]]

    plt.figure(figsize=(10, len(pivot_df) * 0.5))
    sns.heatmap(
        pivot_df,
        annot=True,
        cmap=heatmap_cmap,
        center=0,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={'label': 'ORE (log(actual / expected))'}
    )

    plt.xlabel(group_col)
    plt.ylabel('Charge')
    plt.tight_layout()

    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

# --------------------------- PLOT + SAVE HEATMAPS ---------------------------
plot_aro_heatmap(
    df_sex,
    group_col='Sex',
    title='ORE by Sex (All Charges)',
    filename='heatmap_sex.png'
)

plot_aro_heatmap(
    df_race,
    group_col='Race',
    title='ORE by Race (All Charges)',
    filename='heatmap_race.png'
)
