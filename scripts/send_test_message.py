#!/usr/bin/env python3
"""Simulate an inbound WhatsApp message against a locally running server.

Meta only calls the webhook on the deployed (prod) URL, so there's no way to
trigger a real inbound delivery in dev. This builds the same JSON shape Meta
sends, signs it with WHATSAPP_APP_SECRET (like `verify_signature` expects),
and POSTs it to your local /webhook — exercising the *entire* pipeline
(signature check -> InboundMessageStore -> MessageHandler -> ChatService ->
WhatsAppClient.send_text). Since WHATSAPP_TOKEN/WHATSAPP_PHONE_NUMBER_ID in
.env are real, the reply is actually sent via the Graph API, so you'll see it
arrive on your phone.

Prerequisite: --sender must already be a row in the `users` table (the
whitelist checked by PhoneWhitelist) or the message is silently dropped.

Usage:
    uv run scripts/send_test_message.py "ciao, aggiungi il latte alla lista"
    uv run scripts/send_test_message.py "test" --sender 393331112222
    uv run scripts/send_test_message.py "test" --url http://localhost:8000/webhook
"""

import argparse
import hashlib
import hmac
import json
import os
import uuid

import httpx
from dotenv import load_dotenv

from whatsapp_assistant.configs.settings import get_settings


def build_payload(sender: str, text: str, phone_number_id: str) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "TEST_WABA_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": phone_number_id,
                                "phone_number_id": phone_number_id,
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Dev Test"},
                                    "wa_id": sender,
                                }
                            ],
                            "messages": [
                                {
                                    "from": sender,
                                    "id": f"wamid.DEV{uuid.uuid4().hex}",
                                    "timestamp": "0",
                                    "text": {"body": text},
                                    "type": "text",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def sign(body: bytes, app_secret: str) -> str:
    digest = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="Message body to send, e.g. 'ciao'")
    parser.add_argument(
        "--sender",
        help="Sender phone number, no '+' (must exist in the `users` table). "
        "Defaults to the WHATSAPP_TEST_SENDER env var if set.",
    )
    parser.add_argument(
        "--url", default="http://localhost:8080/webhook", help="Local webhook URL"
    )
    args = parser.parse_args()

    load_dotenv("secrets/.env")
    settings = get_settings()

    sender = args.sender or os.environ.get("WHATSAPP_TEST_SENDER")
    if not sender:
        parser.error("--sender is required (or set WHATSAPP_TEST_SENDER in .env)")

    payload = build_payload(sender, args.text, settings.whatsapp_phone_number_id)
    body = json.dumps(payload).encode()
    headers = {
        "content-type": "application/json",
        "x-hub-signature-256": sign(body, settings.whatsapp_app_secret),
    }

    try:
        resp = httpx.post(args.url, content=body, headers=headers, timeout=10)
        print(f"-> {resp.status_code} {resp.text!r}")
        if resp.status_code == 200:
            print("Ack'd. Reply is processing in the background — check your phone.")
    except httpx.RequestError as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    main()
