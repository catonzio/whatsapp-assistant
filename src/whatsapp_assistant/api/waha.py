import logging

from fastapi import APIRouter, Request

router = APIRouter()

logger = logging.getLogger("waha")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


@router.get("/bot")
def whatsapp_webhook_get():
    return "WhatsApp Download Files Bot is ready!"


@router.post("/bot")
async def whatsapp_webhook_post(request: Request):
    data = await request.json()
    print(data)
    logger.info(f"Received webhook data: {data}")

    if data["event"] != "message":
        # We can't process other event yet
        return f"Unknown event {data['event']}"

    payload = data["payload"]
    # Ignore messages without files
    if not payload.get("mediaUrl", None):
        return "No files in the message"

    # Number in format 791111111@c.us
    # chat_id = payload["from"]
    # Message ID - false_11111111111@c.us_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    # message_id = payload["id"]
    # For groups - who sent the message
    # participant = payload.get("participant")
    # IMPORTANT - Always send seen before sending new message
    # send_seen(chat_id=chat_id, message_id=message_id, participant=participant)

    # Download the file and download it to the current folder
    client_url = payload["mediaUrl"]
    filename = client_url.split("/")[-1]
    # path = abspath("./" + filename)
    # r = requests.get(client_url)
    # with open(path, "wb") as f:
    #     f.write(r.content)

    # Send a text back via WhatsApp HTTP API
    text = f"We have downloaded file here: {filename}"
    logger.info(text)
    # send_message(chat_id=chat_id, text=text)

    # Send OK back
    return "OK"
