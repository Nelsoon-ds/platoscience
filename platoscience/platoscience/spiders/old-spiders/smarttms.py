import scrapy

class SmarttmsSpider(scrapy.Spider):
    name = "smarttms"
    allowed_domains = ["smarttms.co.uk"]
    start_urls = ["https://smarttms.co.uk/clinics/"]

    def parse(self, response):
        """
        The main parsing method. It finds all clinic containers on the page
        and delegates the extraction for each one to the parse_clinic method.
        """
        self.log(f'Successfully fetched: {response.url}')
        
        clinic_containers = response.css('div.location-listing')
        for clinic in clinic_containers:
            # Yield the structured data from each clinic container.
            yield self.parse_clinic(clinic, response.url)

    def parse_clinic(self, clinic, source_url):
        """
        Parses a single clinic container to extract its details.

        Args:
            clinic (scrapy.Selector): The selector for a single clinic's container div.
            source_url (str): The URL of the page where the clinic was found.

        Returns:
            dict: A dictionary containing the scraped data for one clinic.
        """
        name_raw = clinic.css('div.location-title-header::text').get()
        address_lines_raw = clinic.css('div.location-address-details::text').getall()
        phone_raw = clinic.css('div.location-address-details a::attr(href)').get()

        return {
            'name': name_raw.strip() if name_raw else None,
            'address': ' '.join(line.strip() for line in address_lines_raw if line.strip()),
            'detailed_phone': phone_raw.replace('tel:', '') if phone_raw else None,
            'source_url': source_url
        }
