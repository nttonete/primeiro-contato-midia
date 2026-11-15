import sys, json, wave
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(-1)
M = "/home/claude/raffsx/voice_assistant/vosk_python/example/model"
model = Model(M)
wf = wave.open(sys.argv[1], "rb")
rec = KaldiRecognizer(model, wf.getframerate()); rec.SetWords(True)
out = []
while True:
    data = wf.readframes(4000)
    if not data: break
    if rec.AcceptWaveform(data):
        out += json.loads(rec.Result()).get("result", [])
out += json.loads(rec.FinalResult()).get("result", [])
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
print(" ".join(f"{w['word']}@{w['start']:.2f}" for w in out))
