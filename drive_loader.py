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
    try:
                if mime_type == 'application/vnd.google-apps.spreadsheet':
                                content = service.files().export(fileId=file_id, mimeType='text/csv').execute()
elif mime_type == 'application/vnd.google-apps.document':
            content = service.files().export(fileId=file_id, mimeType='text/plain').execute()
elif mime_type == 'application/vnd.google-apps.presentation':
            content = service.files().export(fileId=file_id, mimeType='text/plain').execute()
elif 'google-apps' in mime_type:
            content = service.files().export(fileId=file_id, mimeType='text/plain').execute()
elif mime_type and mime_type.startswith('text/'):
            content = service.files().get_media(fileId=file_id).execute()
else:
            return None
            if isinstance(content, bytes):
                            try:
                                                return content.decode('utf-8')
except Exception:
                try:
                                        return content.decode('latin-1')
except Exception:
                    return None
        return str(content)
except Exception:
        return None
