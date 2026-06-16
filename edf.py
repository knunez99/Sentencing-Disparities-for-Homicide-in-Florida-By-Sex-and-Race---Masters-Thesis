# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 03:52:25 2025

@author: M1
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
df_fixed = pd.read_sql_query("SELECT * FROM fixed_cases;", conn)
conn.close()

df_cpc_fixed = df_fixed[df_fixed['Sentence_System'] == 'Criminal Punishment Code'].copy()
df_unique_fixed = df_cpc_fixed.sort_values('sentence_years', ascending=False).drop_duplicates(subset='DCNumber')

# --------------------- COLOR PALETTES ---------------------
sex_palette = {'Male': '#90ee90', 'Female': '#C21E56'}
race_palette = {'White': 'tab:blue', 'Black': 'tab:orange', 'Hispanic': 'tab:green'}

# --------------------- EDF: All Individuals ---------------------
plt.figure(figsize=(10, 6))
sns.ecdfplot(data=df_unique_fixed, x='sentence_years')
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_all.png"), dpi=300)
plt.close()

# --------------------- EDF: Male vs Female ---------------------
plt.figure(figsize=(8, 5))
sns.ecdfplot(data=df_unique_fixed, x='sentence_years', hue='Sex', palette=sex_palette)
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_sex.png"), dpi=300)
plt.close()

# --------------------- EDF: White vs Black vs Hispanic ---------------------
df_race3 = df_unique_fixed[df_unique_fixed['Race'].isin(['White', 'Black', 'Hispanic'])]

plt.figure(figsize=(8, 5))
sns.ecdfplot(data=df_race3, x='sentence_years', hue='Race', palette=race_palette)
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_race.png"), dpi=300)
plt.close()

# --------------------- EDF: Black Males vs White Males vs Hispanic Males ---------------------
df_males = df_unique_fixed[df_unique_fixed['Sex'] == 'Male']
df_males_race3 = df_males[df_males['Race'].isin(['White', 'Black', 'Hispanic'])]

plt.figure(figsize=(8, 5))
sns.ecdfplot(data=df_males_race3, x='sentence_years', hue='Race', palette=race_palette)
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_race_men.png"), dpi=300)
plt.close()

# --------------------- EDF: White Females vs Black Females vs Hispanic Females ---------------------
df_females = df_unique_fixed[df_unique_fixed['Sex'] == 'Female']
df_females_race3 = df_females[df_females['Race'].isin(['White', 'Black', 'Hispanic'])]

plt.figure(figsize=(8, 5))
sns.ecdfplot(data=df_females_race3, x='sentence_years', hue='Race', palette=race_palette)
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_race_women.png"), dpi=300)
plt.close()

# --------------------- EDF: Black Males vs Black Females ---------------------
df_black = df_unique_fixed[df_unique_fixed['Race'] == 'Black']

plt.figure(figsize=(8, 5))
sns.ecdfplot(data=df_black, x='sentence_years', hue='Sex', palette=sex_palette)
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_sex_black.png"), dpi=300)
plt.close()

# --------------------- EDF: White Males vs White Females ---------------------
df_white = df_unique_fixed[df_unique_fixed['Race'] == 'White']

plt.figure(figsize=(8, 5))
sns.ecdfplot(data=df_white, x='sentence_years', hue='Sex', palette=sex_palette)
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_sex_white.png"), dpi=300)
plt.close()

# --------------------- EDF: Hispanic Males vs Hispanic Females ---------------------
df_hispanic = df_unique_fixed[df_unique_fixed['Race'] == 'Hispanic']

plt.figure(figsize=(8, 5))
sns.ecdfplot(data=df_hispanic, x='sentence_years', hue='Sex', palette=sex_palette)
plt.xlabel('Sentence Length (years)')
plt.ylabel('Cumulative Probability')
plt.xscale('log')
plt.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "edf_sex_hispanic.png"), dpi=300)
plt.close()
