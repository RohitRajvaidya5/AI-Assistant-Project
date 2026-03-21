import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import pyttsx3
import ollama

# ------------------------
# INIT
# ------------------------

print("🚀 Starting Jarvis Step 1...")

model = WhisperModel("base")  # upgrade to "small" later if needed

engine = pyttsx3.init()

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

def ask_ai(prompt):
    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

# ------------------------
# AUDIO (RECORD UNTIL SILENCE)
# ------------------------

def record_until_silence(samplerate=16000, silence_threshold=0.01, silence_duration=1.0):
    print("🎤 Speak now...")

    audio = []
    silent_chunks = 0
    chunk_size = 1024

    while True:
        chunk = sd.rec(chunk_size,
                       samplerate=samplerate,
                       channels=1,
                       dtype='float32')
        sd.wait()

        audio.append(chunk)

        volume = np.linalg.norm(chunk)

        if volume < silence_threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0

        # stop when silence detected
        if silent_chunks > (silence_duration * samplerate / chunk_size):
            break

    return np.concatenate(audio, axis=0).flatten()

# ------------------------
# TRANSCRIBE
# ------------------------

def transcribe(audio):
    segments, _ = model.transcribe(audio)
    text = ""
    for segment in segments:
        text += segment.text
    return text.strip().lower()

# ------------------------
# MAIN LOOP
# ------------------------

print("🧠 Jarvis is ready. Speak anything... (say 'exit' to stop)")

while True:

    audio = record_until_silence()
    text = transcribe(audio)

    if not text:
        continue

    print("You:", text)

    if text in ["exit", "quit"]:
        speak("Goodbye")
        break

    response = ask_ai(text)
    speak(response)