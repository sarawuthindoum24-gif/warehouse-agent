import os
import json
import base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_service():
    b64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64", "")
    b64 = b64.strip()
    padding = 4 - len(b64) % 4
    if padding != 4:
        b64 += "=" * padding
    info = json.loads(base64.b64decode(b64).decode('utf-8'))
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def list_files(folder_id=None):
    if not folder_id:
        folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    service = get_service()
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get('files', [])

def read_file(file_id, mime_type):
    service = get_service()
    if 'google-apps' in mime_type:
        content = service.files().export(fileId=file_id, mimeType='text/plain').execute()
    else:
        content = service.files().get_media(fileId=file_id).execute()
    if isinstance(content, bytes):
        try:
            return content.decode('utf-8')
        except:
            return content.decode('latin-1')
    return str(content)
