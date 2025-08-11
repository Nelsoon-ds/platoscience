import json
import os
import re

# --- HELPER FUNCTIONS ---

def clean_phone_number(phone):
    """Removes non-numeric characters from a phone number string."""
    if not phone:
        return None
    # Ensures input is treated as a string before applying regex
    return re.sub(r'\D', '', str(phone))

def clean_email(email):
    """Cleans common issues from scraped email addresses."""
    if not email:
        return None
    # Standardize to lowercase, remove 'mailto:' prefix and any URL parameters
    cleaned = email.lower().strip().replace('mailto:', '').split('?')[0]
    # Basic regex to check for a valid-looking email format
    if re.fullmatch(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", cleaned):
        return cleaned
    return None

def normalize_url(url):
    """
    Normalizes a URL to a consistent format for accurate deduplication.
    Example: 'https://www.domain.com/path/' -> 'domain.com/path'
    """
    if not url or url == '#':
        return None
    # Remove protocol (http, https) and 'www.' prefix
    url = re.sub(r'^(https?://)?(www\.)?', '', url.lower())
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    return url

# --- CORE LOGIC ---

def process_files(file_paths):
    """
    Reads multiple JSON files, normalizes fields, cleans data,
    removes duplicates, and merges the results.
    """
    all_clinics = {} # Use a dictionary for more effective deduplication
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    print(f"Warning: Expected a list in {file_path}, but found {type(data)}. Skipping.")
                    continue
                
                print(f"Processing {len(data)} records from {os.path.basename(file_path)}...")
                for item in data:
                    # --- Normalize fields from various potential keys ---
                    name = item.get('name') or item.get('clinic_name') or item.get('title')
                    if not name:
                        continue # Skip records without a name

                    # --- Create a robust unique identifier for deduplication ---
                    # The combination of a clean name and a normalized URL is a strong unique key.
                    normalized_website = normalize_url(item.get('website') or item.get('website_link'))
                    unique_id = (name.strip().lower(), normalized_website)
                    
                    # If we've already seen this clinic, skip it.
                    if unique_id in all_clinics:
                        continue

                    # --- Clean and structure the data ---
                    all_clinics[unique_id] = {
                        'name': name.strip(),
                        'address': (item.get('address') or item.get('detailed_address') or '').strip() or 'N/A',
                        'city': (item.get('city') or '').strip() or 'N/A',
                        'country': (item.get('country') or '').strip() or 'N/A',
                        'phone': clean_phone_number(item.get('phone') or item.get('detailed_phone') or item.get('phone_number')),
                        'email': clean_email(item.get('email')),
                        'website': item.get('website') or item.get('website_link') or '#',
                        'source': os.path.basename(file_path)
                    }
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error: Could not read or parse {file_path}. Reason: {e}")

    # Return the values of the dictionary, which is our list of unique clinics
    return list(all_clinics.values())

# --- MAIN EXECUTION BLOCK ---

if __name__ == '__main__':
    # Best Practice: Construct paths relative to the script's location.
    # This ensures the script is portable and works on any machine.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_directory = os.path.join(script_dir, '..', 'raw-data') # Assumes 'raw-data' is a sibling to 'scripts'
    output_dir = os.path.join(script_dir, '..') # Save output file in the parent 'data-sources' directory
    output_filename = os.path.join(output_dir, 'master_clinic_list.json')
    
    # Check if the data directory exists to provide a better error message.
    if not os.path.isdir(data_directory):
        print(f"Error: The data directory was not found at the expected location:")
        print(f"'{data_directory}'")
        print("Please ensure your raw JSON files are in a 'raw-data' folder.")
    else:
        # Automatically find all .json files in the specified directory.
        files_to_process = [
            os.path.join(data_directory, f) 
            for f in os.listdir(data_directory) 
            if f.endswith('.json')
        ]
        
        if not files_to_process:
            print(f"No JSON files found in the directory: {data_directory}")
        else:
            print(f"Found {len(files_to_process)} JSON files to process...")
            master_list = process_files(files_to_process)

            # Save the clean, merged data to the output file.
            with open(output_filename, 'w', encoding='utf-8') as f:
                # ensure_ascii=False writes characters like 'ü' or 'é' directly,
                # which is better for readability.
                json.dump(master_list, f, indent=4, ensure_ascii=False)

            print("-" * 20)
            print(f"✅ Processing complete. Found {len(master_list)} unique clinics.")
            print(f"Master list saved to '{output_filename}'")