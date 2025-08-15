# platoscience/spiders/psychologytoday.py

import scrapy
from scrapy.loader import ItemLoader
import re
from ..items import ProviderItem
import json


class PsychologyTodaySpider(scrapy.Spider):
    name = 'psychology'
    # Custom settings for this spider, specifically for the Google Sheets feed exporter.
    # These settings override the global settings in settings.py.
    custom_settings = {
        "FEEDS": {
            # The key is the Google Sheets URL.
            "gsheets://docs.google.com/spreadsheets/d/1avyAe8ORhqR1i6eyAIPH8ifeOEoWrgDMdPv6FnA_yvc/edit#gid=0": {
                "format": "csv",
                "encoding": "utf-8",
                "gsheets_sheet_name": "Scrape",
                "include_headers_line": False,  # Set to True if the sheet is empty
                "fields": [
                    "name", "phone", "email", "website_link", "address",
                    "state", "zipcode", "specialties", "therapy_types",
                    "self_description", "tags", "social_links", "source_url"
                ],
                "overwrite": False  # Appends new data instead of clearing the sheet
            }
        }
    }

    def start_requests(self):
        base_url = 'https://www.psychologytoday.com/us/treatment-rehab/'
        states = self.settings.getlist('STATES_TO_CRAWL', [])
        if not states:
            self.logger.error(
                "No states found in STATES_TO_CRAWL setting.")
            return

        for state in states:
            formatted_state = state.lower().replace(' ', '-')
            url = f"{base_url}{formatted_state}"
            yield scrapy.Request(url=url, callback=self.parse_results_page, errback=self.handle_start_error)

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

    def parse_clinic_page(self, response):
        # Scrape the Psychology Today profile page
        self.log(f"Scraping clinic details from: {response.url}")
        loader = ItemLoader(item=ProviderItem(), response=response)

        # --- Load all the data from the Psychology Today page first ---
        loader.add_value('source_url', response.url)
        loader.add_css('name', 'h1.profile-title::text')

        phone_href = response.css('a[href^="tel:"]::attr(href)').get()
        if phone_href:
            loader.add_value('phone', phone_href.replace('tel:', ''))

        loader.add_css(
            'self_description', 'div.personal-statement-container ::text')
        loader.add_css(
            'specialties', 'h3:contains("Top Specialties") + ul li ::text')
        loader.add_css('therapy_types',
                       'h3:contains("Types of Therapy") + ul li ::text')

        address_block = response.css('div.address-tile[data-v-54451946]')
        if address_block:
            # Pass all address lines to the loader; the processor will join them.
            loader.add_css('address', 'p.address-line ::text',
                           response=address_block)

            last_line = address_block.css(
                'p.address-line:last-child ::text').get()

            if last_line:
                match_addr = re.search(
                    r'^(.*),\s*([A-Z]{2})\s*(\d{5})$', last_line.strip())
                if match_addr:
                    loader.add_value('state', match_addr.group(2))
                    loader.add_value('zipcode', match_addr.group(3))

        website_link = response.css(
            'a[data-x="website-link"]::attr(href)').get()

        self.log(f"DEBUG: The extracted website link is: {website_link}")

        if not website_link:
            self.log(
                f"No website link found for {loader.get_output_value('name')}. Yielding item as-is.")
            yield loader.load_item()
            return

        match_id = re.search(r'/(\d+)', website_link)

        if match_id:
            clinic_id = match_id.group(1)
            redirect_url = f"https://out.psychologytoday.com/us/profile/{clinic_id}/website-redirect"
            self.log(
                f"Found redirect URL for clinic {clinic_id}: {redirect_url}")

            yield scrapy.Request(
                url=redirect_url,
                callback=self.parse_external_website,
                errback=self.handle_error,
                meta={'loader': loader}
            )
        else:
            self.log(
                f"Could not find clinic ID in {website_link}. Yielding item without external data.")
            yield loader.load_item()

    def parse_json_ld(self, response, loader):
        """
        Looks for JSON-LD script tags, parses them, and loads data.
        This is used as a fallback if a quick body scan fails.
        """
        script_text = response.css(
            'script[type="application/ld+json"]::text').get()
        if not script_text:
            return False

        try:
            data = json.loads(script_text)
            data_graph = data.get('@graph', [])

            if not isinstance(data_graph, list):
                return False

            for item in data_graph:
                if 'email' in item:
                    loader.add_value('email', item.get('email'))
                if 'telephone' in item:
                    loader.add_value('phone', item.get('telephone'))
                if 'sameAs' in item:
                    loader.add_value('social_links', item.get('sameAs'))

            self.logger.info(
                f"Successfully loaded data from JSON-LD on {response.url}")
            return True

        except json.JSONDecodeError:
            self.logger.warning(
                f"Found JSON-LD script, but failed to parse it on {response.url}")
            return False

    def parse_external_website(self, response):
        """
        Parses the external website by trying a quick body scan first,
        then falling back to JSON-LD and other methods.
        """
        loader = response.meta['loader']
        loader.response = response
        final_url = response.url
        loader.add_value('website_link', final_url)
        self.log(f"Processing external site: {final_url}")

        # --- STAGE 1: Quick search on the body text first ---
        body_text = ' '.join(response.xpath('//body//text()').getall()).lower()
        emails = re.findall(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b', body_text, re.IGNORECASE)

        if emails:
            loader.add_value('email', list(set(emails))[0])
            self.logger.info(
                f"Found email via body text scan on {response.url}")

        # --- STAGE 2: If no email found, parse the JSON-LD as a fallback ---
        if not loader.get_output_value('email'):
            self.logger.info(
                f"Body text scan failed. Attempting JSON-LD parse on {response.url}")
            # This helper will add email, phone, and socials if it finds them
            self.parse_json_ld(response, loader)

        # --- STAGE 3: Fallback for social links if JSON-LD didn't find them ---
        if not loader.get_output_value('social_links'):
            socials = response.css('a::attr(href)').re(
                r'(https?://(?:www\.)?(?:facebook|linkedin|instagram|twitter|youtube)\.com[^\s"\']*)')
            if socials:
                loader.add_value('social_links', list(set(socials)))

        # --- STAGE 4: Search for keywords in the body text ---
        keywords = self.settings.getlist('KEYWORDS_TO_FIND', [])
        tags = [kw for kw in keywords if kw.lower() in body_text]
        if tags:
            loader.add_value('tags', tags)

        # --- STAGE 5: Find the 'About Us' page to get a better description ---
        about_keywords = self.settings.getlist('ABOUT_PAGE_KEYWORDS', [])
        conditions = [
            f"contains(translate(., '{k.upper()}', '{k.lower()}'), '{k.lower()}')" for k in about_keywords]
        conditions += [f"contains(@href, '{k}')" for k in about_keywords]
        about_link_xpath = f"//a[{' or '.join(conditions)}]/@href"
        about_link = response.xpath(about_link_xpath).get()

        if about_link:
            about_url = response.urljoin(about_link)
            self.log(f"Found 'About' page link: {about_url}")
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
        # Scrape the 'About Us' page for the description
        loader = response.meta['loader']
        self.log(
            f"Scraping description from 'About' page for {loader.get_output_value('name')}.")

        loader.add_css('self_description', 'p ::text')

        yield loader.load_item()

    # --- Error handling callbacks  ---
    def handle_start_error(self, failure):
        self.logger.error(
            f"Initial request to {failure.request.url} failed: {failure.value}")

    def handle_error(self, failure):
        loader = failure.request.meta['loader']
        name = loader.get_output_value('name') or 'Unknown'
        self.logger.error(
            f"Request to external site for '{name}' ({failure.request.url}) failed: {failure.value}. Yielding partial data.")
        yield loader.load_item()

    def handle_about_error(self, failure):
        loader = failure.request.meta['loader']
        name = loader.get_output_value('name')
        self.logger.warning(
            f"Request to 'About Us' page failed for '{name}'. Yielding item without overriding description.")
        yield loader.load_item()
