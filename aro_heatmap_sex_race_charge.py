# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 09:07:54 2025

@author: M1
"""
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
import os

# --------------------------- PATH SETUP ---------------------------
try:
    SCRIPT_DIR = os.path.dirname(__file__)
except NameError:
    SCRIPT_DIR = os.getcwd()

db_path = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "cases.db"))
output_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(output_dir, exist_ok=True)

# --------------------------- LOAD DATA ---------------------------
conn = sqlite3.connect(db_path)
df_all = pd.read_sql_query("SELECT * FROM all_cases;", conn)
conn.close()

# --------------------------- FILTER & CLEAN ---------------------------
df_cpc_all = df_all[df_all['Sentence_System'] == 'Criminal Punishment Code'].copy()
df_unique_all = df_cpc_all.sort_values('sentence_years', ascending=False).drop_duplicates(subset='DCNumber')

race_map = {
    'White': 'White',
    'Black': 'Black',
    'Hispanic': 'Hispanic',
    'Asian': 'Other',
    'Indigenous / Pacific Islander': 'Other',
    'Other': 'Other'
}
df_unique_all['Race'] = df_unique_all['Race'].map(race_map).fillna('Other')

# --------------------------- SETTINGS ---------------------------
florida_population_race_pct = {
    'White': 0.53,
    'Black': 0.16,
    'Hispanic': 0.26,
    'Other': 0.05
}
main_races = ['White', 'Black', 'Hispanic']
custom_palette = {
    'White': '#1f77b4',
    'Black': '#ff7f0e',
    'Hispanic': '#2ca02c'
}

# --------------------------- ARO TABLE FUNCTION ---------------------------
def build_charge_race_table(df, sex, race_proportions):
    df_sex = df[df['Sex'] == sex].copy()

    count_table = df_sex.groupby(['charge', 'Race'])['DCNumber'].nunique().unstack(fill_value=0)
    avg_sentence_table = df_sex.groupby(['charge', 'Race'])['sentence_years'].mean().unstack(fill_value=np.nan)
    total_by_charge = count_table.sum(axis=1)

    expected_counts = pd.DataFrame(index=count_table.index, columns=count_table.columns)
    for race in count_table.columns:
        expected_counts[race] = total_by_charge * race_proportions.get(race, np.nan)

    aro_table = np.log((count_table + 1e-9) / (expected_counts + 1e-9))

    nested_data = {}
    for charge in count_table.index:
        nested_data[charge] = {}
        for race in count_table.columns:
            nested_data[charge][race] = {
                'count': int(count_table.loc[charge, race]),
                'avg_sentence': float(avg_sentence_table.loc[charge, race]) if not pd.isna(avg_sentence_table.loc[charge, race]) else None,
                'ARO': float(aro_table.loc[charge, race]) if not pd.isna(aro_table.loc[charge, race]) else None
            }

    return pd.DataFrame.from_dict(nested_data, orient='index')

# --------------------------- BUILD MALE & FEMALE ARO TABLES ---------------------------
def flatten_nested_table(nested_table, sex_label):
    records = []
    for charge in nested_table.index:
        for race in nested_table.columns:
            cell = nested_table.loc[charge][race]
            if isinstance(cell, dict):
                records.append({
                    'Sex': sex_label,
                    'Race': race,
                    'Charge': charge,
                    'Count': cell['count'],
                    'ARO': cell['ARO']
                })
    return pd.DataFrame(records)

male_table = build_charge_race_table(df_unique_all, 'Male', florida_population_race_pct)
female_table = build_charge_race_table(df_unique_all, 'Female', florida_population_race_pct)

male_flat = flatten_nested_table(male_table, 'Male')
female_flat = flatten_nested_table(female_table, 'Female')
combined_flat = pd.concat([male_flat, female_flat], ignore_index=True)

# --------------------------- YOUR DESIRED ROW ORDER ---------------------------
charge_order = [
    'FIRST_DEGREE_MURDER', 'SECOND_DEGREE_MURDER', 'THIRD_DEGREE_MURDER',
    'ATTEMPTED_MURDER', 'LAW_ENFORCEMENT_KILL', 'GENERAL_HOMICIDE',
    'FETAL_HOMICIDE', 'GENERAL_MANSLAUGHTER', 'NEGLIGENT_MANSLAUGHTER',
    'VEHICULAR_MANSLAUGHTER', 'DUI_BUI_MANSLAUGHTER'
]

# ---------------------- HEATMAP FUNCTION (SAVED) ----------------------
def save_aro_heatmap(df, sex_label, race_filter, aro_clip=(-3, 3), filename='heatmap.png'):
    df_sex = df[
        (df['Sex'] == sex_label) & 
        (df['Race'].isin(race_filter))
    ].copy()

    aro_matrix = df_sex.pivot(index='Charge', columns='Race', values='ARO')
    aro_matrix = aro_matrix.clip(*aro_clip)

    # Reorder rows based on your specified order, dropping missing charges automatically
    aro_matrix = aro_matrix.loc[[charge for charge in charge_order if charge in aro_matrix.index]]

    plt.figure(figsize=(10, len(aro_matrix) * 0.5))
    sns.heatmap(
        aro_matrix,
        annot=True,
        cmap='coolwarm',
        center=0,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={'label': 'ORE (log(actual / expected))'}
    )
    # Remove title as requested
    # plt.title(f'ORE by Charge and Race ({sex_label})')
    plt.xlabel('Race')
    plt.ylabel('Charge')
    plt.tight_layout()

    plot_path = os.path.join(output_dir, filename)
    plt.savefig(plot_path, dpi=300)
    plt.close()

# ---------------------- SAVE ONLY NECESSARY HEATMAPS ----------------------
save_aro_heatmap(combined_flat, 'Male', main_races, filename='heatmap_race_charge_male.png')
save_aro_heatmap(combined_flat, 'Female', main_races, filename='heatmap_race_charge_female.png')
