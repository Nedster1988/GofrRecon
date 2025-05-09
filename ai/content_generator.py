import logging
import openai
from typing import Dict, Any, List
from config import Config

class ContentGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        openai.api_key = self.config.openai_api_key

    def generate_post_content(self, agent_findings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate postable content from agent findings
        
        Args:
            agent_findings: Dictionary containing agent's findings including articles and metadata
            
        Returns:
            Dictionary containing:
            - title: Post title
            - content: Formatted post content
            - tags: Relevant tags
            - category: Content category
        """
        try:
            # Prepare the prompt for content generation
            articles_text = "\n\n".join([
                f"Article {i+1}:\nTitle: {article['title']}\nSummary: {article.get('summary', '')}\n"
                f"Category: {article.get('category', 'Unknown')}\nTags: {', '.join(article.get('tags', []))}"
                for i, article in enumerate(agent_findings['results'])
            ])

            prompt = f"""Create a social media post based on these recent findings from the {agent_findings['agent']} agent.
The post should be engaging, informative, and suitable for sharing on social media.

Findings:
{articles_text}

Please provide:
1. An attention-grabbing title
2. The main post content (2-3 paragraphs)
3. Relevant hashtags
4. A call to action

Format the response as:
TITLE: [your title here]
CONTENT: [your content here]
HASHTAGS: [comma-separated hashtags]
CTA: [call to action]"""

            # Call GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional social media content creator specializing in news and analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Extract components
            title = ""
            post_content = ""
            hashtags = []
            cta = ""
            
            for line in content.split('\n'):
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('CONTENT:'):
                    post_content = line.replace('CONTENT:', '').strip()
                elif line.startswith('HASHTAGS:'):
                    hashtags = [tag.strip() for tag in line.replace('HASHTAGS:', '').split(',')]
                elif line.startswith('CTA:'):
                    cta = line.replace('CTA:', '').strip()

            # Create the result dictionary
            result = {
                'title': title,
                'content': post_content,
                'hashtags': hashtags,
                'cta': cta,
                'source_articles': agent_findings['results'],
                'agent': agent_findings['agent'],
                'timestamp': agent_findings['timestamp']
            }
            
            self.logger.info(f"Successfully generated content for agent {agent_findings['agent']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return {
                'title': "Error generating content",
                'content': "There was an error generating the post content.",
                'hashtags': [],
                'cta': "Please check the logs for details.",
                'source_articles': agent_findings['results'],
                'agent': agent_findings['agent'],
                'timestamp': agent_findings['timestamp']
            }

    def generate_batch_content(self, agent_findings_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate content for multiple agent findings
        
        Args:
            agent_findings_list: List of agent findings dictionaries
            
        Returns:
            List of generated content dictionaries
        """
        self.logger.info(f"Starting batch content generation for {len(agent_findings_list)} agent findings")
        generated_content = []
        
        for findings in agent_findings_list:
            result = self.generate_post_content(findings)
            generated_content.append(result)
            
        self.logger.info(f"Completed batch content generation")
        return generated_content 