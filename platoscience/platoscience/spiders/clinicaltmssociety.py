import scrapy
import json
import re

class ClinicaltmssocietySpider(scrapy.Spider):
    name = "clinicaltmssociety"
    allowed_domains = ["clinicaltmssociety.org"]
    
    # We start directly with the AJAX URL that returns the JSON data.
    start_urls = ["https://clinicaltmssociety.org/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=8324d87f17&load_all=1&layout=1"]

    def normalize_phone(self, phone_raw, country):
        """
        Cleans and standardizes a phone number based on its country.
        """
        if not phone_raw:
            return None

        # First, remove all non-digit characters from the phone number string.
        digits = re.sub(r'\D', '', phone_raw)

        # Handle US phone numbers, which can be 10 or 11 digits (with country code).
        if country == 'United States':
            if len(digits) == 10:
                # This is a standard 10-digit US number, so we add the +1.
                return f"+1{digits}"
            elif len(digits) == 11 and digits.startswith('1'):
                # This is an 11-digit number that already includes the 1, so we just add the +.
                return f"+{digits}"
        
        # For non-US numbers, if it's long, we assume it has a country code.
        if len(digits) > 10:
            return f"+{digits}"

        # Fallback for other formats (e.g., short local numbers in other countries).
        return digits

    def parse(self, response):
        """
        The main parsing method. 
        """
        self.log(f'Successfully fetched JSON data from: {response.url}')
        
        try:
            # Load the JSON response text into a Python list of dictionaries
            stores_data = json.loads(response.text)
        except json.JSONDecodeError as e:
            self.log(f"Error parsing JSON response: {e}")
            return

        # Loop through each store in the JSON data
        for store in stores_data:
            
            # Use our helper method to clean the phone number for each store
            phone_number = self.normalize_phone(store.get('phone'), store.get('country'))

            yield {
                'name': store.get('title'),
                'address': store.get('street'),
                'city': store.get('city'),
                'country': store.get('country'),
                'detailed_phone': phone_number,
                'email': store.get('email'),
                'website_link': store.get('website'),
            }
