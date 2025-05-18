import whisper

model = whisper.load_model("turbo")
result = model.transcribe("/Users/bryant/Downloads/test.json/audio_20250518_164113.wav", language="zh")
print(f"result: {result}")
print('=========')
print(result["text"])
