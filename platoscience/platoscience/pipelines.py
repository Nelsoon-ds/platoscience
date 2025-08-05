# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re

class PlatosciencePipeline:
    def process_item(self, item, spider):
        return item

class DataCleaningPipeline:
    """
    This pipeline takes the scraped item and cleans the data before it gets saved.
    """

    def process_item(self, item, spider):
        """
        This method is called for every single item that the spider yields.
        'item' is the dictionary of data we scraped (name, address, phone, etc.).
        'spider' is the spider that scraped it.
        """

        # --- Task 1: Clean and Standardize Phone Numbers ---
        if item.get('detailed_phone'):
            phone_number = item['detailed_phone']
            # This strips out anything that is not a digit.
            cleaned_number = re.sub(r'\D', '', phone_number)
            item['detailed_phone'] = cleaned_number

        # --- Task 2: Parse the Address String (Improved Logic) ---
        if item.get('detailed_address'):
            # First, clean up common trailing text like country names
            address_string = item['detailed_address'].replace(' United States', '').replace(' Country', '').strip()
            
            # Initialize new address fields to None to ensure they always exist
            item['street'] = None
            item['city'] = None
            item['state'] = None
            item['zip_code'] = None

            # This regex finds the state and zip code at the end of the string
            match = re.search(r'^(.*),\s*([A-Z]{2})\s*(\d{5})$', address_string)
            
            if match:
                # The first group contains the street and city combined.
                street_and_city_part = match.group(1).strip()
                item['state'] = match.group(2).strip()
                item['zip_code'] = match.group(3).strip()
                
                # --- New, smarter logic to separate street from city ---
                parts = street_and_city_part.split(' ')
                city_parts = []
                street_parts = []
                
                # We work backwards from the end of the string.
                # The city is usually the last few words that don't contain numbers.
                # Once we find a part with a number (like a street number or suite #),
                # we know that part and everything before it belongs to the street.
                found_street_part = False
                for part in reversed(parts):
                    if not found_street_part and not any(char.isdigit() for char in part):
                        # If we haven't found the street yet and this part is just letters,
                        # it's probably part of the city name.
                        city_parts.insert(0, part)
                    else:
                        # We found a number or we've already found the whole city.
                        # This part belongs to the street.
                        found_street_part = True
                        street_parts.insert(0, part)

                item['street'] = ' '.join(street_parts)
                item['city'] = ' '.join(city_parts)

        # After we're done cleaning, we MUST return the item.
        return item

