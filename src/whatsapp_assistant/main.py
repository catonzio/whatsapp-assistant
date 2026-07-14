from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from openai import OpenAI

load_dotenv()

client = OpenAI()
app = FastAPI()


@app.post("/")
async def transcribe_audio(file: UploadFile):
    audio_bytes = await file.read()
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=(file.filename, audio_bytes, file.content_type),
    )
    return {"transcription": transcription.text}
