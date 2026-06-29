import os, json, base64
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def get_service():
	b64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64", "").strip()
	b64 = b64 + "=" * ((4 - len(b64) % 4) % 4)
	info = json.loads(base64.b64decode(b64).decode('utf-8'))
	creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
	return build('drive', 'v3', credentials=creds)


def list_files(folder_id=None):
	folder_id = folder_id or os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
	svc = get_service()
	q = f"'{folder_id}' in parents and trashed=false"
	res = svc.files().list(q=q, fields="files(id, name, mimeType)").execute()
	return res.get('files', [])


def _decode(data):
	if not isinstance(data, bytes):
		return str(data)
	for enc in ('utf-8', 'latin-1', 'cp874'):
		try:
			return data.decode(enc)
		except Exception:
			pass
	return None


def read_file(file_id, mime_type):
	svc = get_service()
	try:
		if mime_type == 'application/vnd.google-apps.spreadsheet':
			raw = svc.files().export(fileId=file_id, mimeType='text/csv').execute()
		elif mime_type in ('application/vnd.google-apps.document', 'application/vnd.google-apps.presentation'):
			raw = svc.files().export(fileId=file_id, mimeType='text/plain').execute()
		elif 'google-apps' in mime_type:
			raw = svc.files().export(fileId=file_id, mimeType='text/plain').execute()
		elif mime_type and mime_type.startswith('text/'):
			raw = svc.files().get_media(fileId=file_id).execute()
		else:
			return None
		return _decode(raw)
	except Exception:
		return None

