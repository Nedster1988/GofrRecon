import os
from pathlib import Path
import streamlit as st
import openai
from google.oauth2.service_account import Credentials

class Config:
    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent.absolute()
        
        # Load OpenAI key from secrets
        self.openai_api_key = st.secrets["openai"]["api_key"]
        openai.api_key = self.openai_api_key
        
        # Load Google service account credentials from secrets
        creds_dict = {key: st.secrets["google"][key] for key in st.secrets["google"]}
        self.google_creds = Credentials.from_service_account_info(creds_dict)
        
        # RSS Feed settings
        self.rss_feeds = [
            "https://example.com/feed1.xml",
            "https://example.com/feed2.xml"
        ]
        
        # Google Sheets settings
        self.spreadsheet_id = st.secrets.get("spreadsheet_id", "your-spreadsheet-id")
        self.sheet_name = st.secrets.get("sheet_name", "Feed Items")
        
        # Email settings
        self.smtp_server = st.secrets.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = int(st.secrets.get("smtp_port", "587"))
        self.sender_email = st.secrets.get("sender_email", "your-email@gmail.com")
        self.smtp_password = st.secrets.get("smtp_password", "")
        self.recipient_emails = st.secrets.get("recipient_emails", "recipient1@example.com,recipient2@example.com").split(',')
        
        # AI settings
        self.model_name = st.secrets.get("model_name", "gpt-3.5-turbo")
        
        # Storage settings
        self.cache_file = os.path.join(self.base_dir, "data", "processed_items.json")
        
    def validate(self):
        """Validate the configuration settings"""
        required_secrets = [
            ('openai.api_key', self.openai_api_key),
            ('google.type', st.secrets["google"]["type"]),
            ('google.private_key', st.secrets["google"]["private_key"]),
            ('google.client_email', st.secrets["google"]["client_email"]),
        ]
        
        for name, value in required_secrets:
            if not value:
                raise ValueError(f"Required secret {name} is not set")
        
        required_files = [
            self.sheets_credentials_path,
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}") 