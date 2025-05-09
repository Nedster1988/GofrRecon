import logging
from typing import Dict, Any, List
import json
import os
from datetime import datetime

class ContentPoster:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.posted_content_path = "data/posted_content.json"
        
    def _load_posted_content(self) -> List[Dict[str, Any]]:
        """Load previously posted content from file"""
        try:
            if os.path.exists(self.posted_content_path):
                with open(self.posted_content_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Error loading posted content: {str(e)}")
            return []
            
    def _save_posted_content(self, content: List[Dict[str, Any]]):
        """Save posted content to file"""
        try:
            os.makedirs(os.path.dirname(self.posted_content_path), exist_ok=True)
            with open(self.posted_content_path, 'w') as f:
                json.dump(content, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving posted content: {str(e)}")
            
    def format_for_platform(self, content: Dict[str, Any], platform: str) -> str:
        """
        Format content for specific platform
        
        Args:
            content: Dictionary containing post content
            platform: Target platform (e.g., 'twitter', 'linkedin', 'facebook')
            
        Returns:
            Formatted content string
        """
        if platform == 'twitter':
            # Twitter has 280 character limit
            post = f"{content['title']}\n\n{content['content'][:200]}...\n\n"
            post += " ".join(content['hashtags'][:3])  # Limit hashtags
            post += f"\n\n{content['cta']}"
            return post[:280]  # Ensure we don't exceed limit
            
        elif platform == 'linkedin':
            # LinkedIn allows longer posts
            post = f"{content['title']}\n\n{content['content']}\n\n"
            post += " ".join(content['hashtags'])
            post += f"\n\n{content['cta']}"
            return post
            
        elif platform == 'facebook':
            # Facebook allows long posts
            post = f"{content['title']}\n\n{content['content']}\n\n"
            post += " ".join(content['hashtags'])
            post += f"\n\n{content['cta']}"
            return post
            
        else:
            raise ValueError(f"Unsupported platform: {platform}")
            
    def post_content(self, content: Dict[str, Any], platforms: List[str] = None) -> Dict[str, Any]:
        """
        Post content to specified platforms
        
        Args:
            content: Dictionary containing post content
            platforms: List of platforms to post to (default: all configured platforms)
            
        Returns:
            Dictionary containing posting results
        """
        if platforms is None:
            platforms = ['twitter', 'linkedin', 'facebook']  # Default platforms
            
        results = {
            'content_id': f"{content['agent']}_{datetime.now().isoformat()}",
            'platforms': {}
        }
        
        # Load previously posted content
        posted_content = self._load_posted_content()
        
        # Post to each platform
        for platform in platforms:
            try:
                formatted_content = self.format_for_platform(content, platform)
                
                # TODO: Implement actual platform posting logic here
                # This would involve platform-specific API calls
                
                results['platforms'][platform] = {
                    'status': 'success',
                    'formatted_content': formatted_content
                }
                
            except Exception as e:
                self.logger.error(f"Error posting to {platform}: {str(e)}")
                results['platforms'][platform] = {
                    'status': 'error',
                    'error': str(e)
                }
                
        # Save to posted content history
        posted_content.append({
            'content_id': results['content_id'],
            'original_content': content,
            'posting_results': results,
            'timestamp': datetime.now().isoformat()
        })
        self._save_posted_content(posted_content)
        
        return results
        
    def get_posting_history(self) -> List[Dict[str, Any]]:
        """Get history of posted content"""
        return self._load_posted_content() 