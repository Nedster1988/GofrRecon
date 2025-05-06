from sources.gun_news import fetch_articles
from datetime import datetime
import feedparser

def parse_date(date_str: str) -> datetime:
    """Parse various date formats into datetime object"""
    try:
        # Try parsing with feedparser's date handler
        parsed = feedparser._parse_date(date_str)
        if parsed:
            return datetime(*parsed[:6])
    except:
        pass
    return datetime.min  # Return earliest date if parsing fails

def main():
    # Fetch articles from all feeds
    articles = fetch_articles()
    
    # Sort articles by publication date (most recent first)
    articles.sort(key=lambda x: parse_date(x['published']), reverse=True)
    
    # Print first 5 articles
    print("\nMost Recent Articles from Gun News Feeds:")
    print("=" * 100)
    
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Published: {article['published']}")
        print(f"   Source: {article['source']}")
        print(f"   Link: {article['link']}")
        print("\n   Summary:")
        print(f"   {article['summary'][:200]}..." if len(article['summary']) > 200 else f"   {article['summary']}")
        print("=" * 100)

if __name__ == "__main__":
    main() 