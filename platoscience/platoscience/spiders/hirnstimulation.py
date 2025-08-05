import scrapy
import re

class ClinicSpider(scrapy.Spider):
    """
    A Scrapy spider to extract clinic information from dghp-online.de.
    This spider first scrapes a list of clinics and their websites, then
    visits each website to find contact information.
    """
    name = 'hirnstimulation'
    
    # The starting URL for the spider.
    start_urls = ['https://dghp-online.de/index.php/kliniken']

    # --- How to run this spider ---
    # 1. Make sure you have Scrapy installed: pip install scrapy
    # 2. Save this file as 'hirnstimulation_spider.py' in a Scrapy project's 'spiders' directory.
    #    (To create a project: scrapy startproject clinic_scraper)
    # 3. Run the spider from the project's root directory using the command:
    #    scrapy crawl hirnstimulation -o clinics.json

    def parse(self, response):
        """
        Step 1: Parse the main table of clinics.
        This method extracts the clinic name and website URL, then yields a 
        new request to crawl that specific clinic's website.
        """
        self.log("Starting to parse the main clinic index page.")

        # Select all rows from the main table, skipping the header.
        clinic_rows = response.css('section.article-content table:first-of-type tbody tr')[1:]

        if not clinic_rows:
            self.log("No clinic rows found on the index page. Please check the selector.")
            return

        # Iterate over each row to get the name and link.
        for row in clinic_rows:
            clinic_name_parts = row.css('td:nth-child(1) *::text').getall()
            clinic_name = ' '.join(part.strip() for part in clinic_name_parts if part.strip())
            
            website_url = row.css('td:nth-child(1) a::attr(href)').get()

            if website_url:
                # For each clinic, send a new request to its website.
                # We pass the already scraped data (name, website) to the callback.
                yield response.follow(
                    website_url, 
                    callback=self.parse_clinic_page,
                    cb_kwargs={
                        'name': clinic_name,
                        'website': website_url
                    }
                )
            else:
                # If no website is listed, yield what we have.
                yield {
                    'name': clinic_name,
                    'website': None,
                    'phone_number': None,
                    'email': None
                }

    def parse_clinic_page(self, response, name, website):
        """
        Step 2: Parse the individual clinic's website for contact info.
        This method searches the HTML of the clinic's page for phone and email.
        """
        self.log(f"Parsing clinic page: {name}")
        
        # --- Email Extraction ---
        # First, look for mailto links, as they are the most reliable.
        email = response.css('a[href^="mailto:"]::attr(href)').re_first(r'mailto:(.+)')
        
        # If no mailto link is found, search the entire page text for an email pattern.
        if not email:
            email = response.xpath('//body').re_first(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')

        # --- Phone Number Extraction ---
        # First, look for tel: links.
        phone = response.css('a[href^="tel:"]::attr(href)').re_first(r'tel:(.+)')

        # If no tel: link is found, search the page text for common phone number patterns.
        # This regex is broad to catch various formats.
        if not phone:
            phone = response.xpath('//body').re_first(r'(\+?\d{1,3}[\s\-\(\)]*\d{2,}[\s\-\(\)]*\d{2,}[\s\-\(\)]*\d+)')

        # Yield the final, complete data for the clinic.
        yield {
            'name': name,
            'website': website,
            'phone_number': phone.strip() if phone else None,
            'email': email.strip() if email else None,
            'country': 'Germany'
        }
