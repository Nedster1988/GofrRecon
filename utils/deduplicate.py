import logging
import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
import hashlib

class Deduplicator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache_file = config.cache_file
        self._ensure_cache_file()
        
    def _ensure_cache_file(self):
        """Ensure the cache file exists"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'w') as f:
                json.dump([], f)
                
    def _load_cache(self) -> List[Dict[str, Any]]:
        """Load the cache of processed items"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading cache: {str(e)}")
            return []
            
    def _save_cache(self, items: List[Dict[str, Any]]):
        """Save items to the cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(items, f)
        except Exception as e:
            self.logger.error(f"Error saving cache: {str(e)}")
            
    def _is_duplicate(self, item: Dict[str, Any], cache: List[Dict[str, Any]]) -> bool:
        """Check if an item is a duplicate"""
        for cached_item in cache:
            if item['link'] == cached_item['link']:
                return True
        return False
        
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process items and remove duplicates
        Returns only new items that haven't been processed before
        """
        cache = self._load_cache()
        new_items = []
        
        for item in items:
            if not self._is_duplicate(item, cache):
                new_items.append(item)
                cache.append(item)
                
        if new_items:
            self._save_cache(cache)
            self.logger.info(f"Found {len(new_items)} new items")
            
        return new_items 

def deduplicate_stories(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate news articles based on content similarity.
    
    Args:
        articles: List of news articles to deduplicate
        
    Returns:
        List of unique articles
    """
    # Create a set to store unique content hashes
    seen_hashes = set()
    unique_articles = []
    
    for article in articles:
        # Create a hash of the title and first 100 characters of content
        content_to_hash = f"{article['title']}{article['content'][:100]}"
        content_hash = hashlib.md5(content_to_hash.encode()).hexdigest()
        
        # If we haven't seen this content before, add it to our results
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_articles.append(article)
    
    return unique_articles

if __name__ == "__main__":
    # Test the deduplication with sample data
    test_articles = [
        {
            "title": "Test Article 1",
            "content": "This is a test article",
            "source": "Test Source",
            "published": datetime.now()
        },
        {
            "title": "Test Article 1",  # Duplicate title
            "content": "This is a test article",  # Duplicate content
            "source": "Different Source",
            "published": datetime.now()
        },
        {
            "title": "Test Article 2",
            "content": "This is a different article",
            "source": "Test Source",
            "published": datetime.now()
        }
    ]
    
    unique = deduplicate_stories(test_articles)
    print(f"Original articles: {len(test_articles)}")
    print(f"Unique articles: {len(unique)}") 