

import crawl4ai
print(crawl4ai.__version__.__version__)

import asyncio
import nest_asyncio
nest_asyncio.apply()

import asyncio
from playwright.async_api import async_playwright

import asyncio
import nest_asyncio
nest_asyncio.apply()

from crawl4ai import AsyncWebCrawler, CacheMode, BrowserConfig, CrawlerRunConfig, CacheMode

async def simple_crawl():
    crawler_run_config = CrawlerRunConfig( cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.naturalgasintel.com/", #https://www.kidocode.com/degrees/technology",
            config=crawler_run_config
        )
        print(result.markdown_v2.raw_markdown)  #[:500].replace("\n", " -- "))  # Print the first 500 characters


asyncio.run(simple_crawl())