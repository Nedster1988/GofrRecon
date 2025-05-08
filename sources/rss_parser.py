import logging
import feedparser
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define some common tech and security news RSS feeds
DEFAULT_FEEDS = {
    "tech": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss"
    ],
    "security": [
        "https://krebsonsecurity.com/feed/",
        "https://www.bleepingcomputer.com/feed/",
        "https://www.darkreading.com/rss.xml"
    ],
    "ai": [
        "https://www.artificialintelligence-news.com/feed/",
        "https://www.unite.ai/feed/",
        "https://www.analyticsinsight.net/feed/"
    ]
}

def clean_html_content(html_content: str) -> str:
    """Clean HTML content and extract text."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        logger.error(f"Error cleaning HTML content: {str(e)}")
        return html_content

def parse_feed_entry(entry: Dict[str, Any], source_url: str) -> Dict[str, Any]:
    """Parse a single feed entry into our standard format."""
    try:
        # Get the domain name for the source
        domain = urlparse(source_url).netloc
        
        # Extract content
        content = entry.get('content', [{'value': ''}])[0].get('value', '')
        if not content:
            content = entry.get('summary', '')
        
        # Clean the content
        content = clean_html_content(content)
        
        # Parse published date
        published = entry.get('published_parsed', None)
        if published:
            published = datetime(*published[:6])
        else:
            published = datetime.now()
        
        return {
            "title": entry.get('title', 'No Title'),
            "url": entry.get('link', ''),
            "source": domain,
            "published": published,
            "content": content,
            "category": next((cat for cat, urls in DEFAULT_FEEDS.items() if source_url in urls), "other")
        }
    except Exception as e:
        logger.error(f"Error parsing feed entry: {str(e)}")
        return None

def fetch_news(
    sources: List[str] = None,
    start_date: datetime = None,
    end_date: datetime = None,
    custom_feeds: Dict[str, List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch news articles from RSS feeds.
    
    Args:
        sources: List of source categories to fetch (e.g., ['tech', 'security', 'ai'])
        start_date: Start date for filtering articles
        end_date: End date for filtering articles
        custom_feeds: Dictionary of custom feed URLs to add to the default feeds
        
    Returns:
        List of news articles with title, url, source, published date, and content
    """
    # Combine default and custom feeds
    all_feeds = DEFAULT_FEEDS.copy()
    if custom_feeds:
        for category, urls in custom_feeds.items():
            all_feeds.setdefault(category, []).extend(urls)
    
    # If no sources specified, use all available
    if not sources:
        sources = list(all_feeds.keys())
    
    articles = []
    
    # Fetch from each feed
    for category in sources:
        if category not in all_feeds:
            logger.warning(f"Unknown category: {category}")
            continue
            
        for feed_url in all_feeds[category]:
            try:
                logger.info(f"Fetching feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:  # Check for feed parsing errors
                    logger.warning(f"Feed parsing error for {feed_url}: {feed.bozo_exception}")
                    continue
                
                for entry in feed.entries:
                    article = parse_feed_entry(entry, feed_url)
                    if article:
                        articles.append(article)
                        
            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {str(e)}")
                continue
    
    # Filter by date if specified
    if start_date or end_date:
        filtered_articles = []
        for article in articles:
            if start_date and article['published'] < start_date:
                continue
            if end_date and article['published'] > end_date:
                continue
            filtered_articles.append(article)
        articles = filtered_articles
    
    # Sort by published date (newest first)
    articles.sort(key=lambda x: x['published'], reverse=True)
    
    return articles

class RSSParser:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def fetch_items(self) -> List[Dict[str, Any]]:
        """
        Fetch items from all configured RSS feeds
        Returns a list of dictionaries containing feed items
        """
        all_items = []
        
        for feed_url in self.config.rss_feeds:
            try:
                self.logger.info(f"Fetching feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    item = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', ''),
                        'content': entry.get('content', [{'value': ''}])[0]['value'],
                        'source': feed_url,
                        'fetched_at': datetime.now().isoformat()
                    }
                    all_items.append(item)
                    
            except Exception as e:
                self.logger.error(f"Error fetching feed {feed_url}: {str(e)}")
                continue
                
        return all_items 

if __name__ == "__main__":
    # Test the RSS parser
    print("Testing RSS feed fetching...")
    articles = fetch_news(sources=['tech', 'security'])
    print(f"\nFetched {len(articles)} articles")
    
    # Display first 3 articles
    for article in articles[:3]:
        print(f"\nTitle: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Published: {article['published']}")
        print(f"Category: {article['category']}")
        print(f"Content preview: {article['content'][:200]}...") 