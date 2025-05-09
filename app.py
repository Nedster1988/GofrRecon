import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import yaml
import threading
import time
import schedule
import json
import os
from config import Config

AGENTS_CONFIG_PATH = "config/agents.yaml"
INBOX_PATH = "data/agent_inbox.json"

def serialize_article(article):
    # Convert any datetime fields to ISO strings
    article = article.copy()
    if isinstance(article.get('published'), datetime):
        article['published'] = article['published'].isoformat()
    return article

def agent_task(agent):
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(INBOX_PATH), exist_ok=True)
    # Fetch news for the agent's category and keywords
    articles = fetch_news(sources=agent.get('categories', [agent.get('category', 'unknown')]))
    # Filter by keywords if specified
    if agent['keywords']:
        articles = [a for a in articles if any(k.lower() in a['title'].lower() or k.lower() in a.get('content', '').lower() for k in agent['keywords'])]
    # Store findings in inbox
    try:
        with open(INBOX_PATH, "r") as f:
            inbox = json.load(f)
    except Exception:
        inbox = []
    articles = [serialize_article(a) for a in articles]
    inbox.append({
        "agent": agent['name'],
        "categories": agent.get('categories', [agent.get('category', 'unknown')]),
        "timestamp": datetime.now().isoformat(),
        "results": articles
    })
    with open(INBOX_PATH, "w") as f:
        json.dump(inbox, f)

def load_agents():
    try:
        with open(AGENTS_CONFIG_PATH, "r") as f:
            agents = yaml.safe_load(f)
            if not isinstance(agents, list):
                agents = []
            return agents
    except Exception:
        return []

def save_agents(agents):
    with open(AGENTS_CONFIG_PATH, "w") as f:
        yaml.dump(agents, f)

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import our modules
from sources.rss_parser import fetch_news
from ai.summarizer import summarize_news
from utils.deduplicate import deduplicate_stories
from sources.news_manager import NewsSourceManager

# Import new modules
from ai.content_generator import ContentGenerator
from utils.content_poster import ContentPoster

# Initialize news source manager
news_manager = NewsSourceManager()

# Initialize content generator and poster
content_generator = ContentGenerator()
content_poster = ContentPoster(Config())

# Set page configuration
st.set_page_config(
    page_title="Gofr Recon",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 1rem;
        font-size: 1.2rem;
        border-radius: 5px;
        border: none;
        margin: 1rem 0;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .news-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🧠 Gofr Recon")
st.markdown("Real-time news intelligence and analysis")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    # Date range selector
    date_range = st.date_input(
        "Select Date Range",
        value=(datetime.now() - timedelta(days=1), datetime.now()),
        max_value=datetime.now()
    )
    
    # News source management
    st.subheader("News Sources")
    
    # Get all categories
    all_categories = news_manager.get_all_categories()
    
    # Display category checkboxes
    selected_categories = []
    for category_id, info in all_categories.items():
        if st.checkbox(f"{info['name']} ({category_id})", value=True):
            selected_categories.append(category_id)
    
    # Add new category
    st.markdown("---")
    st.subheader("Add New Category")
    
    with st.form("add_category"):
        new_category_id = st.text_input("Category ID (e.g., 'finance')")
        new_category_name = st.text_input("Category Name (e.g., 'Finance News')")
        new_category_desc = st.text_area("Description")
        new_feeds = st.text_area("RSS Feeds (one per line)")
        
        if st.form_submit_button("Add Category"):
            if new_category_id and new_category_name and new_feeds:
                feeds_list = [feed.strip() for feed in new_feeds.split('\n') if feed.strip()]
                news_manager.add_custom_category(
                    new_category_id,
                    new_category_name,
                    new_category_desc,
                    feeds_list
                )
                st.success("Category added successfully!")
                st.rerun()
    
    # Manage existing categories
    st.markdown("---")
    st.subheader("Manage Categories")
    
    for category_id, info in all_categories.items():
        with st.expander(f"Edit {info['name']}"):
            current_feeds = "\n".join(info['feeds'])
            new_feeds = st.text_area("RSS Feeds", current_feeds, key=f"edit_{category_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update", key=f"update_{category_id}"):
                    feeds_list = [feed.strip() for feed in new_feeds.split('\n') if feed.strip()]
                    news_manager.update_category_feeds(category_id, feeds_list)
                    st.success("Category updated!")
                    st.rerun()
            
            with col2:
                if category_id in (news_manager.config.get("custom_categories") or {}):
                    if st.button("Delete", key=f"delete_{category_id}"):
                        news_manager.remove_custom_category(category_id)
                        st.success("Category deleted!")
                        st.rerun()
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Gofr Recon provides real-time news intelligence and analysis using AI-powered summarization.")

    st.markdown("---")
    st.header("Recon Agents")

    agents = load_agents()

    with st.form("add_agent_form"):
        agent_name = st.text_input("Agent Name")
        agent_categories = st.multiselect("Categories", list(all_categories.keys()))
        agent_keywords = st.text_input("Keywords (comma-separated)")
        agent_frequency_min = st.number_input("Frequency (minutes)", min_value=0, max_value=1440, value=0, help="Set to 0 to disable minute-based scheduling.")
        agent_frequency_hr = st.number_input("Frequency (hours)", min_value=0, max_value=168, value=6, help="Set to 0 to disable hour-based scheduling.")
        if st.form_submit_button("Add Agent"):
            new_agent = {
                "name": agent_name,
                "categories": agent_categories,
                "keywords": [k.strip() for k in agent_keywords.split(",") if k.strip()],
                "frequency_minutes": int(agent_frequency_min),
                "frequency_hours": int(agent_frequency_hr),
                "enabled": True  # New agents are enabled by default
            }
            agents.append(new_agent)
            save_agents(agents)
            st.success("Agent added!")
            st.rerun()

    st.subheader("Existing Agents")
    if agents:
        for idx, agent in enumerate(agents):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{agent['name']}** | Categories: {', '.join(agent.get('categories', [agent.get('category', 'unknown')]))} | Every {agent['frequency_hours']}h")
                st.markdown(f"Keywords: {', '.join(agent['keywords']) if agent['keywords'] else 'None'}")
            with col2:
                if st.button("🔄" if agent['enabled'] else "⏸️", key=f"toggle_agent_{idx}", help="Toggle agent status"):
                    agents[idx]['enabled'] = not agents[idx]['enabled']
                    save_agents(agents)
                    st.success(f"Agent {'enabled' if agents[idx]['enabled'] else 'disabled'}!")
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"delete_agent_{idx}", help="Delete agent"):
                    agents.pop(idx)
                    save_agents(agents)
                    st.success("Agent deleted!")
                    st.rerun()
            st.markdown("---")
    else:
        st.info("No agents configured yet.")

# Main content area
st.header("News Intelligence Dashboard")

# Agent Inbox Section
st.subheader("Agent Inbox")

if st.button("Run Agents Now", use_container_width=True):
    agents = load_agents()
    for agent in agents:
        if agent.get('enabled'):
            agent_task(agent)
    st.success("All enabled agents have run.")
    st.rerun()

try:
    with open(INBOX_PATH, "r") as f:
        inbox = json.load(f)
except Exception:
    inbox = []
if inbox:
    for entry in reversed(inbox[-10:]):  # Show last 10 agent runs
        st.markdown(f"**Agent:** {entry['agent']} | **Categories:** {', '.join(entry.get('categories', [entry.get('category', 'unknown')]))} | **Time:** {entry['timestamp']}")
        for article in entry['results'][:3]:  # Show up to 3 articles per run
            st.markdown(f"- [{article['title']}]({article['url']})")
        st.markdown("---")
else:
    st.info("No agent findings yet.")

# Add Content Generation section after Agent Inbox section
st.markdown("---")
st.header("Content Generation")

# Load agent inbox
try:
    with open(INBOX_PATH, "r") as f:
        inbox = json.load(f)
except Exception:
    inbox = []

if inbox:
    st.subheader("Agent Findings")
    
    # Select agent findings to generate content from
    selected_findings = []
    for finding in inbox:
        if st.checkbox(f"{finding['agent']} - {finding['timestamp']}", key=f"finding_{finding['timestamp']}"):
            selected_findings.append(finding)
    
    if selected_findings:
        if st.button("Generate Content"):
            with st.spinner("Generating content..."):
                # Generate content for selected findings
                generated_content = content_generator.generate_batch_content(selected_findings)
                
                # Display generated content
                st.subheader("Generated Content")
                for content in generated_content:
                    with st.expander(f"Content for {content['agent']}"):
                        st.write("**Title:**")
                        st.write(content['title'])
                        st.write("**Content:**")
                        st.write(content['content'])
                        st.write("**Hashtags:**")
                        st.write(content['hashtags'])
                        st.write("**Call to Action:**")
                        st.write(content['cta'])
                        
                        # Post content section
                        st.subheader("Post Content")
                        platforms = st.multiselect(
                            "Select platforms to post to",
                            ["Twitter", "LinkedIn", "Facebook"],
                            key=f"platforms_{content['agent']}"
                        )
                        
                        if platforms and st.button("Post Content", key=f"post_{content['agent']}"):
                            with st.spinner("Posting content..."):
                                result = content_poster.post_content(content, platforms)
                                if result['success']:
                                    st.success("Content posted successfully!")
                                else:
                                    st.error(f"Error posting content: {result['error']}")
else:
    st.info("No agent findings available. Run some agents first to generate content.")

# Add Content History section
st.markdown("---")
st.header("Posted Content History")

# Display posting history
history = content_poster.get_posting_history()
if history:
    for post in history:
        with st.expander(f"{post['title']} - {post['timestamp']}"):
            st.write("**Platforms:**")
            st.write(", ".join(post['platforms']))
            st.write("**Content:**")
            st.write(post['content'])
else:
    st.info("No content has been posted yet.")

# Run Recon button
if st.button("🚀 Run Recon", use_container_width=True):
    with st.spinner("Gathering and analyzing news..."):
        try:
            # Fetch news from selected categories
            articles = fetch_news(
                sources=selected_categories,
                start_date=datetime.combine(date_range[0], datetime.min.time()),
                end_date=datetime.combine(date_range[1], datetime.max.time())
            )
            
            # Deduplicate stories
            unique_stories = deduplicate_stories(articles)
            
            # Summarize news
            summarized_news = summarize_news(unique_stories)
            
            # Display results
            st.success(f"✅ Analysis complete! Found {len(summarized_news)} unique articles.")
            
            # Display summarized news in cards
            for story in summarized_news:
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <h3>{story['title']}</h3>
                        <p><strong>Source:</strong> {story['source']}</p>
                        <p><strong>Published:</strong> {story['published']}</p>
                        <p><strong>Category:</strong> {story['category']}</p>
                        <p><strong>Preview:</strong> {story.get('content', '')[:200]}...</p>
                        <p>{story['summary']}</p>
                        <a href="{story['url']}" target="_blank">Read more</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Gofr Recon | Powered by Streamlit and OpenAI")

def run_scheduler():
    agents = load_agents()
    for agent in agents:
        if agent.get('enabled'):
            if agent.get('frequency_minutes', 0) > 0:
                schedule.every(int(agent['frequency_minutes'])).minutes.do(agent_task, agent)
            elif agent.get('frequency_hours', 0) > 0:
                schedule.every(int(agent['frequency_hours'])).hours.do(agent_task, agent)
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_scheduler_once():
    if not hasattr(st.session_state, "scheduler_started"):
        t = threading.Thread(target=run_scheduler, daemon=True)
        t.start()
        st.session_state.scheduler_started = True

# Start the agent scheduler in the background
start_scheduler_once() 