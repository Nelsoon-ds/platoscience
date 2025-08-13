import scrapy

class MagstimSpider(scrapy.Spider):
    """
    A Scrapy spider to extract clinic information from magstim.com/provider/.
    """
    name = 'magstim'
    
    # The starting URL for the spider.
    start_urls = ['https://magstim.com/provider/']

    def parse(self, response):
        """
        This method parses the provider page, extracting the name, address,
        and website for each clinic listed.
        """
        self.log("Starting to parse magstim.com/provider/")

        # Each clinic is contained within a <div class="place">
        for clinic in response.css('div.place'):
            # Extract the title/name of the clinic
            name = clinic.css('div.title::text').get()
            
            # Extract the address
            address = clinic.css('div.address::text').get()
            
            # Extract the website URL from the link
            website = clinic.css('div.link a::attr(href)').get()

            # Yield the extracted data as a dictionary.
            yield {
                'name': name.strip() if name else None,
                'address': address.strip() if address else None,
                'website': website,
                'country': 'USA'
            }

        self.log(f"Finished parsing. Found {len(response.css('div.place'))} clinics.")
