# -*- coding: utf-8 -*-
"""
Title: Convert Excel Sheets to CSV Files

Goal:
I need to clean data from three Excel files, but first I have to convert them to CSV format.
Each file has multiple sheets, and each sheet should become its own CSV.

Files: 
- Inmate_Active.xlsx
- Inmate_Release.xlsx
- Offender.xlsx

What this script does:
- Looks for the above files in C:\Users\M1\Downloads
- Goes through every sheet in each file
- Cleans the sheet name (replaces spaces/slashes with underscores)
- Combines the Excel filename and sheet name to make a unique CSV filename
- Saves each CSV to C:\Users\M1\Documents\KANunez\Data

Why:
CSV files are easier to work with for cleaning and analysis in Python.
"""

import pandas as pd
import os

input_dir = r'C:\Users\M1\Downloads'
output_dir = r'C:\Users\M1\Documents\KANunez\Data'

os.makedirs(output_dir, exist_ok=True)

excel_files = [
    os.path.join(input_dir, 'Inmate_Active.xlsx'),
    os.path.join(input_dir, 'Inmate_Release.xlsx'),
    os.path.join(input_dir, 'Offender.xlsx')
]

for excel_file in excel_files:
    file_name = os.path.splitext(os.path.basename(excel_file))[0]
    print(f"Processing file: {file_name}")

    xls = pd.ExcelFile(excel_file)
    sheet_names = xls.sheet_names  

    for sheet in sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)

        safe_sheet_name = sheet.replace(" ", "_").replace("/", "_").replace("\\", "_").strip()

        csv_filename = f"{safe_sheet_name}.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        df.to_csv(csv_path, index=False)

        print(f"Saved: {csv_path}")
