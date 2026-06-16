# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 02:00:30 2025

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
    return summary[groupby_cols + ['count', 'percentage', 'average_sentence', 'median_sentence', 'std_sentence', 'sem_sentence']]

# ------------------------ CALCULATE SUMMARY BY SEX ----------------------------
summary_by_sex = compute_summary(df_unique_all, ['Sex'])

# ----------------- FLORIDA POPULATION BY SEX ----------------------
fl_pop_sex = pd.DataFrame({
    'Sex': ['Male', 'Female'],
    'population_percentage': [48.8, 51.2]
})

# ------------------- MERGE AND NORMALIZE --------------------------
merged = pd.merge(
    summary_by_sex[['Sex', 'percentage']],
    fl_pop_sex,
    on='Sex',
    how='outer'
).fillna(0).rename(columns={'percentage': 'homicide_percentage'})

merged['homicide_norm'] = 100 * merged['homicide_percentage'] / merged['homicide_percentage'].sum()
merged['pop_norm'] = 100 * merged['population_percentage'] / merged['population_percentage'].sum()

# ----------------------- COLORS SETUP ------------------------------
sex_colors = {'Male': '#90ee90', 'Female': '#C21E56'}

# -------------------------- PLOTTING DONUT CHART -------------------------------
outer_radius = 1.0
outer_width = 0.25
inner_radius = outer_radius - outer_width - 0.05  
inner_width = 0.25

fig, ax = plt.subplots(figsize=(8, 8))

wedges_outer, _ = ax.pie(
    merged['homicide_norm'],
    radius=outer_radius,
    startangle=90,
    colors=[sex_colors[s] for s in merged['Sex']],
    wedgeprops=dict(width=outer_width, edgecolor='white')
)

wedges_inner, _ = ax.pie(
    merged['pop_norm'],
    radius=inner_radius,
    startangle=90,
    colors=[sex_colors[s] for s in merged['Sex']],
    wedgeprops=dict(width=inner_width, edgecolor='white')
)

# ----------------------- ADD LABELS -------------------------------
for i, wedge in enumerate(wedges_outer):
    sex = merged.iloc[i]['Sex']
    pct = merged.iloc[i]['homicide_norm']
    ang = (wedge.theta2 + wedge.theta1) / 2
    x = np.cos(np.deg2rad(ang))
    y = np.sin(np.deg2rad(ang))
    ha = 'left' if x > 0 else 'right'

    ax.annotate(
        f"{sex}\n{pct:.1f}%",
        xy=(x * 1.1, y * 1.1),
        ha=ha,
        va='center',
        fontsize=12,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.7)
    )

# ------------------------- LEGEND ----------------------------------
legend_patches = [
    Patch(color=sex_colors[s], label=f"{s} ({p:.1f}%)")
    for s, p in zip(merged['Sex'], merged['population_percentage'])
]

ax.legend(handles=legend_patches, title='Florida Population by Sex', loc='center left', bbox_to_anchor=(1, 0.5))

# ----------------------- FINAL SETTINGS ----------------------------
ax.set(aspect='equal')
ax.axis('off')
plt.tight_layout()

# --------------------- SAVE DONUT AS PNG -------------------------------
donut_path = os.path.join(output_dir, "donut_sex.png")
fig.savefig(donut_path, dpi=300, bbox_inches='tight')
plt.close()

# --------------------- LIFE & DEATH SENTENCE RATES BY SEX ---------------------
def plot_sentence_rate_by_sex(df_all, sentence_type_filter, filename):
    df_all = df_all[df_all['Sex'].notna()].copy()
    df_all['sentence_type'] = df_all['sentence_type'].str.lower()

    df_sent = df_all[df_all['sentence_type'] == sentence_type_filter.lower()]

    rates = (
        df_sent.groupby('Sex')['DCNumber'].nunique() /
        df_all.groupby('Sex')['DCNumber'].nunique()
    ).reset_index(name='percentage')

    rates['percentage'] *= 100

    plt.figure(figsize=(6, 5))
    ax = sns.barplot(data=rates, x='Sex', y='percentage', palette=sex_colors)
    plt.ylabel("Percentage of Homicide Convictions Receiving Sentence")
    plt.xlabel("Sex")
    plt.ylim(0, max(10, rates['percentage'].max() * 1.2))

    for bar in ax.patches:
        height = bar.get_height()
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

# ---------------------- CALL THE FUNCTIONS ----------------------
plot_sentence_rate_by_sex(
    df_unique_all,
    sentence_type_filter='life sentence',
    filename="life_rate_sex.png"
)

plot_sentence_rate_by_sex(
    df_unique_all,
    sentence_type_filter='death sentence',
    filename="death_rate_sex.png"
)
