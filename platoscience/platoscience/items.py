import scrapy
from itemloaders.processors import MapCompose, TakeFirst, Join

# --- Custom Processors ---
# Best Practice: Define custom processors to handle data cleaning tasks
# that are specific to your project.


def clean_text(value):
    """
    A robust custom processor to strip leading/trailing whitespace.
    It safely handles non-string and None values.
    """
    # Robustness: Check if the value is a string before trying to strip it.
    if isinstance(value, str):
        return value.strip()
    # Return the value as-is if it's not a string (e.g., None, int).
    return value

# --- Item Definitions ---


class ProviderItem(scrapy.Item):
    """
    Defines the data structure for a provider scraped from a source that requires
    a multi-stage crawl (e.g., crawling an external website).

    Processors automatically clean and format the data as it's added by the ItemLoader.
    - input_processor: Runs on each piece of data as it's added to a field.
    - output_processor: Runs on the entire list of data for a field just before the item is yielded.
    """

    # --- Data Fields ---
    name = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    source_url = scrapy.Field(
        output_processor=TakeFirst()
    )
    phone = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    email = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    website_link = scrapy.Field(
        output_processor=TakeFirst()
    )
    specialties = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(', ')
    )
    therapy_types = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(', ')
    )
    address = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(', ')
    )
    social_links = scrapy.Field(
        output_processor=Join(', ')
    )
    state = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    zipcode = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    self_description = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(' ')
    )
    tags = scrapy.Field()


class ClinicItem(scrapy.Item):
    """
    Defines the final, standardized data structure for a clinic after
    all scraping and data processing is complete. This serves as the
    target schema for the master data file.
    """
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
