import os
import subprocess
import json
import pandas as pd
import re
# To load data into a database later, you would uncomment the following:
# from sqlalchemy import create_engine

# --- CONFIGURATION ---

# A list of all your spider names to be executed.
SPIDER_NAMES = [
    'brainsway',
    'clinicaltmssociety',
    'hirnstimulation',
    'magstim',
    'nexstim',
    'smarttms'
]
# Define a consistent output file for the final, clean data.
CLEAN_OUTPUT_FILE = 'master_clinic_list.json'


# --- EXTRACT (E) ---

def run_spiders():
    """
    Executes all Scrapy spiders sequentially using subprocess calls.
    Each spider saves its raw output to a separate JSON file.
    """
    print("--- 1. Starting Spider Execution ---")
    output_files = []
    # Assumes this script is run from the 'platoscience' project root directory.
    project_root = os.getcwd() 

    for spider_name in SPIDER_NAMES:
        # Define a consistent naming scheme for raw output files.
        output_file = os.path.join(project_root, f'output_{spider_name}_raw.json')
        command = [
            'scrapy', 'crawl', spider_name,
            '-o', output_file,
        ]
        print(f"Running spider: {spider_name}...")
        try:
            # check=True will raise an error if the spider fails.
            subprocess.run(command, check=True, capture_output=True, text=True)
            output_files.append(output_file)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Spider '{spider_name}' failed to run.")
            print(f"Stderr: {e.stderr}")
            # Decide whether to continue or stop. For now, we'll stop the pipeline.
            raise e
            
    print("--- All spiders finished successfully. ---\n")
    return output_files

# --- TRANSFORM (T) ---

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
                if data: # Ensure file is not empty
                    print(f"Loaded {len(data)} records from {os.path.basename(file_path)}")
                    all_data.extend(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not process {file_path}. Reason: {e}")
    
    if not all_data:
        print("Warning: No data was consolidated. Exiting.")
        return None

    print(f"--- Total raw records consolidated: {len(all_data)} ---\n")
    return pd.DataFrame(all_data)

def normalize_url(url):
    """Normalizes a URL for more accurate deduplication."""
    if pd.isna(url) or url == '#':
        return None
    url = re.sub(r'^(https?://)?(www\.)?', '', str(url).lower())
    return url.strip('/')

def clean_and_transform(df):
    """
    The central function for all data cleaning, normalization, and deduplication.
    This is where the main "Transform" logic lives.
    """
    print("--- 3. Cleaning and Transforming Data ---")
    
    # --- Field Normalization ---
    # Coalesce data from columns with different names into a single, standard column.
    df['name'] = df['name'].fillna(df['clinic_name']).fillna(df['title'])
    df['phone'] = df['phone'].fillna(df['detailed_phone']).fillna(df['phone_number'])
    df['website'] = df['website'].fillna(df['website_link'])
    df['address'] = df['address'].fillna(df['detailed_address'])
    
    # Drop records that are missing a name after coalescing.
    df.dropna(subset=['name'], inplace=True)
    
    # --- Data Cleaning ---
    df['phone'] = df['phone'].apply(lambda x: re.sub(r'\D', '', str(x)) if pd.notna(x) else None)
    df['name'] = df['name'].str.strip()
    
    # --- Deduplication ---
    # Create a normalized URL column specifically for finding duplicates.
    df['normalized_website'] = df['website'].apply(normalize_url)
    # A good unique key is a combination of name and a clean website URL.
    df.drop_duplicates(subset=['name', 'normalized_website'], keep='first', inplace=True)

    # --- Final Schema Selection ---
    # Select and rename columns to match our final desired output schema.
    final_df = df[[
        'name', 'address', 'city', 'country', 'phone', 'email', 'website', 'source_url'
    ]].copy() # Use .copy() to avoid SettingWithCopyWarning
    
    print(f"--- Data cleaned. Final unique record count: {len(final_df)} ---\n")
    return final_df

# --- LOAD (L) ---

def load_data(df):
    """
    Loads the final, cleaned DataFrame to its destination (e.g., a JSON file, database).
    """
    print("--- 4. Loading Clean Data ---")
    
    # Save to a clean JSON file
    df.to_json(CLEAN_OUTPUT_FILE, orient='records', indent=4)
    print(f"🎉 Success! Clean data saved to '{CLEAN_OUTPUT_FILE}'")
    
    # --- DATABASE LOGIC (Future-proofing) ---
    # When ready, you can uncomment this to load data into a SQL database.
    # try:
    #     engine = create_engine('postgresql://user:password@host/dbname')
    #     df.to_sql('clinics', engine, if_exists='replace', index=False)
    #     print("🎉 Success! Data loaded into the 'clinics' database table.")
    # except Exception as e:
    #     print(f"Error loading data to database: {e}")

# --- ORCHESTRATION ---

def main():
    """Orchestrates the entire ETL pipeline."""
    try:
        raw_file_paths = run_spiders()
        
        if not raw_file_paths:
            print("No spider output files were generated. Exiting.")
            return

        consolidated_df = consolidate_data(raw_file_paths)
        
        if consolidated_df is None or consolidated_df.empty:
            print("No data to process after consolidation. Exiting.")
            return
            
        cleaned_df = clean_and_transform(consolidated_df)
        load_data(cleaned_df)
        
    except Exception as e:
        print(f"\n--- PIPELINE FAILED ---")
        print(f"An error occurred: {e}")
        # Clean up raw files if the pipeline fails (optional)
        # for f in raw_file_paths: os.remove(f)

if __name__ == '__main__':
    main()