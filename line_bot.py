import os, asyncio, concurrent.futures
from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
	AsyncApiClient, AsyncMessagingApi, Configuration,
	ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv
from cognee_memory import ask, sync_drive
load_dotenv()

app = FastAPI()
cfg = Configuration(access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
ready = False
_loop = None

@app.on_event('startup')
async def startup():
	global ready, _loop
	_loop = asyncio.get_event_loop()
	print('Loading Knowledge Graph...')
	await sync_drive()
	ready = True
	print('Bot ready!')

@app.get('/')
async def root():
	return {'status': 'ready' if ready else 'loading', 'bot': 'StockBNN Warehouse Agent'}

@app.get('/health')
async def health():
	return {'status': 'ok'}

@app.post('/webhook')
async def webhook(request: Request):
	sig = request.headers.get('X-Line-Signature', '')
	body = await request.body()
	try:
		handler.handle(body.decode(), sig)
	except InvalidSignatureError:
		raise HTTPException(status_code=400, detail='Invalid signature')
	return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def on_message(event: MessageEvent):
	user_text = event.message.text
	# Run async ask() using run_coroutine_threadsafe to avoid nested loop error
	future = asyncio.run_coroutine_threadsafe(ask(user_text), _loop)
	try:
		answer = future.result(timeout=60)
	except Exception as e:
		answer = f"เกิดข้อผิดพลาด: {str(e)[:100]}"
	# Reply
	reply_future = asyncio.run_coroutine_threadsafe(
		_do_reply(event.reply_token, answer), _loop
	)
	try:
		reply_future.result(timeout=30)
	except Exception:
		pass

async def _do_reply(reply_token: str, text: str):
	async with AsyncApiClient(cfg) as client:
		api = AsyncMessagingApi(client)
		await api.reply_message(ReplyMessageRequest(
			reply_token=reply_token,
			messages=[TextMessage(text=text)]
		))
