import scrapy


class ClinicItem(scrapy.Item):
    # Core Identity Fields
    clinic_name = scrapy.Field()
    full_address = scrapy.Field()
    phone_number = scrapy.Field()
    clinic_website = scrapy.Field()

    # Provenance & Source Intelligence
    source_name = scrapy.Field()
    source_url = scrapy.Field()
    source_category = scrapy.Field()
    
    # Enriched Strategic Data
    tms_equipment_brand = scrapy.Field()
    provider_tier = scrapy.Field()
    
    # Technical Metadata
    scrape_timestamp = scrapy.Field()