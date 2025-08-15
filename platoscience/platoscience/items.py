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
    Defines the data structure for a provider.
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
    # The full address string extracted by the spider.
    address = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=Join(', ')
    )
    # The following address components will be populated by the DataCleaningPipeline.
    city = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    state = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    zipcode = scrapy.Field(
        input_processor=MapCompose(clean_text),
        output_processor=TakeFirst()
    )
    social_links = scrapy.Field(
        # Social links can be a list, so we join them into a single string.
        output_processor=Join(', ')
    )
    self_description = scrapy.Field(
        input_processor=MapCompose(clean_text),
        # Join paragraphs of text with a space.
        output_processor=Join(' ')
    )
    # Tags are collected as a list and will be processed by the pipeline.
    tags = scrapy.Field()
