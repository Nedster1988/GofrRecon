import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from config import Config
import logging
import sys
import socket
from storage.sheets_manager import SheetsManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_port_availability(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return True
    except:
        return False

def find_available_port(start_port=8501, max_attempts=10):
    """Find an available port starting from start_port"""
    port = start_port
    for _ in range(max_attempts):
        if check_port_availability(port):
            return port
        port += 1
    return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_sheet_data():
    """Load data from Google Sheets and return as DataFrame"""
    try:
        config = Config()
        # Use Streamlit secrets instead of local file
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sheet = gc.open("GOFR Recon Feed").sheet1
        
        # Get all data
        data = sheet.get_all_records()
        
        if not data:
            logger.warning("No data found in Google Sheet")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert date strings to datetime
        df['Published Date'] = pd.to_datetime(df['Published Date'], errors='coerce')
        
        # Sort by date, most recent first
        df = df.sort_values('Published Date', ascending=False)
        
        logger.info(f"Successfully loaded {len(df)} articles from Google Sheet")
        return df
        
    except Exception as e:
        logger.error(f"Error loading sheet data: {str(e)}")
        st.error("Failed to load data from Google Sheets. Please check the logs for details.")
        return pd.DataFrame()

def create_clickable_link(title, url):
    """Create HTML link for Streamlit"""
    return f'<a href="{url}" target="_blank">{title}</a>'

def main():
    # Find available port
    port = find_available_port()
    if port is None:
        logger.error("Could not find an available port")
        st.error("Could not start the dashboard. No available ports found.")
        return
    
    logger.info(f"Starting dashboard on port {port}")
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="GOFR Recon Dashboard",
        page_icon="📰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .stDataFrame {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🧠 GOFR Recon Dashboard")
    st.markdown("---")
    
    # Load data with loading spinner
    with st.spinner("Loading articles from Google Sheets..."):
        try:
            manager = SheetsManager()
            data = manager.load_data()

            if data.empty:
                st.warning("⚠️ Connected to Google Sheets, but the sheet is empty.")
            else:
                st.success("✅ Successfully connected to Google Sheets.")
                st.dataframe(data)

        except Exception as e:
            st.error("❌ Failed to load data from Google Sheets.")
            st.exception(e)
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Category filter
    categories = ['All'] + sorted(data['Category'].unique().tolist())
    selected_category = st.sidebar.selectbox(
        "Select Category",
        categories
    )
    
    # Tags filter
    all_tags = set()
    for tags in data['Tags'].dropna():
        all_tags.update(tag.strip() for tag in tags.split(','))
    all_tags = sorted(list(all_tags))
    
    selected_tags = st.sidebar.multiselect(
        "Select Tags",
        all_tags
    )
    
    # Date range filter
    st.sidebar.header("Date Range")
    min_date = data['Published Date'].min()
    max_date = data['Published Date'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Search bar
    search_query = st.sidebar.text_input("Search Articles", "")
    
    # Apply filters
    filtered_df = data.copy()
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    
    if selected_tags:
        filtered_df = filtered_df[filtered_df['Tags'].apply(
            lambda x: any(tag in x.split(',') for tag in selected_tags)
        )]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['Published Date'] >= start_date) &
            (filtered_df['Published Date'] <= end_date)
        ]
    
    if search_query:
        search_query = search_query.lower()
        filtered_df = filtered_df[
            filtered_df['Title'].str.lower().str.contains(search_query) |
            filtered_df['Summary'].str.lower().str.contains(search_query)
        ]
    
    # Create clickable links
    filtered_df['Title'] = filtered_df.apply(
        lambda x: create_clickable_link(x['Title'], x['Link']),
        axis=1
    )
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Articles", len(data))
    with col2:
        st.metric("Filtered Articles", len(filtered_df))
    with col3:
        st.metric("Categories", len(categories) - 1)
    with col4:
        st.metric("Tags", len(all_tags))
    
    st.markdown("---")
    
    # Display filtered data
    if not filtered_df.empty:
        # Format the DataFrame for display
        display_df = filtered_df[['Title', 'Published Date', 'Category', 'Tags', 'Summary']].copy()
        display_df['Published Date'] = display_df['Published Date'].dt.strftime('%Y-%m-%d %H:%M')
        
        # Display as HTML to enable clickable links
        st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        # Add download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name="gofr_articles.csv",
            mime="text/csv"
        )
    else:
        st.info("No articles match the selected filters.")

if __name__ == "__main__":
    main() 