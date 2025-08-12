# pipelines.py - Updated to work with your existing items.py

import re
from itemadapter import ItemAdapter


class PlatosciencePipeline:
    """A default placeholder pipeline."""

    def process_item(self, item, spider):
        return item


class DataCleaningPipeline:
    """
    Enhanced pipeline for cleaning Psychology Today scraped data.
    Works with the field names defined in your items.py ProviderItem.
    """

    def process_item(self, item, spider):
        """
        This method is called for every item yielded by a spider.
        It must return an item object or raise a DropItem exception.
        """
        adapter = ItemAdapter(item)

        # --- Task 1: Clean and Standardize Phone Numbers ---
        phone_number = adapter.get('phone')
        if phone_number:
            # Extract digits and format properly
            cleaned_number = re.sub(r'\D', '', str(phone_number))
            if len(cleaned_number) >= 10:
                if len(cleaned_number) == 10:
                    formatted_phone = f"({cleaned_number[:3]}) {cleaned_number[3:6]}-{cleaned_number[6:]}"
                elif len(cleaned_number) == 11 and cleaned_number[0] == '1':
                    # Remove leading 1 for US numbers
                    formatted_phone = f"({cleaned_number[1:4]}) {cleaned_number[4:7]}-{cleaned_number[7:]}"
                else:
                    # Take last 10 digits
                    last_10 = cleaned_number[-10:]
                    formatted_phone = f"({last_10[:3]}) {last_10[3:6]}-{last_10[6:]}"
                adapter['phone'] = formatted_phone
            else:
                # Keep as is if less than 10 digits
                adapter['phone'] = cleaned_number

        # --- Task 2: Parse Address String into Components ---
        address_string = adapter.get('address')
        # Only parse if city not already set
        if address_string and not adapter.get('city'):
            # Initialize address component fields
            adapter['city'] = None
            adapter['state'] = None
            adapter['zipcode'] = None

            # Clean the address string first
            address_string = str(address_string).strip()

            # Try multiple regex patterns for US addresses
            patterns = [
                # Pattern 1: "123 Main St, Suite 100, Anchorage, AK 99503"
                r'^(.*?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$',
                # Pattern 2: "123 Main St, Anchorage, AK 99503"
                r'^(.*?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$',
                # Pattern 3: "123 Main St Anchorage AK 99503" (no commas)
                r'^(.*?)\s+([A-Za-z\s]+)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$'
            ]

            parsed = False
            for pattern in patterns:
                match = re.search(pattern, address_string)
                if match:
                    if len(match.groups()) == 4:  # Street, City, State, Zip
                        street_part = match.group(1).strip()
                        city_part = match.group(2).strip()
                        state_part = match.group(3).strip()
                        zip_part = match.group(4).strip()

                        # Handle cases where street might contain suite/unit info
                        adapter['address'] = street_part
                        adapter['city'] = city_part
                        adapter['state'] = state_part.upper()
                        adapter['zipcode'] = zip_part
                        parsed = True
                        break

            # If no pattern matched, try a simpler approach
            if not parsed:
                # Look for state abbreviation and zip at the end
                state_zip_match = re.search(
                    r'\b([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\s*$', address_string)
                if state_zip_match:
                    state = state_zip_match.group(1)
                    zipcode = state_zip_match.group(2)
                    # Everything before state/zip
                    before_state_zip = address_string[:state_zip_match.start()].strip(
                    )

                    # Try to split the remaining part into street and city
                    parts = before_state_zip.split(',')
                    if len(parts) >= 2:
                        street = ','.join(parts[:-1]).strip()
                        city = parts[-1].strip()
                    else:
                        # Last resort: assume last word(s) before state is city
                        words = before_state_zip.split()
                        if len(words) > 2:
                            street = ' '.join(words[:-2])
                            city = ' '.join(words[-2:])
                        else:
                            street = before_state_zip
                            city = ""

                    adapter['address'] = street
                    adapter['city'] = city
                    adapter['state'] = state
                    adapter['zipcode'] = zipcode

        # --- Task 3: Clean Email Addresses ---
        email = adapter.get('email')
        if email:
            email_str = str(email).strip().lower()
            # Validate email format
            email_match = re.search(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', email_str)
            if email_match:
                adapter['email'] = email_match.group()
            else:
                adapter['email'] = None  # Invalid email

        # --- Task 5: Clean Tags Field ---
        tags = adapter.get('tags')
        if tags:
            if isinstance(tags, str):
                # Split by comma and clean each tag
                tag_list = [tag.strip()
                            for tag in tags.split(',') if tag.strip()]
                # Remove duplicates and sort
                adapter['tags'] = ', '.join(sorted(set(tag_list)))
            elif isinstance(tags, list):
                # Clean list of tags
                clean_tags = [str(tag).strip()
                              for tag in tags if str(tag).strip()]
                adapter['tags'] = ', '.join(sorted(set(clean_tags)))

        # --- Task 6: Validate and Clean Website Links ---
        website_link = adapter.get('website_link')
        if website_link:
            website_str = str(website_link).strip()
            if not website_str.startswith(('http://', 'https://')):
                if website_str.startswith('www.'):
                    adapter['website_link'] = f'https://{website_str}'
                elif '.' in website_str:
                    adapter['website_link'] = f'https://{website_str}'
            else:
                adapter['website_link'] = website_str
        return item
