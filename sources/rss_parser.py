import logging
import feedparser
from datetime import datetime
from typing import List, Dict, Any

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