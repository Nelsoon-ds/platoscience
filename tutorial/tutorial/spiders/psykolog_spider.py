import json

import scrapy


class PsychologistAPISpider(scrapy.Spider):
    name = 'psykolog'
    allowed_domains = ['psykologeridanmark.dk'] # Restrict the spider to this domain

    # The base API URL, without page-specific parameters
    base_api_url = 'https://psykologeridanmark.dk/wp-json/psykidk/v1/search'

    # Initial query parameters. You can adjust 'query' (e.g., to 'københavn' if needed,
    # but the URL already includes it) and other filters as desired.
    # The 'page' parameter will be incremented.
    initial_params = {
        'query': 'københavn', # 'k%C3%B8benhavn' is URL-encoded for 'københavn'
        'tilskud': 'false',
        'arbejds-og-organisationspsykolog': 'false',
        'autoriseret': 'false',
        'online_konsultation': 'false',
        'korestols_adgang': 'false',
        'hjemmebesoeg': 'false',
        'pageSize': '15', # You can adjust this if the API supports larger page sizes
        'page': '1'
    }

    def start_requests(self):
        # Build the URL for the first page
        first_page_url = f"{self.base_api_url}?{self.build_query_string(self.initial_params)}"
        yield scrapy.Request(url=first_page_url, callback=self.parse_api_response)

    def parse_api_response(self, response):
        try:
            data = json.loads(response.text)

            # Extract psychologist names from the 'result' array
            for psychologist in data.get('result', []):
                name = psychologist.get('Navn')
                if name:
                    # Yield a dictionary for each psychologist
                    yield {
                        'name': name,
                        'profile_id': psychologist.get('ProfilId'),
                        'specialist': psychologist.get('Specialist'),
                        'postcode_city': psychologist.get('Postnr_by'),
                        'workplace_name': psychologist.get('Navn_Arbejdssted'),
                        'mobile_phone': psychologist.get('MobilTlf'),
                        'website': psychologist.get('Hjemmeside'),
                        'email': psychologist.get('Email'),
                        'short_description': psychologist.get('Kort_praesentation'),
                        'recipients': psychologist.get('Modtager'),
                        'zip_code': psychologist.get('zip'),
                        'seo_id': psychologist.get('seo_id'),
                        'address': psychologist.get('Addresse'),
                        'subsidy': psychologist.get('Tilskud'),
                        'image_url': psychologist.get('Billede'),
                        'profile_url': psychologist.get('url'),
                    }

            # Check if there's a next page and send a request for it
            next_url = data.get('nextUrl')
            if next_url:
                self.logger.info(f"Fetching next page: {next_url}")
                yield scrapy.Request(url=next_url, callback=self.parse_api_response)
            else:
                self.logger.info("No more pages to fetch. All data scraped.")

        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from API response for {response.url}. Response content: {response.text[:500]}...")
        except Exception as e:
            self.logger.error(f"An error occurred while processing {response.url}: {e}")

    def build_query_string(self, params):
        """Helper to build a URL-encoded query string from a dictionary of parameters."""
        import urllib.parse
        return urllib.parse.urlencode(params)
