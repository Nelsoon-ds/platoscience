import scrapy
import re

class NexstimSpider(scrapy.Spider):
    """
    A Scrapy spider to extract clinic information from nexstim.com.
    It scrapes clinic details, grouped by country.
    """
    name = 'nexstim'
    
    # The starting URL for the spider.
    start_urls = ['https://www.nexstim.com/patients/users-and-locations']


    def parse(self, response):
        """
        This method parses the main page, iterating through each country section
        and then extracting the details for each clinic within that section.
        """
        self.log("Starting to parse nexstim.com clinic locations.")

        # The page is structured in sections, each starting with a country header.
        # We select all 'grid-accordion' sections.
        for country_section in response.css('section.grid-accordion'):
            # Extract the country name from the h2 tag within the section's header.
            country = country_section.css('.ceheader h2::text').get()

            # Within each country section, find all the clinic content boxes.
            for clinic_box in country_section.css('.contentbox'):
                # Extract the clinic name from the h3 tag.
                name = clinic_box.css('h3::text').get()

                # If a name is found, it's a valid clinic box to process.
                if name:
                    # Extract all text within the <p> tags. This will contain address, phone, etc.
                    # We get all text parts and then join them.
                    p_texts = clinic_box.css('p *::text').getall()
                    full_details = ' '.join(p.strip() for p in p_texts if p.strip())
                    
                    # --- Extract Phone Number ---
                    # Use regex to find a phone number pattern.
                    phone_match = re.search(r'Tel:\s*([+\d\s\(\)-]+)', full_details, re.IGNORECASE)
                    phone = phone_match.group(1).strip() if phone_match else None

                    # --- Extract Email ---
                    # The email is obfuscated in a 'data-mailto-token' attribute.
                    # We can't decode it directly, but the visible text parts are there.
                    email_parts = clinic_box.css('a[data-mailto-token] *::text').getall()
                    email = ''.join(email_parts).strip() if email_parts else None
                    
                    # --- Extract Website ---
                    # The website link has a specific class 'more-link'.
                    website = clinic_box.css('a.more-link::attr(href)').get()
                    
                    # The address is tricky. We'll take all lines from the first <p> tag,
                    # filter out lines with "Tel:", and join the rest.
                    address_lines = clinic_box.css('p:first-of-type::text').getall()
                    address = ' '.join(line.strip() for line in address_lines if 'Tel:' not in line and line.strip())

                    yield {
                        'country': country.strip() if country else None,
                        'clinic_name': name.strip() if name else None,
                        'address': address,
                        'phone_number': phone,
                        'email': email if email else None,
                        'website': response.urljoin(website) if website else None,
                    }

        self.log("Finished parsing clinic locations.")
