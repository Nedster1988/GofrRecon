import logging
import openai
from typing import List, Dict, Any

class Summarizer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        openai.api_key = config.openai_api_key
        
    def process(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of items and generate summaries using OpenAI
        """
        summarized_items = []
        
        for item in items:
            try:
                # Prepare the content for summarization
                content = f"Title: {item['title']}\n\nContent: {item['content']}"
                
                # Generate summary using OpenAI
                response = openai.ChatCompletion.create(
                    model=self.config.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes content concisely."},
                        {"role": "user", "content": f"Please summarize the following content in 2-3 sentences:\n\n{content}"}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                # Extract the summary from the response
                summary = response.choices[0].message.content.strip()
                
                # Add summary to the item
                item['ai_summary'] = summary
                summarized_items.append(item)
                
            except Exception as e:
                self.logger.error(f"Error summarizing item {item.get('title', 'Unknown')}: {str(e)}")
                item['ai_summary'] = "Error generating summary"
                summarized_items.append(item)
                
        return summarized_items 