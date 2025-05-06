import logging
import gspread
from typing import Dict, Any, List, Tuple
from config import Config

class SheetsManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Initialize Google Sheets client
        try:
            self.gc = gspread.authorize(self.config.google_creds)
            self.logger.info("Successfully authenticated with Google Sheets API")
        except Exception as e:
            self.logger.error(
                "Failed to authenticate with Google Sheets API. "
                "Please check your service account credentials and ensure they are valid."
            )
            raise
            
        # Open the specific sheet
        try:
            self.sheet = self.gc.open("GOFR Recon Feed").sheet1
            self.logger.info("Successfully connected to 'GOFR Recon Feed' spreadsheet")
        except gspread.exceptions.SpreadsheetNotFound:
            self.logger.error(
                "Could not find spreadsheet 'GOFR Recon Feed'. "
                "Please ensure:\n"
                "1. The spreadsheet exists and is named exactly 'GOFR Recon Feed'\n"
                "2. The service account email has been given access to the spreadsheet\n"
                "3. The spreadsheet sharing settings allow the service account to edit"
            )
            raise
        except Exception as e:
            self.logger.error(
                "Failed to open Google Sheet. "
                "Please check:\n"
                "1. The spreadsheet name is correct\n"
                "2. The service account has proper permissions\n"
                "3. The spreadsheet is accessible"
            )
            raise
            
    def _prepare_row(self, data: Dict[str, Any]) -> List[str]:
        """Prepare a single row of data for Google Sheets"""
        article = data['original_article']
        return [
            article['title'],
            article['published'],
            article['source'],
            article['link'],
            data['category'],
            ', '.join(data['tags']),
            data['summary']
        ]
        
    def _get_existing_links(self) -> set:
        """Get set of existing article links from the sheet"""
        try:
            # Get all values from the Link column (column D)
            all_links = self.sheet.col_values(4)  # 4 is the index for column D
            # Skip header row
            return set(all_links[1:])
        except gspread.exceptions.APIError as e:
            self.logger.error(
                "Failed to read from Google Sheet. "
                "Please check:\n"
                "1. The service account has proper permissions\n"
                "2. The spreadsheet is accessible\n"
                "3. The API quota hasn't been exceeded"
            )
            raise
        except Exception as e:
            self.logger.error(f"Error getting existing links: {str(e)}")
            return set()
        
    def _filter_new_articles(self, data_list: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter out articles that already exist in the sheet
        
        Returns:
            Tuple of (new_articles, skipped_articles)
        """
        existing_links = self._get_existing_links()
        new_articles = []
        skipped_articles = []
        
        for data in data_list:
            link = data['original_article']['link']
            if link in existing_links:
                skipped_articles.append(data)
                self.logger.info(f"Skipping duplicate article: {data['original_article']['title']}")
            else:
                new_articles.append(data)
                
        return new_articles, skipped_articles
        
    def save_article_analysis(self, data: Dict[str, Any]) -> bool:
        """
        Save a single article analysis to Google Sheets
        
        Args:
            data: Dictionary containing article analysis data
            
        Returns:
            bool: True if article was saved, False if it was a duplicate
        """
        try:
            # Check for duplicates
            new_articles, skipped = self._filter_new_articles([data])
            
            if not new_articles:
                self.logger.info(f"Skipped duplicate article: {data['original_article']['title']}")
                return False
                
            # Prepare the row data
            row = self._prepare_row(data)
            
            # Append to the sheet
            self.sheet.append_row(row)
            
            self.logger.info(f"Saved analysis for article: {data['original_article']['title']}")
            return True
            
        except gspread.exceptions.APIError as e:
            self.logger.error(
                "Failed to write to Google Sheet. "
                "Please check:\n"
                "1. The service account has proper permissions\n"
                "2. The spreadsheet is accessible\n"
                "3. The API quota hasn't been exceeded"
            )
            raise
        except Exception as e:
            self.logger.error(f"Error saving article analysis: {str(e)}")
            raise
            
    def save_batch_analysis(self, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Save multiple article analyses to Google Sheets
        
        Args:
            data_list: List of dictionaries containing article analysis data
            
        Returns:
            Tuple of (saved_count, skipped_count)
        """
        try:
            # Filter out duplicates
            new_articles, skipped_articles = self._filter_new_articles(data_list)
            
            if not new_articles:
                self.logger.info(f"No new articles to save. Skipped {len(skipped_articles)} duplicates.")
                return 0, len(skipped_articles)
                
            # Prepare all rows
            rows = [self._prepare_row(data) for data in new_articles]
            
            # Append all rows at once
            self.sheet.append_rows(rows)
            
            self.logger.info(f"Saved {len(new_articles)} new articles, skipped {len(skipped_articles)} duplicates")
            return len(new_articles), len(skipped_articles)
            
        except gspread.exceptions.APIError as e:
            self.logger.error(
                "Failed to write to Google Sheet. "
                "Please check:\n"
                "1. The service account has proper permissions\n"
                "2. The spreadsheet is accessible\n"
                "3. The API quota hasn't been exceeded"
            )
            raise
        except Exception as e:
            self.logger.error(f"Error saving batch analysis: {str(e)}")
            raise
            
    def ensure_headers(self) -> None:
        """Ensure the sheet has the correct headers"""
        headers = [
            'Title',
            'Published Date',
            'Source URL',
            'Link',
            'Category',
            'Tags',
            'Summary'
        ]
        
        try:
            # Check if headers exist
            existing_headers = self.sheet.row_values(1)
            
            if not existing_headers or existing_headers != headers:
                # Clear the sheet and add headers
                self.sheet.clear()
                self.sheet.append_row(headers)
                self.logger.info("Added headers to Google Sheet")
        except gspread.exceptions.APIError as e:
            self.logger.error(
                "Failed to update sheet headers. "
                "Please check:\n"
                "1. The service account has proper permissions\n"
                "2. The spreadsheet is accessible\n"
                "3. The API quota hasn't been exceeded"
            )
            raise
        except Exception as e:
            self.logger.error(f"Error ensuring headers: {str(e)}")
            raise

def save_article_analysis(data: Dict[str, Any]) -> bool:
    """
    Convenience function to save a single article analysis
    
    Returns:
        bool: True if article was saved, False if it was a duplicate
    """
    manager = SheetsManager()
    return manager.save_article_analysis(data)

def save_batch_analysis(data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Convenience function to save multiple article analyses
    
    Returns:
        Tuple of (saved_count, skipped_count)
    """
    manager = SheetsManager()
    return manager.save_batch_analysis(data_list) 