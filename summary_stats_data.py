# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 03:14:40 2025

@author: M1
"""
import pandas as pd
import numpy as np
import sqlite3
import os

# ------------------------ SET SCRIPT CONTEXT ---------------------------
try:
    SCRIPT_DIR = os.path.dirname(__file__)
except NameError:
    SCRIPT_DIR = os.getcwd()

# ------------------------ SET PATHS ------------------------------------
# Path to database file
db_path = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data", "cases.db"))

# Path to output tables
output_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "tables"))
os.makedirs(output_dir, exist_ok=True)

# --------------------------- LOAD DATA ---------------------------
conn = sqlite3.connect(db_path)
df_fixed = pd.read_sql_query("SELECT * FROM fixed_cases;", conn)
conn.close()

# --------------------- FILTER TO ONLY POST-1998 CASES ---------------------
df_cpc_fixed = df_fixed[df_fixed['Sentence_System'] == 'Criminal Punishment Code'].copy()

# -------------------------- REMOVE DUPLICATES BY PERSON ------------------
df_unique_fixed = df_cpc_fixed.sort_values('sentence_years', ascending=False).drop_duplicates(subset='DCNumber')

# ------------------ CLEAN CHARGE NAMES FOR PRESENTATION ------------------
def prettify_charge(charge):
    if pd.isnull(charge):
        return charge
    return charge.replace('_', ' ').title()

df_unique_fixed['charge'] = df_unique_fixed['charge'].apply(prettify_charge)

# -------------------------- TOTAL UNIQUE INDIVIDUALS ---------------------
total_people = len(df_unique_fixed)

# ---------------------- FUNCTION: COMPUTE SUMMARY ------------------------
def compute_summary(df, groupby_cols):
    summary = df.groupby(groupby_cols).agg(
        count=('DCNumber', 'nunique'),
        average_sentence=('sentence_years', 'mean'),
        median_sentence=('sentence_years', 'median'),
        std_sentence=('sentence_years', 'std'),
        sem=('sentence_years', lambda x: x.std(ddof=1) / np.sqrt(len(x)))
    ).reset_index()

    summary['percentage'] = 100 * summary['count'] / total_people
    return summary[groupby_cols + [
        'count', 'percentage', 'average_sentence', 'median_sentence',
        'std_sentence', 'sem'
    ]]

# ---------------------- RENAME COLUMNS FOR PRESENTATION ------------------
def clean_columns(df):
    return df.rename(columns={
        'count': 'N',
        'percentage': '\\%',
        'average_sentence': 'Average Sentence',
        'median_sentence': 'Median Sentence',
        'std_sentence': 'Standard Deviation',
        'sem': 'Standard Error'
    })

# ------------------------ CALCULATE SUMMARIES ----------------------------
summary_sex = compute_summary(df_unique_fixed, ['Sex'])
summary_race = compute_summary(df_unique_fixed, ['Race'])
summary_sex_race = compute_summary(df_unique_fixed, ['Sex', 'Race'])
summary_sex_charge = compute_summary(df_unique_fixed, ['Sex', 'charge'])
summary_race_charge = compute_summary(df_unique_fixed, ['Race', 'charge'])
summary_race_charge_men = compute_summary(
    df_unique_fixed[df_unique_fixed['Sex'] == 'Male'], ['Race', 'charge']
)
summary_race_charge_women = compute_summary(
    df_unique_fixed[df_unique_fixed['Sex'] == 'Female'], ['Race', 'charge']
)

# ------------------------ SAVE TO LATEX FILES ----------------------------
clean_columns(summary_sex).to_latex(os.path.join(output_dir, 'summary_sex.tex'), index=False, float_format="%.2f")
clean_columns(summary_race).to_latex(os.path.join(output_dir, 'summary_race.tex'), index=False, float_format="%.2f")
clean_columns(summary_sex_race).to_latex(os.path.join(output_dir, 'summary_sex_race.tex'), index=False, float_format="%.2f")
clean_columns(summary_sex_charge).to_latex(os.path.join(output_dir, 'summary_sex_charge.tex'), index=False, float_format="%.2f")
clean_columns(summary_race_charge).to_latex(os.path.join(output_dir, 'summary_race_charge.tex'), index=False, float_format="%.2f")
clean_columns(summary_race_charge_men).to_latex(os.path.join(output_dir, 'summary_race_charge_men.tex'), index=False, float_format="%.2f")
clean_columns(summary_race_charge_women).to_latex(os.path.join(output_dir, 'summary_race_charge_women.tex'), index=False, float_format="%.2f")
