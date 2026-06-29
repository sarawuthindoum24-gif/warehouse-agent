import os, cognee
from dotenv import load_dotenv
from drive_loader import get_service, list_files, download
load_dotenv()

FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

async def sync_drive():
    svc = get_service()
    files = list_files(svc, FOLDER_ID)
    print(f'พบ {len(files)} ไฟล์')
    for f in files:
        try:
            buf, name = download(svc, f['id'], f['mimeType'], f['name'])
            parts = f['path'].strip('/').split('/')
            ds = f"stockbnn_{parts[0]}".replace(' ','_')
            await cognee.add(buf, dataset_name=ds)
            print(f"  loaded: {f['path']}")
        except Exception as e:
            print(f"  skip: {f['path']} -> {e}")
    await cognee.cognify()
    print('Knowledge Graph ready!')

async def ask(question: str) -> str:
    try:
        results = await cognee.recall(question)
        if not results:
            return 'ไม่พบข้อมูลที่เกี่ยวข้องครับ'
        answers = []
        for r in results[:5]:
            if hasattr(r, 'text'):
                answers.append(r.text)
            elif isinstance(r, str):
                answers.append(r)
        return '\n'.join(answers) if answers else str(results[0])
    except Exception as e:
        return f'เกิดข้อผิดพลาด: {str(e)}'
