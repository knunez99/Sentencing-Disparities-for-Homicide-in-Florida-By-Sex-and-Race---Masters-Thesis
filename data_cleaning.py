"""
Data Cleaning

"""

# --------------------------- IMPORT PACKAGES ---------------------------
import pandas as pd
import re
from collections import Counter
import numpy as np
# --------------------------- LOAD DATA ---------------------------
inmate_active = pd.read_csv('Inmate_Active.csv')
inmate_release = pd.read_csv('Inmate_Release.csv')

# ---------------------- FILTER FOR HOMICIDE CHARGES ----------------------
def filter_statute_homicide(df, column):
    keywords = [
        'MURDER',
        'MURD',
        'MANSLAUGHTER',
        'VEHICULAR',
        'ATTEMPTED FELONY MURDER',
        'FETAL HOMICIDE',
        'KILLING UNBORN', 
        'MUR',
        'HOMICIDE'
    ]
    pattern = '|'.join(keywords)
    return df[df[column].str.contains(pattern, case=False, na=False)]

inmate_active_filtered = filter_statute_homicide(inmate_active, 'adjudicationcharge_descr')
inmate_release_filtered = filter_statute_homicide(inmate_release, 'adjudicationcharge_descr')

# -------- REMOVE ALL ROWS WHERE MISSING VALUES LIKE RACE AND SEX --------
inmate_active_filtered = inmate_active_filtered.dropna(subset=['Race', 'Sex'])

inmate_release_filtered = inmate_release_filtered.dropna(subset=['Race', 'Sex'])

# -------------- PUT DATASETS TOGETHER ----------------------------
df = pd.concat([inmate_active_filtered, inmate_release_filtered], ignore_index=True)

del inmate_active_filtered
del inmate_release_filtered
del inmate_active
del inmate_release

# ---------------------- MAP DEMOGRAPHIC CODES ----------------------
race_map = {
    'W': 'White',
    'B': 'Black',
    'A': 'Asian',
    'H': 'Hispanic',
    'I': 'Indigenous / Pacific Islander',
    'U': 'Other / Unknown'
}

sex_map = {
    'M': 'Male',
    'F': 'Female'
}

for df in [df]:
    df['Race'] = df['Race'].map(race_map)
    df['Sex'] = df['Sex'].map(sex_map)
    
# ---------------------- CATEGORIZE CHARGE TYPES ----------------------
unique = df['adjudicationcharge_descr'].unique()
unique_release = df['adjudicationcharge_descr'].unique()

print("\n Unique Charges After Filtering:")
print(unique)


def categorize_charge(text):
    text = text.strip()

    charge_categories = {
        '1ST DG MUR/PREMED. OR ATT.': 'FIRST_DEGREE_MURDER',
        '2ND DEG.MURD,DANGEROUS ACT': 'SECOND_DEGREE_MURDER',
        'HOMICIDE,MANSL.CUL.NEGLI': 'NEGLIGENT_MANSLAUGHTER',
        'a-s, murder o/t 782.04(4) a-s': 'THIRD_DEGREE_MURDER',
        '1ST DEG MUR,COM.OF FELONY': 'FIRST_DEGREE_MURDER',
        'AT.FLNY.MURD/782.04(3) OFF.': 'ATTEMPTED_MURDER',
        'AT.FLNY.MURD/NOT 782.04(3)': 'ATTEMPTED_MURDER',
        'SECOND DEG.MURDER,COMM.OF FELO': 'SECOND_DEGREE_MURDER',
        'DUI MANSLAUGHTER': 'DUI_BUI_MANSLAUGHTER',
        'HOMICIDE-NEGLIG MANSL-VEH': 'VEHICULAR_MANSLAUGHTER',
        'DUI,MANSLAUGHTER': 'DUI_BUI_MANSLAUGHTER',
        'HOMICIDE NEGLIG MANSL VEH': 'VEHICULAR_MANSLAUGHTER',
        '1ST DEG MUR,DEATH FRM DRUGS': 'GENERAL_HOMICIDE',
        'ATTEMPT MURDER LAW ENFORCE OFF': 'ATTEMPTED_MURDER',
        "HOMICIDE,MANSL.UNNC.KILL'G": 'GENERAL_MANSLAUGHTER',
        'HOMICIDE-OTHER/OTHER STATE': 'GENERAL_HOMICIDE',
        'HOMICIDE-WLFL KILL-NONFMLY-GUN': 'GUN_RELATED_HOMICIDE',
        'HOMICIDE,KILL UNBORN CHLD': 'FETAL_HOMICIDE',
        'MANSLAUGHTER/UNBORN CHILD': 'FETAL_HOMICIDE',
        'BUI MANSLAUGHTER': 'DUI_BUI_MANSLAUGHTER',
        'FELONY MURDER-NONSEX': 'GENERAL_HOMICIDE',
        'HOMICIDE,MANSL.ASST.SELF-MUR': 'GENERAL_HOMICIDE',
        'AT.FLNY.MURD LEO/NOT 782.04(3)': 'LAW_ENFORCEMENT_KILL',
        'HOMICIDE-WILFUL W/VESSEL': 'VEHICULAR_MANSLAUGHTER',
        '2ND DG.MURDER/UNBORN CHILD': 'FETAL_HOMICIDE',
        '1ST DG.MURDER/UNBORN CHILD': 'FETAL_HOMICIDE',
        '2ND DEG ATT MUR/V - LEO': 'ATTEMPTED_MURDER',
        '1ST DEG ATT MUR/V - LEO': 'ATTEMPTED_MURDER',
        '2nd DEG, DA MUR/V - LEO': 'SECOND_DEGREE_MURDER',
        '1st DEG MUR/V - LEO': 'FIRST_DEGREE_MURDER',
        'AT.FLNY.MURD LEO/782.04(3) OFF': 'ATTEMPTED_MURDER',
        'HOMICIDE': 'GENERAL_HOMICIDE'
    }
    return charge_categories.get(text, 'OTHER')

df['charge'] = df['adjudicationcharge_descr'].apply(categorize_charge)

unique = df['charge'].unique()
unique_release = df['charge'].unique()

#------------------------------ CREATING SENTENCE TYPE ----------------------
life_death_conditions = [
    df['prisonterm'] == 9999999,
    df['prisonterm'] == 9999998
]

choices = ['death sentence', 'life sentence']

df['sentence_type'] = np.select(life_death_conditions, choices, default='fixed sentence')

#----------- FIND AND CORRECT BETWEEN FIRST DEGREE MURDER AND ATTEMPTED MURDER ----------------
df.loc[
    (df['sentence_type'] == 'fixed sentence') & 
    (df['adjudicationcharge_descr'] == '1ST DG MUR/PREMED. OR ATT.'), 
    'charge'
] = 'ATTEMPTED_MURDER'

#-------------------------- DROP UNNECCESSARY COLUMNS------------------
df.drop(['MiddleName', 'NameSuffix', 'PrisonReleaseDate', 'ReceiptDate', 'releasedateflag_descr', 'race_descr', 'FACILITY_description', 'Authority', 'DetainerDate', 'DetainerType', 'RemovalDate', 'detainertype_descr', 'ReleaseDate', 'adjudication_descr'], axis=1, inplace=True)

#---------------------------CHANGE COUNTY NAME--------------------------
df.rename(columns={'County_of_Conviction': 'county'}, inplace=True)

# ---------------------- CALCULATE AGE AT EVENT ----------------------
def calculate_age_at_event(birth_date, event_date):
    if pd.isnull(birth_date) or pd.isnull(event_date):
        return None
    return (event_date - birth_date).days // 365

for df in [df]:
    for col in ['BirthDate', 'OffenseDate', 'DateAdjudicated']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    df['age_at_offense'] = df.apply(
        lambda row: calculate_age_at_event(row['BirthDate'], row['OffenseDate']), axis=1
    )
    df['is_minor_at_offense'] = df['age_at_offense'].apply(
        lambda x: True if pd.notnull(x) and x < 18 else False
    )

# ---------------------- DETERMINE SENTENCING SYSTEM ----------------------
def categorize_point_system(offense_date):
    if pd.isna(offense_date):
        return 'Unknown'
    elif offense_date < pd.Timestamp('1983-10-01'):
        return 'Unstructured Sentencing'
    elif offense_date < pd.Timestamp('1994-01-01'):
        return '1983 Florida Sentencing Guidelines'
    elif offense_date < pd.Timestamp('1995-10-01'):
        return '1994 Florida Sentencing Guidelines'
    elif offense_date < pd.Timestamp('1998-10-01'):
        return '1995 Florida Sentencing Guidelines'
    else:
        return 'Criminal Punishment Code'

for df in [df]:
    df['Sentence_System'] = df['OffenseDate'].apply(categorize_point_system)
    
# ---------------------- DELETING MORE UNNECCESSARY COLUMNS --------------
df.drop(['BirthDate', 'Sequence', 'SequenceNo'], axis=1, inplace=True)

# ---------------------- CONVERT SENTENCE TERMS TO YEARS -------------------
def convert_term_to_years(prisonterm):
    try:
        term_str = str(int(prisonterm)).zfill(7)

        if term_str == "9999998" or term_str == "9999999":
            return np.nan

        years = int(term_str[:3])
        months = int(term_str[3:5])
        days = int(term_str[5:])

        # Convert total sentence length to years
        total_years = years + months / 12 + days / 365.25
        return total_years
    except (ValueError, TypeError):
        return np.nan  

df['sentence_years'] = df['prisonterm'].apply(convert_term_to_years)

#------------------------ DELETE ALL ROWS WITH MISSING SENTENCE AND ARE FIXED ------
df = df[~((df['sentence_type'] == 'fixed sentence') & (df['sentence_years'].isna()))]

# --------------------------------- DELETE MORE UNNECCESSARY ROWS--------------
df.drop(['prisonterm'], axis=1, inplace=True)

# ------------------------------ CREATE DATAFRAMES ------------------------
df_fixed = df[df['sentence_type'] == 'fixed sentence'].copy()
df_death = df[df['sentence_type'] == 'death sentence'].copy()
df_life = df[df['sentence_type'] == 'life sentence'].copy()

#--------------------------- CREATE CSV FROM DATAFRAMES----------------
df_fixed.to_csv('fixed_cases.csv', index=False)
df_death.to_csv('death_cases.csv', index=False)
df_life.to_csv('life_cases.csv', index=False)
df.to_csv('all_cases.csv', index=False)










