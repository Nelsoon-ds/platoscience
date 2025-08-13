# brainsway.py

import scrapy
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.loader import ItemLoader
# Best Practice: Use relative imports within the Scrapy project.
from ..items import ProviderItem

class BrainswaySpider(scrapy.Spider):
    """
    A Scrapy spider to crawl https://www.brainsway.com/find-a-provider/.
    It demonstrates a robust, multi-stage crawl pattern:
    1. Scrape a list of provider links.
    2. Follow each link to a detail page on brainsway.com.
    3. Follow the external website link to the provider's own site.
    4. Attempt to find and scrape an 'About Us' page for more detail.
    It uses an ItemLoader for clean data population and has robust error handling.
    """
    name = 'brainsway'
    start_urls = ['https://www.brainsway.com/find-a-provider/']

    def parse(self, response):
        """
        Stage 1: Fetches the main provider directory and yields requests
        for each individual provider page.
        """
        self.log(f'Successfully fetched directory: {response.url}')
        # Select all links within the main provider list.
        provider_links = response.css('ul.columns.max-3-columns a::attr(href)').getall()
        
        if not provider_links:
            self.log("Could not find any provider links on the main directory page. Check CSS selector.")
            return
            
        self.log(f"Found {len(provider_links)} provider links. Following each...")
        for link in provider_links:
            # For each link, schedule a request to that URL, processed by parse_provider_page.
            yield response.follow(url=link, callback=self.parse_provider_page)

    def parse_provider_page(self, response):
        """
        Stage 2: Gathers initial details from the BrainsWay provider page
        and initiates the crawl to the provider's external website.
        """
        self.log(f"Scraping initial details from: {response.url}")
        
        # Best Practice: Use an ItemLoader to populate the item.
        # This keeps the spider clean and moves data processing to items.py.
        loader = ItemLoader(item=ProviderItem(), response=response)

        # Populate fields from the brainsway.com detail page.
        # .add_value() is for data not directly from the response (like the source URL).
        loader.add_value('source_url', response.url)
        # .add_css() uses CSS selectors to find and automatically clean the data.
        loader.add_css('name', 'h1::text')
        loader.add_css('phone', 'div.location-contact-phone a::text')
        loader.add_css('email', 'div.location-contact-email p::text')
        
        website_link = response.css('div.location-contact-website a::attr(href)').get()
        if not website_link:
            self.log(f"No external website link found for {loader.get_output_value('name')}. Yielding partial item.")
            yield loader.load_item() # Yield the data we have so far
            return
        
        loader.add_value('website_link', website_link)

        # Stage 3: Follow the external website link.
        # Pass the loader object in the meta dict to carry data to the next callback.
        # Add robust error handling for this external request.
        yield scrapy.Request(
            url=website_link,
            callback=self.parse_external_website,
            errback=self.handle_error,
            meta={'loader': loader} 
        )

    def parse_external_website(self, response):
        """
        Stage 3: Parses the homepage of the provider's external site.
        It searches for keywords and looks for a link to an "About Us" page.
        """
        loader = response.meta['loader']
        # It's good practice to update the loader's response context.
        loader.response = response 
        self.log(f"Processing external site: {response.url}")

        # Extract keywords from the body text to use as tags.
        body_text = ' '.join(response.xpath('//body//text()').getall()).lower()
        tags = [kw for kw in self.settings.get('KEYWORDS_TO_FIND', []) if kw.lower() in body_text]
        loader.add_value('tags', tags)
        
        # Dynamically build an XPath to find 'About Us' style links anywhere on the page.
        about_keywords = self.settings.get('ABOUT_PAGE_KEYWORDS', [])
        # Search for keywords in the link's text or its href attribute.
        conditions = [f"contains(translate(., '{k.upper()}', '{k}'), '{k}')" for k in about_keywords]
        conditions += [f"contains(@href, '{k}')" for k in about_keywords]
        about_link_xpath = f"//a[{' or '.join(conditions)}]/@href"
        
        about_link = response.xpath(about_link_xpath).get()
        
        if about_link:
            about_url = response.urljoin(about_link)
            self.log(f"Found 'About' page link: {about_url}")
            # Stage 4: Follow the 'About' page link, continuing to pass the loader.
            yield scrapy.Request(
                url=about_url,
                callback=self.parse_about_page,
                errback=self.handle_about_error,
                meta={'loader': loader}
            )
        else:
            self.log(f"No 'About' link found for {loader.get_output_value('name')}. Finalizing item.")
            yield loader.load_item()

    def parse_about_page(self, response):
        """
        Stage 4: Parses the 'About Us' page to extract a description.
        """
        loader = response.meta['loader']
        self.log(f"Scraping description from 'About' page for {loader.get_output_value('name')}.")

        # Join all text from paragraph tags to form the description.
        p_texts = response.css('p ::text').getall()
        description = ' '.join(text.strip() for text in p_texts if text.strip())
        loader.add_value('self_description', description)
        
        # This is the final step, so we yield the fully populated item.
        yield loader.load_item()

    # --- ERROR HANDLING CALLBACKS ---

    def handle_error(self, failure):
        """
        Handles errors for the initial external website request (Stage 3).
        Logs the specific error and yields the item with partial data.
        """
        loader = failure.request.meta['loader']
        name = loader.get_output_value('name')
        error_type = "Unknown Error"
        if failure.check(HttpError):
            error_type = f"HTTP Error {failure.value.response.status}"
        elif failure.check(DNSLookupError):
            error_type = "DNS Lookup Error"
        elif failure.check(TimeoutError, TCPTimedOutError):
            error_type = "Timeout Error"
            
        self.logger.error(f"Request to external site failed for '{name}' ({failure.request.url}). Reason: {error_type}. Yielding partial data.")
        # Best Practice: Don't lose data. Yield the item with the info we have so far.
        yield loader.load_item()

    def handle_about_error(self, failure):
        """
        Handles errors for the 'About Us' page request (Stage 4).
        This is less critical, so we log a warning and yield the item anyway.
        """
        loader = failure.request.meta['loader']
        name = loader.get_output_value('name')
        self.logger.warning(f"Request to 'About Us' page failed for '{name}'. Yielding item without self-description.")
        # We still have valuable info (tags, etc.), so we yield the item.
        yield loader.load_item()