import os
import subprocess
import json
import pandas as pd
# You would eventually import your database connection library here
# from sqlalchemy import create_engine

# A list of all your spider names
SPIDER_NAMES = [
    'brainsway',
    'clinicaltmssociety',
    'hirnstimulation',
    'magstim',
    'nexstim',
    'smarttms'
]

def run_spiders():
    """
    Executes all Scrapy spiders sequentially, creating a raw JSON file for each.
    """
    print("--- 1. Starting Spider Execution ---")
    output_files = []
    for spider_name in SPIDER_NAMES:
        output_file = f'output_{spider_name}_raw.json'
        # The command to run a spider and save its output
        command = [
            'scrapy', 'crawl', spider_name,
            '-o', output_file,
            '--nolog' # Optional: keeps the console output clean
        ]
        print(f"Running spider: {spider_name}...")
        subprocess.run(command, check=True)
        output_files.append(output_file)
    print("--- All spiders finished. ---\n")
    return output_files

def consolidate_data(file_paths):
    """
    Reads all raw JSON files and consolidates them into a single Pandas DataFrame.
    """
    print("--- 2. Consolidating Raw Data ---")
    all_data = []
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded {len(data)} records from {file_path}")
                all_data.extend(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not process {file_path}. Reason: {e}")
    
    print(f"--- Total raw records consolidated: {len(all_data)} ---\n")
    return pd.DataFrame(all_data)

def clean_and_transform(df):
    """
    Applies all data cleaning, normalization, and deduplication logic.
    This is where your "Data Janitor" logic lives.
    """
    print("--- 3. Cleaning and Transforming Data ---")
    
    # Example: Standardize country names (can be expanded)
    df['country'].replace({'USA': 'United States'}, inplace=True)

    # Example: Remove duplicates based on website or name/city
    df.drop_duplicates(subset=['website'], keep='first', inplace=True)

    # ... Here you would add phone formatting, address parsing, etc.
    
    print(f"--- Data cleaned. Final record count: {len(df)} ---\n")
    return df

def load_data(df):
    """
    Loads the final, cleaned DataFrame into its destination.
    For now, we save to a clean JSON. Later, this will load to a database.
    """
    print("--- 4. Loading Clean Data ---")
    clean_output_file = 'master_clinic_list_CLEANED.json'
    df.to_json(clean_output_file, orient='records', indent=4)
    print(f"🎉 Success! Clean data saved to '{clean_output_file}'")
    
    # --- DATABASE LOGIC (Future Step) ---
    # try:
    #     engine = create_engine('postgresql://user:password@host/dbname')
    #     df.to_sql('clinics', engine, if_exists='replace', index=False)
    #     print("🎉 Success! Data loaded into the 'clinics' database table.")
    # except Exception as e:
    #     print(f"Error loading data to database: {e}")

def main():
    """Orchestrates the entire ETL pipeline."""
    # Step 1
    //raw_file_paths = run_spiders()
    
    # Step 2
    consolidated_df = consolidate_data(raw_file_paths)
    
    # Step 3
    cleaned_df = clean_and_transform(consolidated_df)
    
    # Step 4
    load_data(cleaned_df)

if __name__ == '__main__':
    main()