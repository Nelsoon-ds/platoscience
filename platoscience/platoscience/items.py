import scrapy
from itemloaders.processors import MapCompose, TakeFirst, Join


def strip_whitespace(value):
    """Custom processor to strip leading/trailing whitespace."""
    return value.strip()

class ProviderItem(scrapy.Item):
    """
    Defines the data structure for a scraped provider.
    Processors are used to clean and format the data automatically
    before it gets saved.
    """
    # --- Input Processors (run on data as it's added) ---
    # MapCompose applies a series of functions to each value.
    # Here, we're just stripping whitespace from every text field.
    name = scrapy.Field(
        input_processor=MapCompose(strip_whitespace),
        output_processor=TakeFirst() # Takes the first non-null value
    )
    source_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    phone = scrapy.Field(
        input_processor=MapCompose(strip_whitespace),
        output_processor=TakeFirst()
    )
    email = scrapy.Field(
        input_processor=MapCompose(strip_whitespace),
        output_processor=TakeFirst()
    )
    website_link = scrapy.Field(
        output_processor=TakeFirst()
    )
    # Join() will join all the collected text with a space.
    self_description = scrapy.Field(
        input_processor=MapCompose(strip_whitespace),
        output_processor=Join(' ')
    )
    # For tags, we don't use TakeFirst() because we want the whole list.
    tags = scrapy.Field()
    

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

