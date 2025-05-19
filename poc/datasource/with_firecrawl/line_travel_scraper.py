#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to scrape data from LINE Travel website using FireCrawl.
"""

import os
import json
import logging
import sys
from dotenv import load_dotenv
from firecrawl import FirecrawlApp, JsonConfig
from pathlib import Path
from typing import Any, List

from firecrawl.firecrawl import ScrapeResponse
from openai import BaseModel
from pydantic import Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class LineTravelScraper:
    """
    A scraper for the LINE Travel website using FireCrawl.
    """

    def __init__(self, api_key: str) -> None:
        """
        Initialize the LINE Travel scraper.
        
        Args:
            api_key: FireCrawl API key.
        """
        self.api_key = api_key
        self.crawler = FirecrawlApp(api_key=self.api_key)
        logger.info("FireCrawl client initialized")

    def scrape_journeys(self) -> ScrapeResponse:
        """
        Scrape journey data from LINE Travel website.
        
        Returns:
            Raw data from FireCrawl without any processing.
        """
        url = "https://travel.line.me/journeys?tab=overview"
        logger.info(f"Scraping data from {url}")

        try:
            class TravelInfo(BaseModel):
                title: str = Field(..., description="The title of the recommended travel.")
                country: List[str] = Field(..., description="The countries where the recommended travel goes.")
                city: List[str] = Field(..., description="The cities where the recommended travel goes.")
                # FIXME: broken in FireCrawl currently, it cannot parse and get the valid data which I want
                period: str = Field(..., description="The duration of the recommended travel.")
                # FIXME: broken in FireCrawl currently, it cannot parse and get the valid data which I want
                category: List[str] = Field(..., description="The categories which is a very short and clear description of the recommended travel.")
                url: str = Field(..., description="A reference as URL to the recommended travel.")

            class RecommendedTravelDetails(BaseModel):
                details: List[TravelInfo] = Field(..., description="Recommended travel details from LINE travel blog.")

            json_config = JsonConfig(schema=RecommendedTravelDetails.model_json_schema())
            scrape_result = self.crawler.scrape_url(
                url,
                formats=["markdown", "json"],
                json_options=json_config,
            )

            logger.info("Successfully scraped data with FireCrawl")
            print("===============================")
            print(f"[DEBUG in scrape_journeys] scrape_result: {scrape_result}")
            print("===============================")
            print(f"[DEBUG in scrape_journeys] scrape_result.html: {scrape_result.html}")
            print("===============================")
            print(f"[DEBUG in scrape_journeys] scrape_result.json: {scrape_result.json}")
            print("===============================")
            print(f"[DEBUG in scrape_journeys] scrape_result.markdown: {scrape_result.markdown}")
            return scrape_result
        except Exception as e:
            logger.error(f"Error scraping with FireCrawl: {e}")
            raise

    def save_raw_data_as_md(self, data: ScrapeResponse, tab: str) -> str:
        """
        Save raw FireCrawl data to a JSON file.
        
        Args:
            data: Raw data from FireCrawl.
            tab: Tab name.
            
        Returns:
            Path to the saved file.
        """
        timestamp = Path(__file__).stem + "_" + str(int(Path(__file__).stat().st_mtime))
        filename = f"line_travel_raw_{tab}_{timestamp}.md"

        filepath = Path(__file__).parent / filename

        with open(filepath, "w+", encoding="utf-8") as f:
            f.write(data.markdown)

        logger.info(f"Saved raw data to {filepath}")
        return str(filepath)

    def save_raw_data_as_json(self, data: ScrapeResponse, tab: str) -> str:
        """
        Save raw FireCrawl data to a JSON file.

        Args:
            data: Raw data from FireCrawl.
            tab: Tab name.

        Returns:
            Path to the saved file.
        """
        timestamp = Path(__file__).stem + "_" + str(int(Path(__file__).stat().st_mtime))
        filename = f"line_travel_raw_{tab}_{timestamp}.json"

        filepath = Path(__file__).parent / filename

        with open(filepath, "w+", encoding="utf-8") as f:
            f.write(json.dumps(data.json, ensure_ascii=False, indent=4))

        logger.info(f"Saved raw data to {filepath}")
        return str(filepath)


def main() -> None:
    """Main function to run the scraper."""
    load_dotenv()
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        logger.error("FireCrawl API key is required. Set it in .env file.")
        sys.exit(1)
    
    scraper = LineTravelScraper(api_key=api_key)
    raw_data = scraper.scrape_journeys()
    tab = "overview"
    md_filepath = scraper.save_raw_data_as_md(raw_data, tab=tab)
    json_filepath = scraper.save_raw_data_as_json(raw_data, tab=tab)
    print(f"Raw data as MarkDown saved to: {md_filepath}")
    print(f"Raw data as JSON saved to: {json_filepath}")


if __name__ == "__main__":
    main()
