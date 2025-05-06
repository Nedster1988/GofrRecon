import logging
import json
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta

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