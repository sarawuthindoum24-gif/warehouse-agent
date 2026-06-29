import os, asyncio
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

@app.on_event('startup')
async def startup():
    global ready
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
    sig = request.headers.get('X-Line-Signature','')
    body = await request.body()
    try:
        handler.handle(body.decode(), sig)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail='Invalid signature')
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def on_message(event: MessageEvent):
    user_text = event.message.text
    loop = asyncio.new_event_loop()
    try:
        answer = loop.run_until_complete(ask(user_text))
    finally:
        loop.close()
    with AsyncApiClient(cfg) as client:
        api = AsyncMessagingApi(client)
        loop2 = asyncio.new_event_loop()
        try:
            loop2.run_until_complete(
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=answer)]
                ))
            )
        finally:
            loop2.close()
