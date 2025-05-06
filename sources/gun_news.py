import logging
import feedparser
from datetime import datetime
from typing import List, Dict, Any

# List of gun news RSS feeds
GUN_NEWS_FEEDS = [
    "https://www.thetruthaboutguns.com/feed/",
    "https://www.guns.com/feed/",
    "https://www.ammoland.com/feed/",
    "https://www.gunsamerica.com/blog/feed/",
    "https://www.thefirearmblog.com/blog/feed/",
    "https://www.recoilweb.com/feed",
    "https://www.gunsweek.com/en/feed",
    "https://www.shootingillustrated.com/feed/",
    "https://www.americanrifleman.org/feed/",
    "https://www.gunsandammo.com/feed/"
]

class GunNewsFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def fetch_articles(self) -> List[Dict[str, Any]]:
        """
        Fetch articles from all configured gun news RSS feeds
        Returns a list of dictionaries containing article information
        """
        all_articles = []
        
        for feed_url in GUN_NEWS_FEEDS:
            try:
                self.logger.info(f"Fetching feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Extract published date, handling different date formats
                    published = entry.get('published', '')
                    if not published:
                        published = entry.get('updated', '')
                    
                    # Extract summary/description
                    summary = entry.get('summary', '')
                    if not summary:
                        summary = entry.get('description', '')
                    
                    article = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': summary,
                        'published': published,
                        'source': feed_url,
                        'fetched_at': datetime.now().isoformat()
                    }
                    all_articles.append(article)
                    
            except Exception as e:
                self.logger.error(f"Error fetching feed {feed_url}: {str(e)}")
                continue
                
        self.logger.info(f"Fetched {len(all_articles)} articles from {len(GUN_NEWS_FEEDS)} feeds")
        return all_articles

def fetch_articles() -> List[Dict[str, Any]]:
    """
    Convenience function to fetch articles without instantiating the class
    """
    fetcher = GunNewsFetcher()
    return fetcher.fetch_articles() 