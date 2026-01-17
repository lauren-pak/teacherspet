import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import random
illegal_apps = ["snap", "instagram", "chatgpt", "tiktok", "youtube", "netflix", "discord", "twitter", "facebook"]

app_detected = "instagram"  # Example detected app

def relaymessage(app_detected):
    
    message_start = ["Stop using", "Quit using", "Okay, enough", "Get off "]
    message_end = [", you bum!", ", get back to work!", ", lock in dawg!", ", the teacher is watching!"]

    # Load .env
    load_dotenv()
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("Missing ELEVENLABS_API_KEY")

    # Create client
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    try:
        text_start= random.choice(message_start)
        text_end= random.choice(message_end)
        audio = client.text_to_speech.convert(
            text = f"{text_start} {app_detected} {text_end}",
            voice_id="pNInz6obpgDQGcFmaJgB",        # Replace with your voice ID
            model_id="eleven_v3",
            output_format="mp3_44100_128"
        )

        # Play the audio
        play(audio)

    except Exception as e:
        print("ElevenLabs error:", e)

relaymessage(app_detected)
