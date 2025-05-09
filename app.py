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

# Custom CSS for Tailwind-style modern UI
st.markdown("""
    <style>
    body, .main, .stApp {
        font-family: 'Inter', sans-serif !important;
        background: #FFFFFF !important;
        color: #1A1A3D !important;
    }
    .sidebar-content {
        background-color: #1A1A3D !important;
        border-radius: 1.2rem;
        box-shadow: 0 4px 24px 0 rgba(0,0,0,0.10);
        padding: 2.5rem 1.5rem 2rem 1.5rem;
        margin-bottom: 2rem;
        border: none;
    }
    [data-testid="stSidebar"] .sidebar-content, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4, [data-testid="stSidebar"] h5, [data-testid="stSidebar"] h6, [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stExpanderHeader {
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] label {
        font-weight: 400 !important;
    }
    .stButton>button, .stForm button {
        background: #0072FF !important;
        color: #FFFFFF !important;
        border-radius: 9999px;
        font-weight: 500;
        font-size: 1.08rem;
        padding: 0.7rem 2rem;
        border: none;
        box-shadow: 0 2px 8px 0 rgba(0,114,255,0.10);
        transition: background 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover, .stForm button:hover {
        background: #00C6FF !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 16px 0 rgba(0,198,255,0.12);
    }
    .stTextInput>div>input, .stNumberInput>div>input, .stTextArea>div>textarea, .stMultiSelect>div {
        border-radius: 0.75rem;
        border: 2px solid #0057FF !important;
        box-shadow: 0 1px 6px 0 rgba(0,114,255,0.04);
        padding: 0.6rem 1.1rem;
        background: #0D2A6B !important;
        color: #FFFFFF !important;
        font-size: 1rem;
    }
    .stTextInput>div>input:focus, .stNumberInput>div>input:focus, .stTextArea>div>textarea:focus {
        outline: 2px solid #0057FF !important;
        background: #0D2A6B !important;
        color: #FFFFFF !important;
    }
    .stCheckbox>label {
        font-size: 1rem;
        font-weight: 400;
        color: #FFFFFF !important;
    }
    .stExpanderHeader {
        font-weight: 500;
        font-size: 1.08rem;
        color: #FFFFFF !important;
    }
    .modern-card, .modern-card * {
        background: #FFFFFF !important;
        color: #1A1A3D !important;
        border-radius: 1.2rem;
        box-shadow: 0 4px 24px 0 rgba(0,0,0,0.10);
        padding: 2rem 1.5rem 1.5rem 1.5rem;
        margin-bottom: 2.2rem;
        border: none;
    }
    .modern-card a, .modern-card a:visited, .modern-card a:hover {
        color: #0072FF !important;
        text-decoration: underline;
    }
    .modern-card-empty {
        background: #F5F7FA !important;
        color: #1A1A3D !important;
        border-radius: 1.2rem;
        border: none;
        padding: 2.2rem;
        text-align: center;
        font-size: 1.08rem;
        margin-bottom: 2.2rem;
    }
    .modern-header {
        font-size: 2.1rem;
        font-weight: 500;
        color: #1A1A3D;
        margin-bottom: 1.2rem;
        margin-top: 2.2rem;
        letter-spacing: 0.01em;
    }
    .modern-subheader {
        font-size: 1.18rem;
        font-weight: 400;
        color: #1A1A3D;
        margin-bottom: 1.2rem;
        margin-top: 1.2rem;
    }
    .modern-icon {
        margin-right: 0.5rem;
        vertical-align: middle;
        color: #00C6FF !important;
    }
    .modern-btn-icon {
        margin-right: 0.5rem;
        vertical-align: middle;
        font-size: 1.1rem;
        color: #00C6FF !important;
    }
    .modern-btn-clear {
        background: #0072FF !important;
        color: #FFFFFF !important;
        border-radius: 9999px;
        font-weight: 400;
        font-size: 1.08rem;
        padding: 0.7rem 2rem;
        border: none;
        box-shadow: 0 2px 8px 0 rgba(0,114,255,0.08);
        transition: background 0.2s, box-shadow 0.2s;
    }
    .modern-btn-clear:hover {
        background: #00C6FF !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 16px 0 rgba(0,198,255,0.10);
    }
    a, a:visited {
        color: #0072FF !important;
        text-decoration: none;
    }
    a:hover {
        color: #00C6FF !important;
        text-decoration: underline;
    }
    /* Add more breathing room between sections */
    .stApp > div > div > div > div { margin-bottom: 2.5rem !important; }
    p, span, small {
        color: #1A1A3D !important;
    }
    .stMarkdown p, .stMarkdown span, .stMarkdown small {
        color: #1A1A3D !important;
    }
    /* Fix for unreadable article titles */
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] li {
        color: #1A1A3D !important;
    }

    /* Restore dark menu dropdown contrast */
    section[data-testid="stSidebar"] {
        background-color: #1A1A3D !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* Optional: Better dropdown menu styling (top-right) */
    div[role="menu"] {
        background-color: #1A1A3D !important;
        color: #FFFFFF !important;
    }

    /* Fix unreadable article text inside summary boxes */
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] li {
        color: #1A1A3D !important;  /* High-contrast dark gray */
    }

    /* Fix Streamlit dropdown and menu contrast */
    div[role="menu"], div[role="menu"] * {
        background-color: #1A1A3D !important;
        color: #FFFFFF !important;
    }

    /* Sidebar input contrast fix */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] select {
        background-color: #27272a !important; /* Tailwind gray-800 */
        color: #FFFFFF !important;
    }

    /* Sidebar labels */
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        color: #FFFFFF !important; /* Tailwind gray-200 */
    }
    </style>
""", unsafe_allow_html=True)

# Logo at the top of the main app using columns
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image("logo.png", width=80)
with col_title:
    st.markdown("<span style='font-size:2.2rem;font-weight:700;color:#374151;'>Gofr Recon</span>", unsafe_allow_html=True)

# Logo in the sidebar using columns
col_logo_sb, col_title_sb = st.sidebar.columns([1, 6])
with col_logo_sb:
    st.sidebar.image("logo.png", width=60)
with col_title_sb:
    st.sidebar.markdown("<span style='font-size:1.5rem;font-weight:700;color:#fff;'>Gofr Recon</span>", unsafe_allow_html=True)

# Sidebar (Agent Input Panel)
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    st.header("Configuration")
    date_range = st.date_input(
        "Select Date Range",
        value=(datetime.now() - timedelta(days=1), datetime.now()),
        max_value=datetime.now()
    )
    st.subheader("News Sources")
    all_categories = news_manager.get_all_categories()
    selected_categories = []
    for category_id, info in all_categories.items():
        if st.checkbox(f"{info['name']} ({category_id})", value=True):
            selected_categories.append(category_id)
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
                "enabled": True
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
    st.markdown('</div>', unsafe_allow_html=True)

# Main content area
st.markdown('<div class="modern-header" style="margin-top:1.5rem;">📊 News Intelligence Dashboard</div>', unsafe_allow_html=True)

# Agent Inbox Section
st.markdown('<div class="modern-subheader">Agent Inbox</div>', unsafe_allow_html=True)

run_agents_col, clear_col = st.columns([2, 2])
with run_agents_col:
    if st.button("▶️ Run Agents Now", key="run_agents_btn", help="Run all enabled agents now", use_container_width=True):
        agents = load_agents()
        for agent in agents:
            if agent.get('enabled'):
                agent_task(agent)
        st.success("All enabled agents have run.")
        st.rerun()

# Show agent inbox in modern cards
try:
    with open(INBOX_PATH, "r") as f:
        inbox = json.load(f)
except Exception:
    inbox = []

if inbox:
    for entry in reversed(inbox[-10:]):  # Show last 10 agent runs
        st.markdown(f"<div class='modern-card'>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-weight:600;font-size:1.1rem;'>🕵️‍♂️ Agent:</span> <span style='font-weight:500;'>{entry['agent']}</span> | <span style='font-weight:600;'>Categories:</span> <span style='font-weight:500;'>{', '.join(entry.get('categories', [entry.get('category', 'unknown')]))}</span> | <span style='font-weight:600;'>Time:</span> <span style='font-weight:500;'>{entry['timestamp']}</span>", unsafe_allow_html=True)
        for article in entry['results'][:3]:  # Show up to 3 articles per run
            st.markdown(f"<div style='margin-left:1rem;'><span style='font-weight:600;'>•</span> <a href='{article['url']}' target='_blank' style='color:#6366f1;text-decoration:none;font-weight:500;'>{article['title']}</a></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='modern-card-empty'>No agent findings yet. Run an agent to see results here.</div>", unsafe_allow_html=True)

# Content Generation section
st.markdown("---")
st.markdown('<div class="modern-header">📝 Content Generation</div>', unsafe_allow_html=True)

# Load agent inbox (again for content generation)
try:
    with open(INBOX_PATH, "r") as f:
        inbox = json.load(f)
except Exception:
    inbox = []

col_clear, col_spacer = st.columns([2, 8])
with col_clear:
    if st.button("🗑️ Clear All Agent Findings", key="clear_all_findings2", use_container_width=True):
        with open(INBOX_PATH, "w") as f:
            json.dump([], f)
        st.success("All agent findings deleted.")
        st.rerun()

if inbox:
    st.markdown('<div class="modern-subheader">Agent Findings</div>', unsafe_allow_html=True)
    for idx, finding in enumerate(inbox):
        st.markdown(f"<div class='modern-card'>", unsafe_allow_html=True)
        st.write(f"**Agent:** {finding['agent']} | **Categories:** {', '.join(finding.get('categories', []))} | **Time:** {finding['timestamp']}")
        st.write(f"**Articles:** {len(finding['results'])}")
        del_col, sel_col = st.columns([1, 9])
        with del_col:
            if st.button("🗑️ Delete", key=f"delete_finding_{idx}_cg"):
                del inbox[idx]
                with open(INBOX_PATH, "w") as f:
                    json.dump(inbox, f)
                st.success("Agent finding deleted.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    if st.button("✨ Generate Content", key="generate_content_btn", use_container_width=True):
        with st.spinner("Generating content..."):
            generated_content = content_generator.generate_batch_content(inbox)
            st.markdown('<div class="modern-subheader">Generated Content</div>', unsafe_allow_html=True)
            for content in generated_content:
                st.markdown(f"<div class='modern-card'>", unsafe_allow_html=True)
                st.write("**Title:**")
                st.write(content['title'])
                st.write("**Content:**")
                st.write(content['content'])
                st.write("**Hashtags:**")
                st.write(content['hashtags'])
                st.write("**Call to Action:**")
                st.write(content['cta'])
                st.markdown("---")
                st.subheader("Post Content")
                platforms = st.multiselect(
                    "Select platforms to post to",
                    ["Twitter", "LinkedIn", "Facebook"],
                    key=f"platforms_{content['agent']}_{content['timestamp']}"
                )
                if platforms and st.button("📤 Post Content", key=f"post_{content['agent']}_{content['timestamp']}", use_container_width=True):
                    with st.spinner("Posting content..."):
                        result = content_poster.post_content(content, platforms)
                        if result['success']:
                            st.success("Content posted successfully!")
                        else:
                            st.error(f"Error posting content: {result['error']}")
                st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='modern-card-empty'>No agent findings available. Run some agents first to generate content.</div>", unsafe_allow_html=True)

# Content History section
st.markdown("---")
st.markdown('<div class="modern-header">📚 Posted Content History</div>', unsafe_allow_html=True)

history = content_poster.get_posting_history()
if history:
    for post in history:
        st.markdown(f"<div class='modern-card'>", unsafe_allow_html=True)
        st.write("**Title:**")
        st.write(post.get('title', ''))
        st.write("**Platforms:**")
        st.write(", ".join(post.get('platforms', [])))
        st.write("**Content:**")
        st.write(post.get('content', ''))
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='modern-card-empty'>No content has been posted yet.</div>", unsafe_allow_html=True)

# Run Recon button
st.markdown("<div style='margin:2rem 0; text-align:center;'>", unsafe_allow_html=True)
if st.button("🚀 Run Recon", key="run_recon_btn", use_container_width=True):
    with st.spinner("Gathering and analyzing news..."):
        try:
            articles = fetch_news(
                sources=selected_categories,
                start_date=datetime.combine(date_range[0], datetime.min.time()),
                end_date=datetime.combine(date_range[1], datetime.max.time())
            )
            unique_stories = deduplicate_stories(articles)
            summarized_news = summarize_news(unique_stories)
            st.success(f"✅ Analysis complete! Found {len(summarized_news)} unique articles.")
            for story in summarized_news:
                st.markdown(f"""
                <div class='modern-card'>
                    <h3 style='font-size:1.2rem;font-weight:600;color:#374151;'>{story['title']}</h3>
                    <p><strong>Source:</strong> {story['source']}</p>
                    <p><strong>Published:</strong> {story['published']}</p>
                    <p><strong>Category:</strong> {story['category']}</p>
                    <p><strong>Preview:</strong> {story.get('content', '')[:200]}...</p>
                    <p>{story['summary']}</p>
                    <a href="{story['url']}" target="_blank" style="color:#6366f1;">Read more</a>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center;color:#6b7280;font-size:1rem;'>Gofr Recon | Powered by Streamlit and OpenAI</div>", unsafe_allow_html=True)

def run_scheduler():
    def agent_task_if_enabled(agent):
        agents = load_agents()
        for a in agents:
            if a['name'] == agent['name'] and a.get('enabled'):
                agent_task(a)
                break
    agents = load_agents()
    for agent in agents:
        if agent.get('frequency_minutes', 0) > 0:
            schedule.every(int(agent['frequency_minutes'])).minutes.do(agent_task_if_enabled, agent)
        elif agent.get('frequency_hours', 0) > 0:
            schedule.every(int(agent['frequency_hours'])).hours.do(agent_task_if_enabled, agent)
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