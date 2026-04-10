"""
Google Drive utilities for uploading and retrieving reports
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import io

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
except ImportError:
    print("Google API client not installed. Skipping Google Drive integration.")

class GoogleDriveManager:
    def __init__(self, credentials_file=None):
        """Initialize Google Drive manager"""
        self.service = None
        self.folder_id = None
        
        if credentials_file and os.path.exists(credentials_file):
            self._authenticate(credentials_file)
    
    def _authenticate(self, credentials_file):
        """Authenticate with Google Drive using service account"""
        try:
            creds = Credentials.from_service_account_file(
                credentials_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.service = build('drive', 'v3', credentials=creds)
            print("[OK] Authenticated with Google Drive")
        except Exception as e:
            print(f"[ERROR] Failed to authenticate with Google Drive: {e}")
            self.service = None
    
    def create_reports_folder(self):
        """Create 'PrudentSigma Reports' folder if it doesn't exist"""
        if not self.service:
            return None
        
        try:
            # Search for existing folder
            query = "name='PrudentSigma Reports' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                pageSize=1,
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                self.folder_id = folders[0]['id']
                print(f"[OK] Found existing folder: {self.folder_id}")
                return self.folder_id
            
            # Create new folder
            file_metadata = {
                'name': 'PrudentSigma Reports',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            self.folder_id = folder.get('id')
            print(f"[OK] Created new Reports folder: {self.folder_id}")
            return self.folder_id
        except Exception as e:
            print(f"[ERROR] Failed to create reports folder: {e}")
            return None
    
    def upload_report(self, local_file_path):
        """Upload a report file to Google Drive"""
        if not self.service or not self.folder_id:
            print("[WARNING] Google Drive not configured. Skipping upload.")
            return False
        
        try:
            file_name = os.path.basename(local_file_path)
            
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id]
            }
            
            media = MediaFileUpload(
                local_file_path,
                mimetype='text/markdown',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f"[OK] Uploaded report to Google Drive: {file_name}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to upload report: {e}")
            return False
    
    def list_reports(self):
        """List all reports in the Google Drive folder"""
        if not self.service or not self.folder_id:
            return []
        
        try:
            query = f"'{self.folder_id}' in parents and trashed=false and name~'report_.*\\.md'"
            results = self.service.files().list(
                q=query,
                orderBy='createdTime desc',
                spaces='drive',
                pageSize=10,
                fields='files(id, name, createdTime, modifiedTime)'
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            print(f"[ERROR] Failed to list reports: {e}")
            return []
    
    def download_report(self, file_id):
        """Download a report content from Google Drive"""
        if not self.service:
            return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            return content.decode('utf-8') if isinstance(content, bytes) else content
        except Exception as e:
            print(f"[ERROR] Failed to download report: {e}")
            return None
