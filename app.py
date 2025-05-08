import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import yaml

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import our modules
from sources.rss_parser import fetch_news
from ai.summarizer import summarize_news
from utils.deduplicate import deduplicate_stories
from sources.news_manager import NewsSourceManager

# Initialize news source manager
news_manager = NewsSourceManager()

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
        agent_category = st.selectbox("Category", list(all_categories.keys()))
        agent_keywords = st.text_input("Keywords (comma-separated)")
        agent_frequency = st.number_input("Frequency (hours)", min_value=1, max_value=168, value=6)
        agent_enabled = st.checkbox("Enabled", value=True)
        if st.form_submit_button("Add Agent"):
            new_agent = {
                "name": agent_name,
                "category": agent_category,
                "keywords": [k.strip() for k in agent_keywords.split(",") if k.strip()],
                "frequency_hours": agent_frequency,
                "enabled": agent_enabled
            }
            agents.append(new_agent)
            save_agents(agents)
            st.success("Agent added!")
            st.rerun()

    st.subheader("Existing Agents")
    if agents:
        for idx, agent in enumerate(agents):
            st.markdown(f"**{agent['name']}** | Category: {agent['category']} | Every {agent['frequency_hours']}h | {'Enabled' if agent['enabled'] else 'Disabled'}")
            st.markdown(f"Keywords: {', '.join(agent['keywords']) if agent['keywords'] else 'None'}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Delete", key=f"delete_agent_{idx}"):
                    agents.pop(idx)
                    save_agents(agents)
                    st.success("Agent deleted!")
                    st.rerun()
            with col2:
                pass  # Placeholder for future edit functionality
    else:
        st.info("No agents configured yet.")

# Main content area
st.header("News Intelligence Dashboard")

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

AGENTS_CONFIG_PATH = "config/agents.yaml"

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