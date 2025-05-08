import logging
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SheetsStorage:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.credentials = Credentials.from_service_account_file(
            config.sheets_credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
        
    def store(self, items: List[Dict[str, Any]]) -> None:
        """
        Store processed items in Google Sheets
        """
        if not items:
            self.logger.info("No items to store")
            return
            
        try:
            # Prepare the data for sheets
            values = []
            for item in items:
                row = [
                    item['title'],
                    item['link'],
                    item['published'],
                    item['ai_summary'],
                    item['source'],
                    item['fetched_at']
                ]
                values.append(row)
                
            # Prepare the request body
            body = {
                'values': values
            }
            
            # Append the data to the sheet
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.config.spreadsheet_id,
                range=f"{self.config.sheet_name}!A:F",
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            self.logger.info(f"Stored {len(items)} items in Google Sheets")
            
        except HttpError as e:
            self.logger.error(f"Error storing items in Google Sheets: {str(e)}")
            raise 