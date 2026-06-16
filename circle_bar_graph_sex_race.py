# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 02:45:29 2025

@author: M1
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
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

# Paths
db_path = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "cases.db"))
output_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "plots"))
os.makedirs(output_dir, exist_ok=True)

# --------------------------- LOAD DATA ---------------------------
conn = sqlite3.connect(db_path)
df_all = pd.read_sql_query("SELECT * FROM all_cases;", conn)
conn.close()

df_cpc_all = df_all[df_all['Sentence_System'] == 'Criminal Punishment Code'].copy()
df_unique_all = df_cpc_all.sort_values('sentence_years', ascending=False).drop_duplicates(subset='DCNumber')

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
    return summary[groupby_cols + ['count', 'percentage']]

summary_by_sex_race = compute_summary(df_unique_all, ['Sex', 'Race'])

# ----------------- FLORIDA GENERAL POPULATION BY RACE --------------------
fl_population_pct = pd.DataFrame({
    'Race': ['White', 'Black', 'Hispanic', 'Asian', 'Indigenous/ Pacific Islander', 'Other / Unknown'],
    'population_percentage': [53, 16, 26, 3, 1, 1]
})

# ------------------ EXPAND POPULATION BY SEX ----------------
pop_expanded = pd.concat([
    fl_population_pct.assign(Sex='Male', population_percentage=fl_population_pct['population_percentage'] * 0.488),
    fl_population_pct.assign(Sex='Female', population_percentage=fl_population_pct['population_percentage'] * 0.512)
], ignore_index=True)

pop_expanded['population_percentage'] = pop_expanded.groupby('Sex')['population_percentage'].transform(
    lambda x: 100 * x / x.sum()
)

# -------------------------- MERGE SUMMARIES -------------------------------
merged = pd.merge(
    summary_by_sex_race[['Sex', 'Race', 'percentage']],
    pop_expanded,
    on=['Sex', 'Race'],
    how='outer'
).fillna(0).rename(columns={'percentage': 'homicide_percentage'})

merged['homicide_norm'] = merged.groupby('Sex')['homicide_percentage'].transform(lambda x: 100 * x / x.sum())
merged['pop_norm'] = merged.groupby('Sex')['population_percentage'].transform(lambda x: 100 * x / x.sum())

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

def prep_group(df, value_col):
    df = df.set_index('Race').reindex(race_order).reset_index()
    return df[df[value_col] > 0].reset_index(drop=True)

pop_male = prep_group(merged[merged['Sex'] == 'Male'], 'pop_norm')
pop_female = prep_group(merged[merged['Sex'] == 'Female'], 'pop_norm')
hom_male = prep_group(merged[merged['Sex'] == 'Male'], 'homicide_norm')
hom_female = prep_group(merged[merged['Sex'] == 'Female'], 'homicide_norm')

pop_female = pop_female[::-1].reset_index(drop=True)
hom_female = hom_female[::-1].reset_index(drop=True)

spacer_main = 2.0
spacer_top = 1.0

def add_spacers(male_df, female_df, value_col):
    spacer_top_df = pd.DataFrame([{'Sex': 'Spacer', 'Race': 'Spacer', value_col: spacer_top}])
    spacer_main_df = pd.DataFrame([{'Sex': 'Spacer', 'Race': 'Spacer', value_col: spacer_main}])
    return pd.concat([spacer_top_df, male_df, spacer_main_df, female_df, spacer_top_df], ignore_index=True)

outer_data = add_spacers(hom_male[['Sex', 'Race', 'homicide_norm']], hom_female[['Sex', 'Race', 'homicide_norm']], 'homicide_norm')
inner_data = add_spacers(pop_male[['Sex', 'Race', 'pop_norm']], pop_female[['Sex', 'Race', 'pop_norm']], 'pop_norm')

outer_data['normalized'] = outer_data['homicide_norm'].fillna(0)
inner_data['normalized'] = inner_data['pop_norm'].fillna(0)

def assign_colors(df):
    return [(1, 1, 1) if row['Race'] == 'Spacer' else race_colors.get(row['Race'], (0.8, 0.8, 0.8)) for _, row in df.iterrows()]

colors_outer = assign_colors(outer_data)
colors_inner = assign_colors(inner_data)

fig, ax = plt.subplots(figsize=(14, 10))

wedges_outer, _ = ax.pie(
    outer_data['normalized'],
    radius=1.0,
    startangle=90,
    counterclock=True,
    colors=colors_outer,
    wedgeprops=dict(width=0.25, edgecolor='white')
)

wedges_inner, _ = ax.pie(
    inner_data['normalized'],
    radius=0.7,
    startangle=90,
    counterclock=True,
    colors=colors_inner,
    wedgeprops=dict(width=0.25, edgecolor='white')
)

label_threshold = 1.0

label_offsets = {
    'Hispanic': 1.8,
    'Asian': 1.7,
    'Other / Unknown': 1.65,
    'Indigenous/ Pacific Islander': 1.65,
    'White': 1.4,
    'Black': 1.4
}

for i, wedge in enumerate(wedges_outer):
    label_info = outer_data.iloc[i]
    race = label_info['Race']
    if label_info['Sex'] == 'Spacer' or label_info['normalized'] < label_threshold:
        continue

    ang = (wedge.theta2 + wedge.theta1) / 2
    x = np.cos(np.deg2rad(ang))
    y = np.sin(np.deg2rad(ang))
    ha = 'left' if x > 0 else 'right'

    offset = label_offsets.get(race, 1.5)

    label_text = f"{label_info['Sex'][0]}-{short_label(race)}\n{label_info['normalized']:.1f}%"
    ax.annotate(
        label_text,
        xy=(x * 1.1, y * 1.1),
        xytext=(x * offset, y * offset),
        ha=ha,
        va='center',
        fontsize=12,
        arrowprops=dict(arrowstyle='-', color='gray'),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="gray", alpha=0.7)
    )

legend_patches = [
    Patch(color=race_colors[r], label=f"{short_label(r)}: {p:.1f}%")
    for r, p in zip(fl_population_pct['Race'], fl_population_pct['population_percentage'])
]

ax.legend(
    handles=legend_patches,
    loc='center left',
    bbox_to_anchor=(-0.3, 0.5),
    title="Florida Population by Race"
)

ax.set(aspect='equal')
ax.axis('off')


plt.tight_layout()

# Save donut chart to plots folder
donut_path = os.path.join(output_dir, "donut_sex_race.png")
fig.savefig(donut_path, dpi=300, bbox_inches='tight')
plt.close(fig)

# --------------------- NEW FUNCTION: PLOT SENTENCE RATE BY SEX + RACE WITH LABELS --------------------
def plot_sentence_rate_by_sex_race(df, sentence_type_filter, filename):
    df = df[df['Race'].notna()].copy()

    if 'sentence_type' in df.columns:
        df['sentence_type'] = df['sentence_type'].str.lower()
    else:
        raise ValueError("DataFrame missing 'sentence_type' column")

    df_sent = df[df['sentence_type'] == sentence_type_filter.lower()]

    total_by_group = df.groupby(['Sex', 'Race'])['DCNumber'].nunique().reset_index(name='total_count')
    sent_by_group = df_sent.groupby(['Sex', 'Race'])['DCNumber'].nunique().reset_index(name='sent_count')

    merged_counts = pd.merge(total_by_group, sent_by_group, on=['Sex', 'Race'], how='left').fillna(0)
    merged_counts['sentence_rate_pct'] = 100 * merged_counts['sent_count'] / merged_counts['total_count']

    merged_counts['Race'] = pd.Categorical(merged_counts['Race'], categories=race_order, ordered=True)
    merged_counts = merged_counts.sort_values(['Race', 'Sex'])
    merged_counts['Race_Label'] = merged_counts['Race'].map(short_label)

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=merged_counts,
        x='Race_Label',
        y='sentence_rate_pct',
        hue='Sex',
        palette={'Male': '#90ee90', 'Female': '#C21E56'}
    )

    plt.ylabel("Percentage of Homicide Convictions Receiving Sentence")
    plt.xlabel("Race")
    plt.ylim(0, max(10, merged_counts['sentence_rate_pct'].max() * 1.2))

    for p in ax.patches:
        height = p.get_height()
        if np.isnan(height) or height == 0:
            continue
        ax.text(
            p.get_x() + p.get_width() / 2,
            height + 0.3,
            f'{height:.1f}%',
            ha='center',
            va='bottom',
            fontsize=11,
            fontweight='bold'
        )

    ax.legend(title='Sex')
    plt.tight_layout()

    # Save barplot to plots folder
    save_path = os.path.join(output_dir, filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

# ---------------------- CALL THE FUNCTIONS TO PLOT ----------------------
plot_sentence_rate_by_sex_race(
    df_unique_all,
    sentence_type_filter='life sentence',
    filename="life_rate_sex_race.png"
)

plot_sentence_rate_by_sex_race(
    df_unique_all,
    sentence_type_filter='death sentence',
    filename="death_rate_sex_race.png"
)
