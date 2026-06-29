import io, os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from dotenv import load_dotenv
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SUPPORTED = {
    'application/vnd.google-apps.spreadsheet',
    'application/vnd.google-apps.document',
    'text/csv','text/plain','application/pdf',
}
EXPORT_MAP = {
    'application/vnd.google-apps.spreadsheet': ('text/csv','.csv'),
    'application/vnd.google-apps.document':    ('text/plain','.txt'),
}

def get_service():
    creds = service_account.Credentials.from_service_account_file(
        os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE','service_account.json'), scopes=SCOPES)
    return build('drive','v3',credentials=creds)

def list_files(service, folder_id, path=''):
    files = []
    items = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields='files(id,name,mimeType)'
    ).execute().get('files',[])
    for item in items:
        fp = f"{path}/{item['name']}"
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            files.extend(list_files(service, item['id'], fp))
        elif item['mimeType'] in SUPPORTED:
            files.append({**item,'path':fp})
    return files

def download(service, fid, mime, name):
    buf = io.BytesIO()
    if mime in EXPORT_MAP:
        em, ext = EXPORT_MAP[mime]
        req = service.files().export_media(fileId=fid, mimeType=em)
        name += ext
    else:
        req = service.files().get_media(fileId=fid)
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    buf.name = name
    return buf, name
