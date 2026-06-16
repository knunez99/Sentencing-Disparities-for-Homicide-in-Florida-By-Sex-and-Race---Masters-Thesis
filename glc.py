# -*- coding: utf-8 -*-
"""
Created on Sun Jul 20 07:59:54 2025

@author: M1
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from numpy import trapz
import sqlite3
import os

# --------------------------- SETTINGS ---------------------------
sns.set(style="whitegrid")
plt.rcParams.update({'figure.autolayout': True})

# ------------------------ SET SCRIPT CONTEXT ---------------------------
try:
    SCRIPT_DIR = os.path.dirname(__file__)
except NameError:
    SCRIPT_DIR = os.getcwd()

db_path = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "cases.db"))
output_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(output_dir, exist_ok=True)

# --------------------------- LOAD DATA -----------------------------------
conn = sqlite3.connect(db_path)
df_fixed = pd.read_sql_query("SELECT * FROM fixed_cases;", conn)
conn.close()

df_cpc_fixed = df_fixed[df_fixed['Sentence_System'] == 'Criminal Punishment Code'].copy()
df_unique_fixed = df_cpc_fixed.sort_values('sentence_years', ascending=False).drop_duplicates(subset='DCNumber')

race_map = {
    'White': 'White',
    'Black': 'Black',
    'Hispanic': 'Hispanic',
    'Asian': 'Other',
    'Indigenous / Pacific Islander': 'Other',
    'Other': 'Other'
}
df_unique_fixed['Race'] = df_unique_fixed['Race'].str.strip().str.title().map(race_map).fillna('Other')

df_unique_fixed = df_unique_fixed[df_unique_fixed['sentence_years'].notnull()]
df_unique_fixed['sentence_years'] = pd.to_numeric(df_unique_fixed['sentence_years'], errors='coerce')
df_unique_fixed = df_unique_fixed[df_unique_fixed['sentence_years'] > 0]

df_unique_fixed_filtered = df_unique_fixed[df_unique_fixed['Race'] != 'Other'].copy()

# --------------------------- FUNCTIONS -----------------------------------
def generalized_lorenz_curve(values):
    sorted_vals = np.sort(values)
    cumvals = np.cumsum(sorted_vals)
    cumvals = np.insert(cumvals, 0, 0)
    cumprop = np.linspace(0, 1, len(cumvals))
    n = len(values)
    cumavg = cumvals / n
    return cumprop, cumavg

def glc_area(values):
    x, y = generalized_lorenz_curve(values)
    return trapz(y, x)

def plot_generalized_lorenz(data_series_list, labels, colors_dict=None, filename=None):
    plt.figure(figsize=(10, 7))
    for data, label in zip(data_series_list, labels):
        color = colors_dict[label] if colors_dict and label in colors_dict else None
        x, y = generalized_lorenz_curve(data)
        plt.plot(x, y, label=label, color=color)
    plt.xlabel('Cumulative Proportion of Defendants')
    plt.ylabel('Cumulative Average Sentence Years')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    if filename:
        plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

# --------------------------- COLOR MAPS -----------------------------------
sex_colors = {'Male': '#90ee90', 'Female': '#C21E56'}
sex_labels = [f"{s}" for s in df_unique_fixed_filtered['Sex'].unique()]
sex_color_map = {f"{s}": sex_colors.get(s, None) for s in df_unique_fixed_filtered['Sex'].unique()}

race_colors = {'White': 'blue', 'Black': 'orange', 'Hispanic': 'green'}
race_labels = [f"{r}" for r in df_unique_fixed_filtered['Race'].unique()]
race_color_map = {f"{r}": race_colors.get(r, None) for r in df_unique_fixed_filtered['Race'].unique()}

# --------------------------- PLOTS -----------------------------------
# By Sex
sex_groups = [df_unique_fixed_filtered[df_unique_fixed_filtered['Sex'] == s]['sentence_years'] for s in df_unique_fixed_filtered['Sex'].unique()]
plot_generalized_lorenz(sex_groups, sex_labels,
                        colors_dict=sex_color_map,
                        filename='glc_by_sex.png')

# By Race
race_groups = [df_unique_fixed_filtered[df_unique_fixed_filtered['Race'] == r]['sentence_years'] for r in df_unique_fixed_filtered['Race'].unique()]
plot_generalized_lorenz(race_groups, race_labels,
                        colors_dict=race_color_map,
                        filename='glc_by_race.png')

# --------------------------- GLC AREA SUMMARIES -----------------------------------
print("\nGLC area - Aggregate:")
print(f"  Aggregate: {glc_area(df_unique_fixed_filtered['sentence_years']):.2f}")

print("\nGLC areas by Sex:")
for sex in df_unique_fixed_filtered['Sex'].unique():
    area = glc_area(df_unique_fixed_filtered[df_unique_fixed_filtered['Sex'] == sex]['sentence_years'])
    print(f"  {sex}: {area:.2f}")

print("\nGLC areas by Race:")
for race in df_unique_fixed_filtered['Race'].unique():
    area = glc_area(df_unique_fixed_filtered[df_unique_fixed_filtered['Race'] == race]['sentence_years'])
    print(f"  {race}: {area:.2f}")

print("\nGLC areas by Sex + Race:")
for sex in df_unique_fixed_filtered['Sex'].unique():
    for race in df_unique_fixed_filtered['Race'].unique():
        subset = df_unique_fixed_filtered[(df_unique_fixed_filtered['Sex'] == sex) & (df_unique_fixed_filtered['Race'] == race)]
        if len(subset) > 0:
            area = glc_area(subset['sentence_years'])
            print(f"  {sex} - {race}: {area:.2f}")

# --------------------------- CHARGE-LEVEL GLC PLOTS -----------------------------------
charges = df_unique_fixed_filtered['charge'].dropna().unique()

glc_by_charge = []
glc_by_sex_charge = []
glc_by_race_charge = []

def safe_filename(name):
    return name.replace(' ', '_').replace('/', '_').replace('\\', '_')

for charge in charges:
    charge_subset = df_unique_fixed_filtered[df_unique_fixed_filtered['charge'] == charge]
    if len(charge_subset) > 10:
        area = glc_area(charge_subset['sentence_years'])
        glc_by_charge.append({
            'Charge': charge,
            'GLC_Area': area,
            'Mean': charge_subset['sentence_years'].mean(),
            'Count': len(charge_subset)
        })

    # By Sex per charge
    for sex in charge_subset['Sex'].dropna().unique():
        subset = charge_subset[charge_subset['Sex'] == sex]
        if len(subset) > 10:
            area = glc_area(subset['sentence_years'])
            glc_by_sex_charge.append({
                'Charge': charge,
                'Sex': sex,
                'GLC_Area': area,
                'Mean': subset['sentence_years'].mean(),
                'Count': len(subset)
            })

    sex_groups = []
    sex_labels = []
    for sex in charge_subset['Sex'].dropna().unique():
        subset = charge_subset[charge_subset['Sex'] == sex]
        if len(subset) > 10:
            sex_groups.append(subset['sentence_years'])
            sex_labels.append(sex)

    if sex_groups:
        filename = f"glc_by_sex_{safe_filename(charge)}.png"
        plot_generalized_lorenz(sex_groups, sex_labels, colors_dict=sex_color_map, filename=filename)

    # By Race per charge
    for race in charge_subset['Race'].dropna().unique():
        subset = charge_subset[charge_subset['Race'] == race]
        if len(subset) > 10:
            area = glc_area(subset['sentence_years'])
            glc_by_race_charge.append({
                'Charge': charge,
                'Race': race,
                'GLC_Area': area,
                'Mean': subset['sentence_years'].mean(),
                'Count': len(subset)
            })

    race_groups = []
    race_labels = []
    for race in charge_subset['Race'].dropna().unique():
        subset = charge_subset[charge_subset['Race'] == race]
        if len(subset) > 10:
            race_groups.append(subset['sentence_years'])
            race_labels.append(race)

    if race_groups:
        filename = f"glc_by_race_{safe_filename(charge)}.png"
        plot_generalized_lorenz(race_groups, race_labels, colors_dict=race_color_map, filename=filename)

# --------------------------- CREATE DATAFRAMES -----------------------------------
df_unique_fixed_glc_by_sex_charge = pd.DataFrame(glc_by_sex_charge).sort_values('GLC_Area', ascending=False)
df_unique_fixed_glc_by_race_charge = pd.DataFrame(glc_by_race_charge).sort_values('GLC_Area', ascending=False)

# --------------------------- DISPLAY SUMMARY TABLES -----------------------------------
print("\nGLC Summary - Sex per Charge:")
print(df_unique_fixed_glc_by_sex_charge)

print("\nGLC Summary - Race per Charge:")
print(df_unique_fixed_glc_by_race_charge)

# --------------------------- VISUALIZE SUMMARY BARPLOTS -----------------------------------
sex_palette = {'Male': '#90ee90', 'Female': '#C21E56'}
race_palette = {'White': '#1f77b4', 'Black': '#ff7f0e', 'Hispanic': '#2ca02c'}

plt.figure(figsize=(12, 8))
sns.barplot(data=df_unique_fixed_glc_by_sex_charge, y='Charge', x='GLC_Area', hue='Sex', palette=sex_palette)
plt.title('GLC Area by Charge and Sex')
plt.xlabel('GLC Area')
plt.ylabel('Charge')
plt.legend(title='Sex')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'glc_area_by_sex_charge.png'), dpi=300)
plt.close()

plt.figure(figsize=(12, 8))
sns.barplot(data=df_unique_fixed_glc_by_race_charge, y='Charge', x='GLC_Area', hue='Race', palette=race_palette)
plt.title('GLC Area by Charge and Race')
plt.xlabel('GLC Area')
plt.ylabel('Charge')
plt.legend(title='Race')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'glc_area_by_race_charge.png'), dpi=300)
plt.close()
