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

def clean_data(data):
    """
    This function takes a list of scraped items (dictionaries) and
    applies cleaning logic to each one.
    """
    cleaned_data = []
    
    # Loop through every item (clinic) in the list
    for item in data:
        # --- Task 1: Clean and Standardize Phone Numbers ---
        cleaned_phone = None
        if item.get('detailed_phone'):
            phone_number = item['detailed_phone']
            # This strips out anything that is not a digit.
            cleaned_phone = re.sub(r'\D', '', phone_number)
        
        # --- Task 2: Infer Country ---
        inferred_country = None
        if item.get('detailed_address'):
            address_string = item['detailed_address']
            
            # We create a list of countries to look for in the address string.
            known_countries = [
                'United States', 'USA', 'United Kingdom', 'UK', 'Canada', 
                'Australia', 'Germany', 'France', 'Spain', 'Italy', 'Ukraine',
                'Mexico', 'Brazil', 'India', 'Thailand', 'Turkey'
                # You can add more countries to this list as you scrape new sites
            ]
            
            for country in known_countries:
                # We use a case-insensitive search to find the country name
                if re.search(r'\b' + re.escape(country) + r'\b', address_string, re.IGNORECASE):
                    # Standardize the name (e.g., "USA" becomes "United States")
                    if country in ['USA', 'United States']:
                        inferred_country = 'United States'
                    elif country in ['UK', 'United Kingdom']:
                        inferred_country = 'United Kingdom'
                    else:
                        inferred_country = country
                    break # Stop searching once we've found a country

        # --- Task 3: Build the final, filtered dictionary ---
        # Create a new dictionary containing only the fields we want.
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
    Main function to run the data cleaning process.
    """
    try:
        # Open the raw JSON file and load the data into a Python list
        with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
            print(f"Reading data from '{INPUT_FILENAME}'...")
            raw_data = json.load(f)
        
        print(f"Successfully loaded {len(raw_data)} records.")

        # Run the cleaning function on the loaded data
        print("Cleaning data...")
        processed_data = clean_data(raw_data)
        print("Cleaning complete.")

        # Open the new output file and save the cleaned data
        # 'indent=4' makes the new JSON file nicely formatted and easy to read
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            print(f"Saving cleaned data to '{OUTPUT_FILENAME}'...")
            json.dump(processed_data, f, indent=4)
        
        print("Process finished successfully!")

    except FileNotFoundError:
        print(f"ERROR: The file '{INPUT_FILENAME}' was not found.")
        print("Please make sure the script and the JSON file are in the same folder.")
    except json.JSONDecodeError:
        print(f"ERROR: Could not read the data from '{INPUT_FILENAME}'. It might not be a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# This makes the script runnable from the command line
if __name__ == '__main__':
    main()
