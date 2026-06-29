import os
import json
import sqlite3
import httpx

DB_PATH = "/tmp/warehouse.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, name TEXT, content TEXT)")
    conn.commit()
    conn.close()

async def sync_drive():
    from drive_loader import get_service, list_files, read_file
    init_db()
    svc = get_service()
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    files = list_files(folder_id)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM docs")
    for f in files:
        try:
            content = read_file(f["id"], f["mimeType"])
            if content and len(content) > 10:
                conn.execute("INSERT INTO docs (name, content) VALUES (?, ?)", (f["name"], content[:5000]))
        except Exception as e:
            print(f"Skip {f['name']}: {e}")
    conn.commit()
    conn.close()
    print("Drive synced!")

async def ask(question: str) -> str:
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT name, content FROM docs").fetchall()
        conn.close()
        if not rows:
            return "ยังไม่มีข้อมูลในระบบครับ กรุณารอสักครู่"
        context = "\n\n".join([f"[{r[0]}]\n{r[1][:1000]}" for r in rows[:5]])
        api_key = os.environ.get("LLM_API_KEY", "")
        api_base = os.environ.get("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": f"คุณคือ AI ผู้ช่วยคลังสินค้า StockBNN ตอบคำถามจากข้อมูลต่อไปนี้:\n\n{context}"},
                {"role": "user", "content": question}
            ],
            "max_tokens": 500
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{api_base}/chat/completions", json=payload, headers=headers)
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"
