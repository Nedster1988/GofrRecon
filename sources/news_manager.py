import yaml
import os
from typing import Dict, List, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class NewsSourceManager:
    def __init__(self, config_path: str = "config/news_sources.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load the news sources configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                if not isinstance(config, dict):
                    # If YAML is empty or not a dict, use default structure
                    config = {"default_categories": {}, "custom_categories": {}}
                return config
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            return {"default_categories": {}, "custom_categories": {}}
    
    def _save_config(self):
        """Save the current configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving config file: {str(e)}")
    
    def get_all_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all categories (both default and custom)."""
        all_categories = {}
        all_categories.update(self.config.get("default_categories", {}))
        all_categories.update(self.config.get("custom_categories", {}))
        return all_categories
    
    def get_category_info(self, category_id: str) -> Dict[str, Any]:
        """Get information about a specific category."""
        all_categories = self.get_all_categories()
        return all_categories.get(category_id, {})
    
    def add_custom_category(self, category_id: str, name: str, description: str, feeds: List[str]):
        """Add a new custom category."""
        if not self.config.get("custom_categories"):
            self.config["custom_categories"] = {}
            
        self.config["custom_categories"][category_id] = {
            "name": name,
            "description": description,
            "feeds": feeds
        }
        self._save_config()
    
    def update_category_feeds(self, category_id: str, feeds: List[str]):
        """Update the feeds for a category."""
        all_categories = self.get_all_categories()
        if category_id in all_categories:
            if category_id in self.config.get("default_categories", {}):
                # Create a custom category with the same name if it's a default category
                category_info = self.config["default_categories"][category_id]
                self.add_custom_category(
                    category_id,
                    category_info["name"],
                    category_info["description"],
                    feeds
                )
            else:
                self.config["custom_categories"][category_id]["feeds"] = feeds
                self._save_config()
    
    def remove_custom_category(self, category_id: str):
        """Remove a custom category."""
        if category_id in self.config.get("custom_categories", {}):
            del self.config["custom_categories"][category_id]
            self._save_config()
    
    def get_feeds_for_category(self, category_id: str) -> List[str]:
        """Get all feeds for a specific category."""
        category_info = self.get_category_info(category_id)
        return category_info.get("feeds", [])
    
    def get_all_feeds(self) -> Dict[str, List[str]]:
        """Get all feeds organized by category."""
        return {
            category_id: category_info["feeds"]
            for category_id, category_info in self.get_all_categories().items()
        }

if __name__ == "__main__":
    # Test the news source manager
    manager = NewsSourceManager()
    
    # Print all categories
    print("Available categories:")
    for category_id, info in manager.get_all_categories().items():
        print(f"\n{info['name']} ({category_id})")
        print(f"Description: {info['description']}")
        print(f"Number of feeds: {len(info['feeds'])}")
    
    # Example of adding a custom category
    print("\nAdding custom category...")
    manager.add_custom_category(
        "healthcare",
        "Healthcare",
        "Healthcare industry news and updates",
        [
            "https://example.com/healthcare/feed",
            "https://another-healthcare-news.com/rss"
        ]
    )
    
    # Print updated categories
    print("\nUpdated categories:")
    for category_id, info in manager.get_all_categories().items():
        print(f"\n{info['name']} ({category_id})")
        print(f"Description: {info['description']}")
        print(f"Number of feeds: {len(info['feeds'])}") 