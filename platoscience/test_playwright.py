import scrapy
from scrapy_playwright.page import PageMethod


class TestPlaywrightSpider(scrapy.Spider):
    name = "test_playwright"

    def start_requests(self):
        yield scrapy.Request(
            "https://httpbin.org/headers",
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_timeout", 1000)  # just wait 1 second
                ],
            },
        )

    async def parse(self, response):
        self.logger.info("Playwright test spider ran successfully!")
        self.logger.info(f"Response status: {response.status}")
        self.logger.info(f"Response body snippet: {response.text[:200]}")
