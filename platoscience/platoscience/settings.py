import json

BOT_NAME = "platoscience"

SPIDER_MODULES = ["platoscience.spiders"]
NEWSPIDER_MODULE = "platoscience.spiders"

KEYWORDS_TO_FIND = [
    "tms", "rtms", "dtms", "tbs", "eeg", "qeeg", "neurofeedback",
    "biofeedback", "neuromodulation", "brain mapping", "erp",
    "depression", "mdd", "ocd", "anxiety", "ptsd", "adhd", "add",
    "peak performance", "cognitive enhancement", "stroke rehabilitation",
    "chronic pain", "migraine", "psychiatrist", "neurologist",
    "neuropsychologist", "therapist", "bcn", "qeeg-d",
    "mental health professional", "behavioral health", "clinic",
    "wellness center", "rehabilitation center", "private practice",
    "hospital", "neuroscience center", "university research",
    "clinical trials", "telehealth", "telepsychiatry", "digital health",
    "brain stimulation", "neurotechnology", "mental wellness",
    "non-invasive treatment", "integrative medicine"
]

ABOUT_PAGE_KEYWORDS = [
    'about', 'team', 'story', 'mission', 'vision',
    'clinic', 'company', 'who-we-are', 'our-practice'
]
STATES_TO_CRAWL = ['alaska']

ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


DOWNLOADER_MIDDLEWARES = {
    "platoscience.middlewares.PlatoscienceDownloaderMiddleware": 544,
}

ITEM_PIPELINES = {
    "platoscience.pipelines.DataCleaningPipeline": 300,
}

FEED_EXPORT_ENCODING = "utf-8"

FEED_STORAGES = {
    "gsheets": "scrapy_google_sheets_exporter.gsheets_exporter.GoogleSheetsFeedStorage",
}

CREDENTIALS_FILE = "platoscience/credentials.json"
try:
    with open(CREDENTIALS_FILE) as f:
        GOOGLE_CREDENTIALS = json.load(f)
except FileNotFoundError:
    print(f"ERROR: Credentials file not found at '{CREDENTIALS_FILE}'")
    GOOGLE_CREDENTIALS = None

GSHEETS_SPREADSHEET_ID = "1avyAe8ORhqR1i6eyAIPH8ifeOEoWrgDMdPv6FnA_yvc"

LOG_LEVEL = 'DEBUG'
