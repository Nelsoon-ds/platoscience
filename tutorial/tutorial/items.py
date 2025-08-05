# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ClinicItem(scrapy.Item):
    # Core Identity Fields
    clinic_name = scrapy.Field()
    full_address = scrapy.Field() # Combining address lines for simplicity
    phone_number = scrapy.Field()
    clinic_website = scrapy.Field()

    # Provenance & Source Intelligence
    source_name = scrapy.Field()
    source_url = scrapy.Field()
    source_category = scrapy.Field()
    
    # Enriched Strategic Data
    tms_equipment_brand = scrapy.Field()
    provider_tier = scrapy.Field() # e.g., 'Elite', 'Premier'
    
    # Technical Metadata
    scrape_timestamp = scrapy.Field()