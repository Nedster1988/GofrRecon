import logging
import openai
from typing import Dict, Any, List
from config import Config

class ArticleAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        openai.api_key = self.config.openai_api_key
        
    def summarize_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an article using GPT-4 to generate summary, classification, and tags
        
        Args:
            article: Dictionary containing article details (title, summary, link, published)
            
        Returns:
            Dictionary containing:
            - summary: Concise summary of the article
            - category: One of [Law, Product, Case, Political, Opinion, Research]
            - tags: List of relevant tags (gun models, states, case names, etc.)
        """
        try:
            # Prepare the prompt
            prompt = f"""Analyze this gun-related article and provide:
1. A concise 2-3 sentence summary
2. A single category from: Law, Product, Case, Political, Opinion, Research
3. A list of relevant tags (gun models, states, case names, etc.)

Article Title: {article['title']}
Article Summary: {article['summary']}
Article Link: {article['link']}
Published: {article['published']}

Provide the response in this exact format:
SUMMARY: [your summary here]
CATEGORY: [single category]
TAGS: [comma-separated list of tags]"""

            # Call GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert analyst of gun-related news and articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=500
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Extract summary, category, and tags
            summary = ""
            category = ""
            tags = []
            
            for line in content.split('\n'):
                if line.startswith('SUMMARY:'):
                    summary = line.replace('SUMMARY:', '').strip()
                elif line.startswith('CATEGORY:'):
                    category = line.replace('CATEGORY:', '').strip()
                elif line.startswith('TAGS:'):
                    tags = [tag.strip() for tag in line.replace('TAGS:', '').split(',')]
            
            # Create the result dictionary
            result = {
                'summary': summary,
                'category': category,
                'tags': tags,
                'original_article': article
            }
            
            self.logger.info(f"Successfully analyzed article: {article['title']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing article {article.get('title', 'Unknown')}: {str(e)}")
            return {
                'summary': "Error generating summary",
                'category': "Unknown",
                'tags': [],
                'original_article': article
            }
            
    def analyze_articles(self, articles: List[Dict[str, Any]], max_articles: int = 5) -> List[Dict[str, Any]]:
        """
        Analyze multiple articles in batch
        
        Args:
            articles: List of article dictionaries
            max_articles: Maximum number of articles to analyze (default: 5)
            
        Returns:
            List of analyzed article dictionaries
        """
        self.logger.info(f"Starting batch analysis of {min(len(articles), max_articles)} articles")
        analyzed_articles = []
        
        for i, article in enumerate(articles[:max_articles]):
            self.logger.info(f"Analyzing article {i+1}/{min(len(articles), max_articles)}: {article['title']}")
            result = self.summarize_article(article)
            analyzed_articles.append(result)
            
        self.logger.info(f"Completed batch analysis of {len(analyzed_articles)} articles")
        return analyzed_articles

def analyze_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze an article without instantiating the class
    """
    analyzer = ArticleAnalyzer()
    return analyzer.summarize_article(article)

def analyze_articles(articles: List[Dict[str, Any]], max_articles: int = 5) -> List[Dict[str, Any]]:
    """
    Convenience function to analyze multiple articles without instantiating the class
    """
    analyzer = ArticleAnalyzer()
    return analyzer.analyze_articles(articles, max_articles) 