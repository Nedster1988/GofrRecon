#!/usr/bin/env python3

import logging
from datetime import datetime
import feedparser
from sources.gun_news import fetch_articles
from ai.article_analyzer import analyze_articles
from storage.sheets_manager import SheetsManager

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_date(date_str: str) -> datetime:
    """Parse various date formats into datetime object"""
    try:
        parsed = feedparser._parse_date(date_str)
        if parsed:
            return datetime(*parsed[:6])
    except:
        pass
    return datetime.min

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting GOFR Recon Analysis")

    try:
        # Initialize Google Sheets manager
        sheets_manager = SheetsManager()
        sheets_manager.ensure_headers()
        
        # Fetch articles from all feeds
        articles = fetch_articles()
        
        # Sort articles by publication date (most recent first)
        articles.sort(key=lambda x: parse_date(x['published']), reverse=True)
        
        # Analyze the 5 most recent articles
        analyzed_articles = analyze_articles(articles, max_articles=5)
        
        # Save analyzed articles to Google Sheets
        saved_count, skipped_count = sheets_manager.save_batch_analysis(analyzed_articles)
        logger.info(f"Storage Summary: {saved_count} new articles saved, {skipped_count} duplicates skipped")
        
        # Print results
        print("\nAnalyzed Articles:")
        print("=" * 100)
        
        for i, article in enumerate(analyzed_articles, 1):
            print(f"\n{i}. {article['original_article']['title']}")
            print(f"   Published: {article['original_article']['published']}")
            print(f"   Source: {article['original_article']['source']}")
            print(f"   Link: {article['original_article']['link']}")
            print(f"\n   Category: {article['category']}")
            print(f"   Tags: {', '.join(article['tags'])}")
            print("\n   Summary:")
            print(f"   {article['summary']}")
            print("=" * 100)
            
    except Exception as e:
        logger.error(f"Error in main processing loop: {str(e)}")
        raise

if __name__ == "__main__":
    main() 