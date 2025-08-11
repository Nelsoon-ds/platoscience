# platoscience/spiders/psychologytoday.py

import scrapy
from scrapy.loader import ItemLoader
# We no longer need Playwright here!
# from scrapy_playwright.page import PageMethod
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError
import re
from ..items import ProviderItem


class PsychologyTodaySpider(scrapy.Spider):
    name = 'psychology'

    # ... (your custom_settings and start_requests methods are perfect, no change needed) ...
    custom_settings = {
        "FEEDS": {
            "gsheets://docs.google.com/spreadsheets/d/1avyAe8ORhqR1i6eyAIPH8ifeOEoWrgDMdPv6FnA_yvc/edit#gid=0": {
                "format": "csv",
                "encoding": "utf-8",
                "fields": [
                    "name", "phone", "email", "website_link", "address", "city",
                    "state", "zipcode", "specialties", "therapy_types",
                    "conditions", "self_description", "tags", "social_links", "source_url"
                ],
                "overwrite": True,
            }
        },
    }

    def start_requests(self):
        base_url = 'https://www.psychologytoday.com/us/treatment-rehab/'
        states = self.settings.getlist('STATES_TO_CRAWL', [])
        if not states:
            self.logger.error("No states found in STATES_TO_CRAWL setting.")
            return
        for state in states:
            formatted_state = state.lower().replace(' ', '-')
            url = f"{base_url}{formatted_state}"
            yield scrapy.Request(url=url, callback=self.parse_results_page)

    def parse_results_page(self, response):
        self.log(f'Successfully fetched results page: {response.url}')
        clinic_links = response.css(
            'div.results-row a.profile-title::attr(href)').getall()
        for link in clinic_links:
            yield response.follow(url=link, callback=self.parse_clinic_page)

        next_page = response.css(
            'a.previous-next-btn[title*="Next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_results_page)

    def clean_text(self, text_list):
        if not text_list:
            return ""
        cleaned = " ".join(text_list).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r',\s*,', ',', cleaned)
        cleaned = cleaned.strip(', ')
        return cleaned

    def parse_clinic_page(self, response):
        # STAGE 1: Scrape the Psychology Today profile page
        self.log(f"Scraping clinic details from: {response.url}")
        loader = ItemLoader(item=ProviderItem(), response=response)

        # --- Load all the data from the Psychology Today page first ---
        loader.add_value('source_url', response.url)
        loader.add_css('name', 'h1.profile-title::text')

        phone_href = response.css('a[href^="tel:"]::attr(href)').get()
        if phone_href:
            loader.add_value('phone', phone_href.replace('tel:', ''))

        description_parts = response.css(
            'div.personal-statement-container ::text').getall()
        loader.add_value('self_description',
                         self.clean_text(description_parts))

        loader.add_xpath(
            'specialties', '//h2[contains(text(), "Specialties")]/following-sibling::div[1]//li/text()')
        loader.add_xpath(
            'therapy_types', '//h3[contains(text(), "Types of Therapy")]/following-sibling::ul[1]//li/text()')
        loader.add_xpath(
            'conditions', '//h3[contains(text(), "Issues")]/following-sibling::ul[1]//li/text()')

        address_block = response.css('div.address-tile[data-v-54451946]')
        if address_block:
            address_lines = address_block.css('p.address-line ::text').getall()
            loader.add_value('address', self.clean_text(address_lines))
            last_line = address_lines[-1].strip() if address_lines else ''
            match_addr = re.search(
                r'^(.*),\s*([A-Z]{2})\s*(\d{5})$', last_line)
            if match_addr:
                loader.add_value('city', match_addr.group(1).strip())
                loader.add_value('state', match_addr.group(2).strip())
                loader.add_value('zipcode', match_addr.group(3).strip())

        # --- This is our new logic ---
        website_link = response.css(
            'a[data-x="website-link"]::attr(href)').get()

        # !!! ADD THIS LINE FOR DEBUGGING !!!
        self.log(f"DEBUG: The extracted website link is: {website_link}")

        if not website_link:
            self.log(
                f"No website link found for {loader.get_output_value('name')}. Yielding item as-is.")
            yield loader.load_item()
            return

        # 1. Use regex to extract the clinic ID from the URL.
        match_id = re.search(r'/(\d+)', website_link)

        if match_id:
            clinic_id = match_id.group(1)
            # 2. Build the direct redirect URL you discovered.
            redirect_url = f"https://out.psychologytoday.com/us/profile/{clinic_id}/website-redirect"
            self.log(
                f"Found redirect URL for clinic {clinic_id}: {redirect_url}")

            # STAGE 2: Follow the redirect to the external website's homepage
            yield scrapy.Request(
                url=redirect_url,
                callback=self.parse_external_website,
                errback=self.handle_error,
                meta={'loader': loader}
            )
        else:
            # If no ID is found, this block will run.
            self.log(
                f"Could not find clinic ID in {website_link}. Yielding item without external data.")
            yield loader.load_item()

    def parse_external_website(self, response):
        # STAGE 3: Process the external homepage and look for an 'About' link
        loader = response.meta['loader']
        loader.response = response  # Update loader's response context
        final_url = response.url
        loader.add_value('website_link', final_url)
        self.log(f"Processing external site: {final_url}")

        # --- Scrape data from the homepage ---
        body_text = ' '.join(response.xpath('//body//text()').getall()).lower()
        emails = re.findall(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b', body_text, re.IGNORECASE)
        if emails:
            loader.add_value('email', list(set(emails))[0])  # Simplified

        socials = response.css('a::attr(href)').re(
            r'(https?://(?:www\.)?(?:facebook|linkedin|instagram|twitter|youtube)\.com[^\s"\']*)')
        if socials:
            loader.add_value('social_links', list(set(socials)))

        keywords = self.settings.getlist('KEYWORDS_TO_FIND', [])
        tags = [kw for kw in keywords if kw.lower() in body_text]
        if tags:
            loader.add_value('tags', tags)

        # --- Now, look for the 'About Us' link, just like in brainsway.py ---
        about_keywords = self.settings.getlist('ABOUT_PAGE_KEYWORDS', [])
        conditions = [
            f"contains(translate(., '{k.upper()}', '{k.lower()}'), '{k.lower()}')" for k in about_keywords]
        conditions += [f"contains(@href, '{k}')" for k in about_keywords]
        about_link_xpath = f"//a[{' or '.join(conditions)}]/@href"
        about_link = response.xpath(about_link_xpath).get()

        if about_link:
            about_url = response.urljoin(about_link)
            self.log(f"Found 'About' page link: {about_url}")
            # STAGE 4: Follow the 'About' page link
            yield scrapy.Request(
                url=about_url,
                callback=self.parse_about_page,
                errback=self.handle_about_error,
                meta={'loader': loader}
            )
        else:
            self.log(
                f"No 'About' link found. Finalizing item for {loader.get_output_value('name')}.")
            yield loader.load_item()

    def parse_about_page(self, response):
        # STAGE 5: Scrape the 'About Us' page for the description
        loader = response.meta['loader']
        self.log(
            f"Scraping description from 'About' page for {loader.get_output_value('name')}.")

        p_texts = response.css('p ::text').getall()
        description = ' '.join(text.strip()
                               for text in p_texts if text.strip())
        loader.add_value('self_description', description)

        yield loader.load_item()

    def handle_error(self, failure):
        # Handles errors for the main external site request (Stage 2)
        loader = failure.request.meta['loader']
        name = loader.get_output_value('name') or 'Unknown'
        self.logger.error(
            f"Request to external site for '{name}' ({failure.request.url}) failed: {failure.value}. Yielding partial data.")
        yield loader.load_item()

    def handle_about_error(self, failure):
        # Handles errors for the 'About' page request (Stage 4)
        loader = failure.request.meta['loader']
        name = loader.get_output_value('name')
        self.logger.warning(
            f"Request to 'About Us' page failed for '{name}'. Yielding item without full description.")
        yield loader.load_item()
