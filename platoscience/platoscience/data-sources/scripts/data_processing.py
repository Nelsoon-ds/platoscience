import json
import os
import re

def clean_phone_number(phone):
    """Removes non-numeric characters from a phone number."""
    if not phone:
        return None
    return re.sub(r'\D', '', str(phone))

def clean_email(email):
    """Cleans common issues from scraped email addresses."""
    if not email:
        return None
    # Remove mailto: prefix and any URL parameters
    email = email.lower().replace('mailto:', '').split('?')[0]
    # Simple regex to validate email format
    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return email
    return None

def process_files(file_paths):
    """
    Reads multiple JSON files, merges the data, cleans it,
    and removes duplicates.
    """
    all_clinics = []
    seen_clinics = set()

    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    # --- Normalize fields ---
                    # Different files might use different keys for the same data.
                    name = item.get('name') or item.get('clinic_name')
                    address = item.get('address') or item.get('detailed_address')
                    phone = item.get('phone_number') or item.get('detailed_phone')
                    email = item.get('email')
                    website = item.get('website') or item.get('website_link')
                    country = item.get('country')
                    city = item.get('city')
                    
                    if not name:
                        continue

                    # --- Clean data ---
                    cleaned_phone = clean_phone_number(phone)
                    cleaned_email = clean_email(email)
                    
                    # --- Create a unique identifier to spot duplicates ---
                    # A combination of name and website is a good unique key.
                    unique_id = (name.strip().lower(), website.strip().lower() if website else "")
                    
                    if unique_id not in seen_clinics:
                        all_clinics.append({
                            'name': name.strip(),
                            'address': address.strip() if address else 'N/A',
                            'city': city.strip() if city else 'N/A',
                            'country': country.strip() if country else 'N/A',
                            'phone': cleaned_phone,
                            'email': cleaned_email,
                            'website': website.strip() if website else '#',
                            'source': os.path.basename(file_path)
                        })
                        seen_clinics.add(unique_id)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Could not read or parse {file_path}: {e}")

    return all_clinics

if __name__ == '__main__':
    # Define the directory where your raw JSON files are stored.
    # Make sure to use the correct path for your system.
    data_directory = '/Users/davidolsen/Documents/repositories/Repositories/web-scraping/platoscience/platoscience/data-sources/raw-data'

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
        # Process the files
        master_list = process_files(files_to_process)

        # Save the clean, merged data to a new file in the parent directory
        output_filename = 'master_clinic_list-new.json'
        with open(output_filename, 'w', encoding='utf-8') as f:
            # ensure_ascii=False will write the characters directly instead of escaping them.
            json.dump(master_list, f, indent=4, ensure_ascii=False)

        print(f"Processing complete. Found {len(master_list)} unique clinics.")
        print(f"Master list saved to '{output_filename}'")
