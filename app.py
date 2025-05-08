import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import our modules (these will be created later)
from sources.rss_parser import fetch_news
from ai.summarizer import summarize_news
from utils.deduplicate import deduplicate_stories

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
    
    # Source selection (placeholder for now)
    st.subheader("News Sources")
    st.checkbox("Tech News", value=True)
    st.checkbox("Business News", value=True)
    st.checkbox("Security News", value=True)
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Gofr Recon provides real-time news intelligence and analysis using AI-powered summarization.")

# Main content area
st.header("News Intelligence Dashboard")

# Run Recon button
if st.button("🚀 Run Recon", use_container_width=True):
    with st.spinner("Gathering and analyzing news..."):
        try:
            # Fetch news (will be implemented in rss_parser.py)
            news_items = fetch_news()
            
            # Deduplicate stories (will be implemented in deduplicate.py)
            unique_stories = deduplicate_stories(news_items)
            
            # Summarize news (will be implemented in summarizer.py)
            summarized_news = summarize_news(unique_stories)
            
            # Display results
            st.success("✅ Analysis complete!")
            
            # Display summarized news in cards
            for story in summarized_news:
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <h3>{story['title']}</h3>
                        <p><strong>Source:</strong> {story['source']}</p>
                        <p><strong>Published:</strong> {story['published']}</p>
                        <p>{story['summary']}</p>
                        <a href="{story['url']}" target="_blank">Read more</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("This is expected as the supporting modules haven't been implemented yet.")

# Footer
st.markdown("---")
st.markdown("Gofr Recon | Powered by Streamlit and OpenAI") 