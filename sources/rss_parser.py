import logging
import feedparser
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

# Mock RSS feed data
MOCK_FEEDS = {
    "tech": [
        {
            "title": "OpenAI Announces GPT-5 Development",
            "url": "https://example.com/openai-gpt5",
            "source": "Tech Daily",
            "published": datetime.now() - timedelta(hours=2),
            "content": "OpenAI has officially announced the development of GPT-5, promising significant improvements in reasoning and multimodal capabilities. The new model is expected to be released in late 2024.",
            "category": "AI"
        },
        {
            "title": "Microsoft Unveils New AI Copilot Features",
            "url": "https://example.com/microsoft-copilot",
            "source": "Tech Insider",
            "published": datetime.now() - timedelta(hours=5),
            "content": "Microsoft has expanded its AI Copilot capabilities across its product suite, introducing new features for developers and enterprise users. The update includes enhanced code generation and documentation tools.",
            "category": "AI"
        }
    ],
    "security": [
        {
            "title": "Major Cloud Provider Suffers Data Breach",
            "url": "https://example.com/cloud-breach",
            "source": "Security Weekly",
            "published": datetime.now() - timedelta(hours=1),
            "content": "A leading cloud service provider has reported a significant data breach affecting thousands of enterprise customers. The incident appears to be related to a sophisticated supply chain attack.",
            "category": "Cybersecurity"
        },
        {
            "title": "New Zero-Day Vulnerability Found in Popular Framework",
            "url": "https://example.com/zero-day",
            "source": "Security News",
            "published": datetime.now() - timedelta(hours=3),
            "content": "Security researchers have discovered a critical zero-day vulnerability in a widely used web framework. The flaw could allow remote code execution and affects multiple versions.",
            "category": "Vulnerabilities"
        }
    ],
    "business": [
        {
            "title": "Tech Giant Acquires AI Startup for $500M",
            "url": "https://example.com/tech-acquisition",
            "source": "Business Insider",
            "published": datetime.now() - timedelta(hours=4),
            "content": "A major technology company has acquired an AI startup specializing in natural language processing for $500 million. The deal is expected to accelerate the company's AI initiatives.",
            "category": "M&A"
        },
        {
            "title": "New AI Regulations Proposed in EU",
            "url": "https://example.com/ai-regulations",
            "source": "Business Times",
            "published": datetime.now() - timedelta(hours=6),
            "content": "The European Union has proposed new regulations governing the development and deployment of artificial intelligence systems. The framework aims to balance innovation with safety and ethical considerations.",
            "category": "Regulation"
        }
    ]
}

def fetch_news(
    sources: List[str] = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> List[Dict[str, Any]]:
    """
    Fetch news articles from RSS feeds (currently returns mock data).
    
    Args:
        sources: List of source categories to fetch (e.g., ['tech', 'security', 'business'])
        start_date: Start date for filtering articles
        end_date: End date for filtering articles
        
    Returns:
        List of news articles with title, url, source, published date, and content
    """
    # If no sources specified, use all available
    if not sources:
        sources = list(MOCK_FEEDS.keys())
    
    # Collect articles from specified sources
    articles = []
    for source in sources:
        if source in MOCK_FEEDS:
            articles.extend(MOCK_FEEDS[source])
    
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
    # Test the function
    articles = fetch_news()
    print(f"Fetched {len(articles)} articles")
    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Published: {article['published']}")
        print(f"Category: {article['category']}") 