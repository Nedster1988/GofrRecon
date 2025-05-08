import os
from typing import List, Dict, Any
from datetime import datetime
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
except Exception as e:
    print(f"Warning: OpenAI API key not found. Running in mock mode. Error: {str(e)}")

def get_mock_summary(article: Dict[str, Any]) -> str:
    """Generate a mock summary for testing without OpenAI API."""
    title = article['title']
    content = article['content']
    
    # Simple mock summaries based on content length
    if len(content) < 100:
        return f"Brief update: {content}"
    else:
        # Take first sentence and add a generic ending
        first_sentence = content.split('.')[0] + '.'
        return f"{first_sentence} This development could have significant implications for the industry."

def summarize_with_openai(article: Dict[str, Any]) -> str:
    """Summarize an article using OpenAI's API."""
    try:
        # Prepare the prompt
        prompt = f"""Please provide a concise summary of the following news article:

Title: {article['title']}
Content: {article['content']}

Provide a 2-3 sentence summary that captures the key points and implications."""

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles concisely and professionally."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        return get_mock_summary(article)

def summarize_news(articles: List[Dict[str, Any]], use_mock: bool = False) -> List[Dict[str, Any]]:
    """
    Summarize a list of news articles.
    
    Args:
        articles: List of news articles to summarize
        use_mock: If True, use mock summaries instead of OpenAI API
        
    Returns:
        List of articles with added summaries
    """
    summarized_articles = []
    
    for article in articles:
        # Create a copy of the article to avoid modifying the original
        summarized_article = article.copy()
        
        # Generate summary
        if use_mock or not openai.api_key:
            summary = get_mock_summary(article)
        else:
            summary = summarize_with_openai(article)
        
        # Add summary to the article
        summarized_article['summary'] = summary
        summarized_articles.append(summarized_article)
    
    return summarized_articles

if __name__ == "__main__":
    # Test the summarizer with a sample article
    test_article = {
        "title": "OpenAI Announces GPT-5 Development",
        "url": "https://example.com/openai-gpt5",
        "source": "Tech Daily",
        "published": datetime.now(),
        "content": "OpenAI has officially announced the development of GPT-5, promising significant improvements in reasoning and multimodal capabilities. The new model is expected to be released in late 2024.",
        "category": "AI"
    }
    
    # Test both mock and real summarization
    print("Testing mock summarization:")
    mock_summary = get_mock_summary(test_article)
    print(f"Mock Summary: {mock_summary}\n")
    
    print("Testing OpenAI summarization (if API key is available):")
    real_summary = summarize_with_openai(test_article)
    print(f"OpenAI Summary: {real_summary}") 