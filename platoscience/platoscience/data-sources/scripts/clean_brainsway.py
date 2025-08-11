import json
import re
import os

# Get the absolute path of the directory where this script is located.
# __file__ is a special variable that holds the path to the current script.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the full, absolute paths for the input and output files.
# This ensures the script always looks for 'brainsway.json' in its own folder.
INPUT_FILENAME = os.path.join(SCRIPT_DIR, 'brainsway.json')
OUTPUT_FILENAME = os.path.join(SCRIPT_DIR, 'brainsway_cleaned.json')

# --- CONFIGURATION CONSTANTS ---
# Best Practice: Define lists and dictionaries that don't change as module-level constants.
# This makes them easy to find and modify.
KNOWN_COUNTRIES = [
    'United States', 'USA', 'United Kingdom', 'UK', 'Canada', 
    'Australia', 'Germany', 'France', 'Spain', 'Italy', 'Ukraine',
    'Mexico', 'Brazil', 'India', 'Thailand', 'Turkey'
    # You can add more countries to this list as you scrape new sites
]

# Best Practice: Use a dictionary for mappings. It's cleaner and more scalable
# than long if/elif/else chains.
COUNTRY_ALIASES = {
    'USA': 'United States',
    'UK': 'United Kingdom'
}


def clean_data(data):
    """
    This function takes a list of scraped items (dictionaries) and
    applies cleaning and standardization logic to each one.
    """
    cleaned_data = []
    
    # Loop through every item (clinic) in the list
    for item in data:
        # --- Task 1: Clean and Standardize Phone Numbers ---
        # Use .get() to safely access the key, providing None if it's missing.
        phone_number = item.get('detailed_phone')
        cleaned_phone = re.sub(r'\D', '', phone_number) if phone_number else None
        
        # --- Task 2: Infer Country ---
        inferred_country = None
        address_string = item.get('detailed_address')
        if address_string:
            for country in KNOWN_COUNTRIES:
                # Use a case-insensitive, whole-word search to find the country name.
                if re.search(r'\b' + re.escape(country) + r'\b', address_string, re.IGNORECASE):
                    # Standardize the name using the alias dictionary.
                    # .get(country, country) returns the standardized name if it's an alias,
                    # or the original country name if it's not.
                    inferred_country = COUNTRY_ALIASES.get(country, country)
                    break # Stop searching once we've found a country

        # --- Task 3: Build the final, filtered dictionary ---
        # Create a new dictionary containing only the fields we want to keep.
        final_item = {
            'source_url': item.get('source_url'),
            'name': item.get('name'),
            'phone': cleaned_phone,
            'website_link': item.get('website_link'),
            'country': inferred_country
        }

        cleaned_data.append(final_item)
        
    return cleaned_data

def main():
    """
    Main function to orchestrate the data cleaning process.
    """
    try:
        # Open the raw JSON file and load the data into a Python list
        with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
            print(f"Reading data from '{INPUT_FILENAME}'...")
            raw_data = json.load(f)
        
        # Robustness: Check if the loaded data is a list.
        if not isinstance(raw_data, list):
            print(f"ERROR: Expected a list of items in '{INPUT_FILENAME}', but found {type(raw_data)}.")
            return

        print(f"Successfully loaded {len(raw_data)} records.")

        # Run the cleaning function on the loaded data
        print("Cleaning data...")
        processed_data = clean_data(raw_data)
        print("Cleaning complete.")

        # Open the new output file and save the cleaned data.
        # 'indent=4' makes the new JSON file nicely formatted and easy to read.
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            print(f"Saving cleaned data to '{OUTPUT_FILENAME}'...")
            json.dump(processed_data, f, indent=4)
        
        print("Process finished successfully!")

    except FileNotFoundError:
        print(f"ERROR: The input file '{INPUT_FILENAME}' was not found.")
        print("Please ensure the script and the JSON file are in the same directory.")
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from '{INPUT_FILENAME}'. The file may be empty or contain invalid JSON.")
    except Exception as e:
        # Catch-all for any other unexpected errors.
        print(f"An unexpected error occurred: {e}")

# This standard Python construct makes the script runnable from the command line.
if __name__ == '__main__':
    main()