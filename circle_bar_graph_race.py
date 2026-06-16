# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 02:57:57 2025

@author: M1
"""
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
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

# --------------------- FILTER TO ONLY POST-1998 CASES ---------------------
df_cpc_all = df_all[df_all['Sentence_System'] == 'Criminal Punishment Code'].copy()

# -------------------------- REMOVE DUPLICATES BY PERSON ------------------
df_unique_all = df_cpc_all.sort_values('sentence_years', ascending=False).drop_duplicates(subset='DCNumber')

# -------------------------- TOTAL UNIQUE INDIVIDUALS ---------------------
total_people = len(df_unique_all)

# --------------------------- RACE CONFIGS ---------------------------
race_order = ['White', 'Black', 'Hispanic', 'Asian', 'Indigenous/ Pacific Islander', 'Other / Unknown']
race_colors = dict(zip(race_order, sns.color_palette("tab10", n_colors=len(race_order))))

def short_label(race):
    return {
        'Indigenous/ Pacific Islander': 'Indig/Pac',
        'Other / Unknown': 'Other',
        'White': 'White',
        'Black': 'Black',
        'Hispanic': 'Hispanic',
        'Asian': 'Asian'
    }.get(race, race)

# ---------------------- FUNCTION: COMPUTE SUMMARY ------------------------
def compute_summary(df, groupby_cols):
    summary = df.groupby(groupby_cols).agg(
        count=('DCNumber', 'nunique'),
        average_sentence=('sentence_years', 'mean'),
        median_sentence=('sentence_years', 'median'),
        std_sentence=('sentence_years', 'std'),
        sem_sentence=('sentence_years', lambda x: x.std(ddof=1) / np.sqrt(len(x)))
    ).reset_index()
    
    summary['percentage'] = 100 * summary['count'] / total_people
    return summary[groupby_cols + ['count', 'percentage']]

# ------------------------ CALCULATE SUMMARIES ----------------------------
summary_by_race = compute_summary(df_unique_all, ['Race'])

# ----------------- FLORIDA GENERAL POPULATION BY RACE --------------------
fl_population_pct = pd.DataFrame({
    'Race': race_order,
    'population_percentage': [53, 16, 26, 3, 1, 1]
})

# ------------------- MERGE SUMMARIES ----------------
merged = pd.merge(
    summary_by_race[['Race', 'percentage']],
    fl_population_pct,
    on='Race',
    how='outer'
).fillna(0).rename(columns={'percentage': 'homicide_percentage'})

# Normalize to 100% for each ring
merged['homicide_norm'] = 100 * merged['homicide_percentage'] / merged['homicide_percentage'].sum()
merged['pop_norm'] = 100 * merged['population_percentage'] / merged['population_percentage'].sum()

# ------------------------ PREPARE DATA FOR PLOTTING ------------------
plot_data = merged.set_index('Race').reindex(race_order).reset_index()

outer_vals = plot_data['homicide_norm']
inner_vals = plot_data['pop_norm']
colors = [race_colors[r] for r in plot_data['Race']]

# -------------------------- DONUT CHART PLOTTING ------------------------
fig, ax = plt.subplots(figsize=(8, 8))

wedges_outer, _ = ax.pie(
    outer_vals,
    radius=1.0,
    startangle=90,
    counterclock=True,
    colors=colors,
    wedgeprops=dict(width=0.3, edgecolor='white')
)

wedges_inner, _ = ax.pie(
    inner_vals,
    radius=0.6,
    startangle=90,
    counterclock=True,
    colors=colors,
    wedgeprops=dict(width=0.3, edgecolor='white')
)

# ---------------------- ADD LABELS -----------------------------------
label_threshold = 1.0

for i, wedge in enumerate(wedges_outer):
    if outer_vals.iloc[i] < label_threshold:
        continue  
    ang = (wedge.theta2 + wedge.theta1) / 2
    x = np.cos(np.deg2rad(ang))
    y = np.sin(np.deg2rad(ang))
    ha = 'left' if x > 0 else 'right'
    label_text = f"{short_label(plot_data.loc[i, 'Race'])}\n{outer_vals.iloc[i]:.1f}%"
    ax.annotate(label_text, xy=(x * 1.15, y * 1.15), ha=ha, va='center', fontsize=9)

# ---------------------- LEGEND -----------------------------------
legend_patches = [
    Patch(color=race_colors[r], label=f"{short_label(r)}: {p:.1f}%")
    for r, p in zip(fl_population_pct['Race'], fl_population_pct['population_percentage'])
]

ax.legend(
    handles=legend_patches,
    loc='center left',
    bbox_to_anchor=(1, 0.5),
    title="Florida Population by Race"
)

ax.set(aspect='equal')
ax.axis('off')
plt.tight_layout()

# --------------------- SAVE DONUT AS PNG -------------------------------
donut_path = os.path.join(output_dir, "donut_race.png")
fig.savefig(donut_path, dpi=300, bbox_inches='tight')
plt.close()

# -------------------- BAR PLOT FUNCTION FOR RACE ------------------------
def plot_sentence_rate_by_race(df, sentence_type_filter, filename):
    df = df[df['Race'].notna()].copy()
    df['sentence_type'] = df['sentence_type'].str.lower()

    df_sent = df[df['sentence_type'] == sentence_type_filter.lower()]

    rates = (
        df_sent.groupby('Race')['DCNumber'].nunique() /
        df.groupby('Race')['DCNumber'].nunique()
    ).reset_index(name='percentage')

    rates['Race'] = pd.Categorical(rates['Race'], categories=race_order, ordered=True)
    rates = rates.set_index('Race').reindex(race_order, fill_value=0).reset_index()
    rates['percentage'] *= 100

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=rates, x='Race', y='percentage', palette=race_colors)
    ax.set_xticklabels([short_label(r) for r in rates['Race']])

    plt.ylabel("Percentage of Homicide Convictions Receiving Sentence")
    plt.xlabel("Race")
    plt.ylim(0, max(10, rates['percentage'].max() * 1.2))

    for bar in ax.patches:
        height = bar.get_height()
        if np.isnan(height) or height == 0:
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.5,
            f'{height:.1f}%',
            ha='center',
            va='bottom',
            fontsize=12,
        )

    plt.tight_layout()
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

# -------------------- CALL BAR PLOT FUNCTION ------------------------
plot_sentence_rate_by_race(
    df_unique_all,
    sentence_type_filter='life sentence',
    filename="life_rate_race.png"
)

plot_sentence_rate_by_race(
    df_unique_all,
    sentence_type_filter='death sentence',
    filename="death_rate_race.png"
)