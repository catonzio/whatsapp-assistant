# WhatsApp Assistant

A free WhatsApp bot: send it a voice message, it replies with the transcription.

It uses the **WhatsApp Cloud API** (webhooks) + **OpenAI** for transcription.
Because the bot only ever *replies* to user-initiated messages within the 24-hour
customer-service window, these are **service conversations** and are free under
WhatsApp's current pricing — you never send a proactive/template message.

## How it works

1. A user sends a voice note to your WhatsApp business number.
2. Meta delivers it to `POST /webhook`. We ACK with `200` immediately and process
   in the background (WhatsApp retries if the webhook is slow).
3. We download the audio (resolve media ID → temporary URL → bytes, both authenticated).
4. We transcribe it with OpenAI (`gpt-4o-transcribe`).
5. We send the transcription back as a text reply.

## Setup

### 1. Environment

Fill in `.env`:

```
OPENAI_API_KEY=sk-...
WHATSAPP_TOKEN=            # Meta App Dashboard > WhatsApp > API Setup > temporary/permanent token
WHATSAPP_PHONE_NUMBER_ID=  # the "Phone number ID" (NOT the phone number)
WHATSAPP_VERIFY_TOKEN=     # any random string you invent
```

### 2. Create the Meta app (one-time)

1. Go to <https://developers.facebook.com/apps> → create an app → add the **WhatsApp** product.
2. In **WhatsApp > API Setup** you get a **test number**, a **Phone number ID**, and a
   temporary access token (24h). Copy the token and phone number ID into `.env`.
3. Add your own phone number as a **recipient** in that panel so you can test.

> The temporary token expires every 24h. For something long-lived, create a
> **System User** in Business Settings with a permanent token, or refresh the token.

### 3. Run locally + expose it

```bash
uv run fastapi dev src/whatsapp_assistant/main.py
```

Meta needs a public HTTPS URL. In another terminal, tunnel to your local port:

```bash
ngrok http 8000
# or: cloudflared tunnel --url http://localhost:8000
```

### 4. Configure the webhook

In **WhatsApp > Configuration > Webhook**:

- **Callback URL:** `https://<your-tunnel>/webhook`
- **Verify token:** the same value as `WHATSAPP_VERIFY_TOKEN`
- Click **Verify and save** (Meta calls `GET /webhook`).
- Under **Webhook fields**, subscribe to **messages**.

### 5. Test

Send a voice message from your registered number to the test number. You should
get the transcription back within a few seconds.

## Development

```bash
uv sync              # install deps
uv run fastapi dev src/whatsapp_assistant/main.py   # hot-reload dev server
```
