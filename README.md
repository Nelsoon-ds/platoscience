# Platoscience - Psychology Today Scraper

This Scrapy project is designed to crawl the Psychology Today website to gather information about mental health providers. It performs a multi-stage scrape, starting with state-level listings, then visiting individual provider profiles, and finally crawling the provider's external website to enrich the data with contact details and relevant keywords.

## Features

-   **State-Based Crawling:** Easily configure which US states to crawl via the `settings.py` file.
-   **Multi-Stage Data Enrichment:**
    1.  Scrapes provider listings from Psychology Today.
    2.  Visits each provider's profile for details like specialties and descriptions.
    3.  Follows the provider's external website link.
    4.  Parses the external site for contact information (email, social media) and keywords.
    5.  Attempts to find and scrape the 'About Us' page for a more detailed description.
-   **Robust Data Extraction:** Uses a fallback mechanism to find data, checking for information in the page body, JSON-LD scripts, and specific HTML tags.
-   **Data Cleaning Pipeline:** A dedicated pipeline cleans and standardizes phone numbers, addresses, emails, and website URLs.
-   **Google Sheets Integration:** Scraped data is exported directly to a specified Google Sheet using `scrapy-google-sheets-exporter`.

## Project Structure

platoscience/
├── platoscience/
│ ├── spiders/
│ │ ├── psychologytoday.py # The main spider logic
│ ├── items.py # Defines the data structure (schema)
│ ├── middlewares.py # Custom middleware (currently boilerplate)
│ ├── pipelines.py # Data cleaning and processing pipeline
│ ├── settings.py # Project settings and configuration
├── scrapy.cfg # Scrapy project configuration file
└── requirements.txt # Python dependencies



## Setup and Installation

### Prerequisites

-   Python 3.8+
-   pip package installer

### Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd platoscience
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Google Sheets API Credentials**

    This project uses `scrapy-google-sheets-exporter` to write data to Google Sheets. You must authenticate with a Google Cloud service account.

    a. Follow the [authentication guide](https://gspread.readthedocs.io/en/latest/oauth2.html) to create a service account and download your JSON credentials file.

    b. **IMPORTANT SECURITY WARNING:** Rename the downloaded file to `credentials.json` and place it in the `platoscience/` directory. **DO NOT commit this file to Git or any public repository.** It contains private keys that grant access to your Google account. Add it to your `.gitignore` file immediately:
    ```
    echo "platoscience/credentials.json" >> .gitignore
    ```

    c. Share your target Google Sheet with the `client_email` found inside your `credentials.json` file, giving it "Editor" permissions.

## Configuration

All major configurations are located in `platoscience/settings.py`:

-   `GSHEETS_SPREADSHEET_ID`: The ID of your Google Sheet, found in its URL.
-   `STATES_TO_CRAWL`: A Python list of US states to crawl (e.g., `['Wisconsin', 'Illinois']`).
-   `KEYWORDS_TO_FIND`: A list of keywords to search for on external provider websites. Matched keywords are added to the `tags` field.
-   `ABOUT_PAGE_KEYWORDS`: Keywords used to identify links to 'About Us' pages on external sites.
-   `AUTOTHROTTLE_ENABLED`: Set to `True` by default for polite crawling. You can adjust the target concurrency and delay.

## How to Run the Spider

Execute the following command from the project's root directory:

```bash
scrapy crawl psychology