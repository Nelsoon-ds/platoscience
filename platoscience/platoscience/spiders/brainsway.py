import scrapy
import json

class BrainswaySpider(scrapy.Spider):
    """
    A Scrapy spider to crawl https://www.brainsway.com/find-a-provider/.
    This version scrapes links to all provider pages directly from the HTML,
    then visits each page to extract contact details.
    """
    name = 'brainsway'
    allowed_domains = ['brainsway.com']
    start_urls = ['https://www.brainsway.com/find-a-provider/']

    def parse(self, response):
        """
        This method parses the main "Find a Provider" page.
        It finds all the individual provider page links directly from the HTML
        and creates a request to scrape each one.
        """
        self.log(f'Successfully fetched: {response.url}')

        # Get all the links to the individual provider pages using the selector you found.
        provider_links = response.css('ul.columns.max-3-columns a::attr(href)').getall()

        if not provider_links:
            self.log("Could not find any provider links using the specified selector. The website structure might have changed.")
            return

        # Follow each link to the provider's page and call the parse_provider_page method.
        for link in provider_links:
            yield response.follow(url=link, callback=self.parse_provider_page)

    def parse_provider_page(self, response):
        """
        This method is called for each individual provider's page.
        It scrapes all the contact details from this page.
        """
        self.log(f"Scraping details from: {response.url}")

        # Extract the name of the provider from the main H1 tag.
        name = response.css('h1::text').get()

        # Extract the full address text, joining the lines from the <p> tag.
        address_lines = response.css('div.location-contact-address-content p *::text').getall()
        detailed_address = ' '.join(line.strip() for line in address_lines if line.strip())

        # Extract the phone number from the link's text.
        detailed_phone = response.css('div.location-contact-phone a::text').get()

        # Extract the email. We get all text nodes, take the last one (the email), and strip whitespace.
        email = None
        email_text_nodes = response.css('div.location-contact-email p::text').getall()
        if email_text_nodes:
             email = email_text_nodes[-1].strip()

        # Extract the website URL from the link's href attribute.
        website_link = response.css('div.location-contact-website a::attr(href)').get()
        
        # Extract the Google Maps link.
        map_link = response.css('div.location-contact-maplink a::attr(href)').get()

        # Yield all the scraped data as a single dictionary item.
        yield {
            'source_url': response.url,
            'name': name.strip() if name else None,
            'detailed_address': detailed_address,
            'detailed_phone': detailed_phone,
            'email': email,
            'website_link': website_link,
            'map_link': map_link,
        }
