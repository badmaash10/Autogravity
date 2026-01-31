"""
Google Docs Uploader Utility
============================
Uploads a local markdown file to Google Docs and prints the URL.

Usage:
    python gdocs_uploader.py path/to/file.md "Document Title"

Prerequisites:
    1. Create a Google Cloud project
    2. Enable Google Docs API
    3. Create OAuth2 credentials (Desktop App)
    4. Download credentials.json to this directory
"""

import sys
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Scopes required for creating Google Docs
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.file']

# Paths
SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_PATH = SCRIPT_DIR / "credentials.json"
TOKEN_PATH = SCRIPT_DIR / "token.pickle"


def get_authenticated_service():
    """Authenticate and return the Google Docs service."""
    creds = None

    # Load existing token
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(f"[ERROR] credentials.json not found at {CREDENTIALS_PATH}")
                print("Please download OAuth2 credentials from Google Cloud Console.")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    docs_service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    return docs_service, drive_service


def upload_to_docs(file_path: str, title: str = None) -> str:
    """
    Uploads a file to Google Docs.
    
    Args:
        file_path: Path to the file to upload
        title: Title for the Google Doc (defaults to filename)
    
    Returns:
        URL of the created Google Doc
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read file content
    content = path.read_text(encoding='utf-8')
    
    if title is None:
        title = path.stem

    docs_service, drive_service = get_authenticated_service()

    # Create a new Google Doc
    doc = docs_service.documents().create(body={'title': title}).execute()
    doc_id = doc.get('documentId')

    # Insert content into the document
    requests = [
        {
            'insertText': {
                'location': {'index': 1},
                'text': content
            }
        }
    ]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

    # Generate URL
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    
    return doc_url


def main():
    if len(sys.argv) < 2:
        print("Usage: python gdocs_uploader.py <file_path> [title]")
        sys.exit(1)

    file_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Uploading {file_path} to Google Docs...")
    
    try:
        url = upload_to_docs(file_path, title)
        print(f"SUCCESS: {url}")
        return url
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
