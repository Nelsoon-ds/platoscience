# platoscience/spiders/psychologytoday.py - Final Corrected Version

import scrapy
from scrapy.loader import ItemLoader
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError
import re
from scrapy_playwright.page import PageMethod
from ..items import ProviderItem


class PsychologyTodaySpider(scrapy.Spider):
    # name = 'psychologytoday'

    custom_settings = {
        "FEEDS": {
            "gsheets://docs.google.com/spreadsheets/d/1avyAe8ORhqR1i6eyAIPH8ifeOEoWrgDMdPv6FnA_yvc/edit#gid=0": {
                "format": "csv",
                "fields": [
                    "name", "phone", "email", "website_link", "address", "city",
                    "state", "zipcode", "specialties", "therapy_types",
                    "conditions", "self_description", "tags", "social_links", "source_url"
                ],
                "overwrite": True,
            }
        },
    }

    # Using start_requests is a standard Scrapy practice.
    def start_requests(self):
        base_url = 'https://www.psychologytoday.com/us/treatment-rehab/'
        states = self.settings.getlist('STATES_TO_CRAWL', [])
        if not states:
            self.logger.error("No states found in STATES_TO_CRAWL setting.")
            return
        for state in states:
            # This correctly handles states with spaces, e.g., "new-york".
            formatted_state = state.lower().replace(' ', '-')
            url = f"{base_url}{formatted_state}"
            yield scrapy.Request(url=url, callback=self.parse_results_page)

    def parse_results_page(self, response):
        self.log(f'Successfully fetched results page: {response.url}')

        # This robust selector finds all clinic links on the page.
        clinic_links = response.css(
            'div.results-row a.profile-title::attr(href)').getall()
        for link in clinic_links:
            yield response.follow(url=link, callback=self.parse_clinic_page)

        # This correctly finds the "Next" button for pagination.
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
        self.log(f"Scraping clinic details from: {response.url}")
        loader = ItemLoader(item=ProviderItem(), response=response)
        loader.add_value('source_url', response.url)
        loader.add_css('name', 'h1.profile-title::text')

        phone_href = response.css('a[href^="tel:"]::attr(href)').get()
        if phone_href:
            phone_number = phone_href.replace('tel:', '')
            loader.add_value('phone', phone_number)

        description_parts = response.css(
            'div.personal-statement-container ::text').getall()
        loader.add_value('self_description',
                         self.clean_text(description_parts))

        loader.add_xpath(
            'specialties',
            '//h2[contains(text(), "Specialties")]/following-sibling::div[1]//li/text()'
        )
        loader.add_xpath(
            'therapy_types',
            '//h3[contains(text(), "Types of Therapy")]/following-sibling::ul[1]//li/text()'
        )
        loader.add_xpath(
            'conditions',
            '//h3[contains(text(), "Issues")]/following-sibling::ul[1]//li/text()'
        )

        address_block = response.css('div.address-tile[data-v-54451946]')
        if address_block:
            address_lines = address_block.css('p.address-line ::text').getall()
            full_address = self.clean_text(address_lines)
            loader.add_value('address', full_address)

            last_line = address_lines[-1].strip() if address_lines else ''
            match = re.search(r'^(.*),\s*([A-Z]{2})\s*(\d{5})$', last_line)
            if match:
                loader.add_value('city', match.group(1).strip())
                loader.add_value('state', match.group(2).strip())
                loader.add_value('zipcode', match.group(3).strip())

        # 👇 1. We find the website link like before.
        website_link = response.css(
            'a[data-x="website-link"]::attr(href)').get()

        # If there's no website link, we just yield the data we have.
        if not website_link:
            yield loader.load_item()
            return

        yield scrapy.Request(
            url=response.urljoin(website_link),
            callback=self.parse_final_website,  # Send it to the new callback
            meta={
                'loader': loader,
                'playwright': True,  # This tells Scrapy to use Playwright
                'playwright_page_methods': [
                    PageMethod('wait_for_selector',
                               'span.website-interstitial-link', timeout=5000),
                    PageMethod('click', 'span.website-interstitial-link'),
                    PageMethod('wait_for_load_state', 'load'),

                ],
            },
            errback=self.handle_error
        )

    def parse_final_website(self, response):
        """
        This callback is executed after Playwright has handled the redirect.
        The response object here is from the FINAL clinic website.
        """
        loader = response.meta['loader']

        # The final URL is simply the URL of the response we received!
        final_url = response.url
        loader.add_value('website_link', final_url)

        # Now we can run the logic that used to be in `parse_external_website`.
        body_text = ' '.join(response.xpath('//body//text()').getall()).lower()

        emails = re.findall(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', body_text)
        if emails:
            # Simple cleaning to remove common non-contact emails.
            clean_emails = list(
                set([e for e in emails if not e.startswith(('noreply@', 'no-reply@', 'sentry@'))]))
            if clean_emails:
                loader.add_value('email', clean_emails[0])

        socials = response.css('a::attr(href)').re(
            r'(https?://(?:www\.)?(?:facebook|linkedin|instagram|twitter|youtube)\.com[^\s"\']*)')
        if socials:
            loader.add_value('social_links', list(set(socials)))

        keywords_to_find = self.settings.getlist('KEYWORDS_TO_FIND', [])
        tags = [kw for kw in keywords_to_find if kw.lower() in body_text]
        if tags:
            loader.add_value('tags', tags)

        # The rest of your logic to find the 'about' page can go here.
        # For simplicity, I'm just yielding the item.
        yield loader.load_item()

        # Note: I've removed the parse_about_page logic for brevity,
        # but you can easily add it back in here if needed.

    def handle_error(self, failure):
        # This error handler now correctly catches failures from the final website.
        loader = failure.request.meta['loader']
        name = loader.get_output_value('name') or 'Unknown'
        error_type = "Unknown Error"
        if failure.check(HttpError):
            error_type = f"HTTP Error {failure.value.response.status}"
        elif failure.check(DNSLookupError):
            error_type = "DNS Lookup Error"
        elif failure.check(TimeoutError, TCPTimedOutError):
            error_type = "Timeout Error"
        self.logger.error(
            f"Request to external site for '{name}' ({failure.request.url}) failed: {error_type}")
        # Yield what we have so we don't lose the data from the PT page.
        yield loader.load_item()
