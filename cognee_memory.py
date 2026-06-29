import os
import cognee
from drive_loader import get_service, list_files, read_file

async def sync_drive():
    svc = get_service()
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    files = list_files(folder_id)
    texts = []
    for f in files:
        try:
            content = read_file(f['id'], f['mimeType'])
            if content:
                texts.append(f"=== {f['name']} ===\n{content}")
        except Exception as e:
            print(f"Skip {f['name']}: {e}")
    if texts:
        combined = "\n\n".join(texts)
        await cognee.add(combined)
        await cognee.cognify()

async def ask(question: str) -> str:
    try:
        results = await cognee.search(cognee.SearchType.INSIGHTS, question)
        if results:
            return str(results[0])
        return "ไม่พบข้อมูลที่เกี่ยวข้องครับ"
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"
