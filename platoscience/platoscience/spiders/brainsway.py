# brainsway.py

import scrapy
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.loader import ItemLoader
from ..items import ProviderItem # Import our new item

class BrainswaySpider(scrapy.Spider):
    """
    A Scrapy spider to crawl https://www.brainsway.com/find-a-provider/.
    It uses an ItemLoader to structure and clean the scraped data.
    """
    name = 'brainsway'
    start_urls = ['https://www.brainsway.com/find-a-provider/']

    def parse(self, response):
        self.log(f'Successfully fetched: {response.url}')
        provider_links = response.css('ul.columns.max-3-columns a::attr(href)').getall()
        if not provider_links:
            self.log("Could not find any provider links.")
            return
        for link in provider_links:
            yield response.follow(url=link, callback=self.parse_provider_page)

    def parse_provider_page(self, response):
        """
        Gathers initial provider details and passes an ItemLoader
        to the next request.
        """
        self.log(f"Scraping initial details from: {response.url}")
        website_link = response.css('div.location-contact-website a::attr(href)').get()
        if not website_link:
            self.log(f"No website link found for {response.url}. Skipping.")
            return
            
        # 1. Create the ItemLoader, linking it to our ProviderItem
        loader = ItemLoader(item=ProviderItem(), response=response)

        # 2. Add data using CSS selectors. No more .get() or .strip() needed!
        # The processors in items.py handle that automatically.
        loader.add_value('source_url', response.url)
        loader.add_css('name', 'h1::text')
        loader.add_css('phone', 'div.location-contact-phone a::text')
        loader.add_css('email', 'div.location-contact-email p::text')
        loader.add_value('website_link', website_link)

        # 3. Pass the loader object in the meta dict
        yield scrapy.Request(
            url=website_link,
            callback=self.parse_external_website,
            errback=self.handle_error,
            meta={'loader': loader} # Pass the whole loader
        )

    def parse_external_website(self, response):
        """
        Parses the external site, finds keywords for tags, and looks
        for a link to an "About Us" page anywhere on the page.
        """
        loader = response.meta['loader']
        loader.response = response
        self.log(f"Processing external site: {loader.get_output_value('website_link')}")

        body_text = ' '.join(response.xpath('//body//text()').getall()).lower()
        tags = []
        for keyword in self.settings.get('KEYWORDS_TO_FIND', []):
            if keyword.lower() in body_text:
                tags.append(keyword)
        loader.add_value('tags', tags)
        
        about_keywords = self.settings.get('ABOUT_PAGE_KEYWORDS', [])
        conditions = [f"contains(translate(., '{k.upper()}', '{k}'), '{k}')" for k in about_keywords]
        conditions += [f"contains(@href, '{k}')" for k in about_keywords]
        
        # --- THE CHANGE IS HERE ---
        # OLD: //footer//a[...] (Searched only in the footer)
        # NEW: //a[...] (Searches the entire page)
        about_link_xpath = f"//a[{' or '.join(conditions)}]/@href"
        
        about_link_selector = response.xpath(about_link_xpath).get()
        
        if about_link_selector:
            about_url = response.urljoin(about_link_selector)
            self.log(f"Found 'About' page via page-wide search: {about_url}")
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
        Parses the 'About Us' page to get the self-description using
        a hybrid approach for maximum reliability.
        """
        # 1. Get the loader, just like before.
        loader = response.meta['loader']

        # 2. Scrape the description DIRECTLY from the response, just like your old code.
        #    This avoids any confusion with the loader's internal response.
        #    (Note: I'm using 'p ::text' to get all text, which is a slight improvement).
        p_texts = response.css('p ::text').getall()
        description = ' '.join(text.strip() for text in p_texts if text.strip())

        # 3. Use .add_value() to add the already-scraped text to the loader.
        #    .add_value() doesn't use selectors, so it can't get confused.
        loader.add_value('self_description', description)
        
        self.log(f"Successfully scraped description for {loader.get_output_value('name')}.")
        
        # 4. Yield the final, clean item.
        yield loader.load_item()

    def handle_error(self, failure):
            """
            Handles errors when fetching the provider's external website.
            It logs the error and yields the partial data collected so far.
            """
            loader = failure.request.meta['loader']
            url = loader.get_output_value('website_link')
            name = loader.get_output_value('name')
            
            error_msg = f"Error processing {name} at URL: {url}."
            
            if failure.check(HttpError):
                error_msg += f" HTTP Status: {failure.value.response.status}."
            elif failure.check(DNSLookupError):
                error_msg += " DNS Lookup Error."
            elif failure.check(TimeoutError, TCPTimedOutError):
                error_msg += " Timeout Error."
            else:
                error_msg += f" Unhandled Error: {failure.value}"
                
            self.logger.error(error_msg)
            # Don't lose the data! Yield the item with the info we already scraped.
            yield loader.load_item()

    def handle_about_error(self, failure):
            """
            Handles errors when fetching the 'About Us' page. It logs the
            warning and yields the item without a self-description.
            """
            loader = failure.request.meta['loader']
            name = loader.get_output_value('name')
            self.logger.warning(f"Request to 'About Us' page failed for {name}. Yielding item without description.")
            # We still have the tags and other info, so we yield the item.
            yield loader.load_item()