#!/usr/bin/env python3
"""Vídeo da série 'A Bíblia em histórias' (Luz da Fé): ilustração do livro com movimento,
legenda palavra a palavra sincronizada com a voz e chamada para a próxima parte.

uso: historia_video.py <dados.json> <mix.m4a> <asr.json> <texto.txt> <saida.mp4>
dados.json: {"serie": "...", "titulo": "José", "parte": 1, "imgs": ["c4_1"], "fim1": "...", "fim2": "...", "t0": 0.4}
"""
import sys, json, re, unicodedata, difflib, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

dados_p, mix, asr_p, txt_p, out = sys.argv[1:6]
D = json.load(open(dados_p))
W, H, FPS = 1080, 1920, 30
GF = "/usr/share/fonts/truetype/google-fonts/"
POPB, POPR, LORA = GF + "Poppins-Bold.ttf", GF + "Poppins-Regular.ttf", GF + "Lora-Variable.ttf"
GOLD, CREAM = (240, 199, 94), (255, 246, 226)
T0 = D.get("t0", 0.4)

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)
TOTAL = dur(mix)

# ---------- imagens (pan + zoom lento) ----------
ZMAX = 1.10
def prep(name):
    im = Image.open(f"/home/claude/serie/livro/img/{name}.png").convert("RGB")
    s = H * ZMAX / im.height
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
IMGS = [prep(n) for n in D["imgs"]]

def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def quadro(im, u, sentido):
    """u em 0..1 ao longo do trecho; pan horizontal + zoom de 1.10 até 1.0 (aproxima)."""
    ch = im.height / (1.0 + 0.10 * u)             # aproxima devagar ao longo do trecho
    cw = ch * W / H
    maxx = im.width - cw
    x = maxx * (0.15 + 0.7 * (u if sentido > 0 else 1 - u))
    y = (im.height - ch) / 2
    return im.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((W, H), Image.BILINEAR)

# sombra superior/inferior para legibilidade
grad = np.zeros((H, W, 1), np.float32)
yy = np.arange(H)[:, None, None]
grad += np.clip(1 - yy / 520, 0, 1) * 0.75
grad += np.clip((yy - 1000) / 920, 0, 1) * 0.55
GRAD = grad

# ---------- legenda sincronizada ----------
def norm(x):
    x = unicodedata.normalize("NFD", x.lower()); x = "".join(c for c in x if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", x)
words = json.load(open(asr_p))
TEXTO = open(txt_p).read().split()
A = [norm(w["word"]) for w in words]; Tn = [norm(w) for w in TEXTO]
ts = [None] * len(Tn)
for a0, b0, n in difflib.SequenceMatcher(None, Tn, A, autojunk=False).get_matching_blocks():
    for q in range(n): ts[a0 + q] = (words[b0 + q]["start"], words[b0 + q]["end"])
last = (T0, T0)
for q in range(len(ts)):
    if ts[q] is None:
        nxt = next((ts[r] for r in range(q + 1, len(ts)) if ts[r]), (last[1] + 0.35, last[1] + 0.35))
        ts[q] = (last[1], max(last[1] + 0.05, min(nxt[0], last[1] + 0.35)))
    last = ts[q]
caps, cur = [], []
for q, w in enumerate(TEXTO):
    cur.append(q)
    if len(cur) == 3 or w.endswith((".", ",", "?", "!", ":")):
        caps.append(cur); cur = []
if cur: caps.append(cur)
VOZ_FIM = ts[-1][1]

F_CAP = ImageFont.truetype(POPB, 74)
F_LAB = ImageFont.truetype(POPB, 30)
F_TIT = ImageFont.truetype(LORA, 66); F_TIT.set_variation_by_axes([700])
F_END1 = ImageFont.truetype(POPB, 60)
F_END2 = ImageFont.truetype(POPR, 40)

def legenda(d, t):
    for grp in caps:
        a, b = ts[grp[0]][0], ts[grp[-1]][1]
        if a - 0.05 <= t <= b + 0.15:
            ws = [TEXTO[i] for i in grp]
            sp = d.textlength(" ", font=F_CAP)
            lens = [d.textlength(w, font=F_CAP) for w in ws]
            tot = sum(lens) + sp * (len(ws) - 1)
            x = W / 2 - tot / 2; y = 1230
            for i, w in zip(grp, ws):
                ativo = ts[i][0] - 0.03 <= t
                cor = GOLD if (ativo and t <= ts[i][1] + 0.08) else (CREAM if ativo else (255, 255, 255))
                d.text((x, y), w, font=F_CAP, fill=cor, stroke_width=7, stroke_fill=(15, 15, 22), anchor="ls")
                x += d.textlength(w, font=F_CAP) + sp
            return

cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
       "-pix_fmt", "yuv420p", "-c:a", "copy", "-t", f"{TOTAL:.2f}", "-movflags", "+faststart", out]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
N = len(IMGS); seg = TOTAL / N
T_END = VOZ_FIM + 0.4
CAPA = None
if D.get("capa"):
    CAPA = Image.open(D["capa"]).convert("RGBA")
    CAPA = CAPA.resize((int(CAPA.width * 620 / CAPA.height), 620), Image.LANCZOS)
for fi in range(int(TOTAL * FPS)):
    t = fi / FPS
    k = min(int(t / seg), N - 1); u = (t - k * seg) / seg
    fr = quadro(IMGS[k], u, 1 if k % 2 == 0 else -1)
    if k + 1 < N and u > 0.92:                       # transição suave entre imagens
        nx = quadro(IMGS[k + 1], 0, -1 if k % 2 == 0 else 1)
        fr = Image.blend(fr, nx, ease((u - 0.92) / 0.08))
    arr = np.asarray(fr, np.float32) * (1 - GRAD)
    fr = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(fr)
    # cabeçalho fixo
    d.text((W / 2, 205), D["serie"].upper(), font=F_LAB, fill=GOLD, anchor="mm")
    tit = D["titulo"] if not D.get("parte") else f'{D["titulo"]} · Parte {D["parte"]}'
    d.text((W / 2, 275), tit, font=F_TIT, fill=CREAM, anchor="mm",
           stroke_width=3, stroke_fill=(15, 15, 22))
    if t < T_END:
        legenda(d, t)
    else:
        a = ease((t - T_END) / 0.5)
        ov = Image.new("RGBA", (W, H), (18, 20, 34, int(150 * a)))
        fr = Image.alpha_composite(fr.convert("RGBA"), ov).convert("RGB"); d = ImageDraw.Draw(fr)
        y0 = 1060 + (1 - a) * 40
        if CAPA is not None:
            cimg = CAPA.copy(); cimg.putalpha(int(255 * a))
            fr.paste(cimg, (int(W / 2 - CAPA.width / 2), int(y0 - CAPA.height - 50)), cimg)
            d = ImageDraw.Draw(fr)
        d.rounded_rectangle((140, y0, W - 140, y0 + 150), 75, fill=GOLD)
        d.text((W / 2, y0 + 75), D["fim1"], font=F_END1, fill=(29, 32, 51), anchor="mm")
        d.text((W / 2, y0 + 230), D["fim2"], font=F_END2, fill=CREAM, anchor="mm")
    fo = 1 - ease((t - TOTAL + 0.4) / 0.4)
    a8 = np.asarray(fr, np.uint8)
    if fo < 1: a8 = (a8 * fo).astype(np.uint8)
    proc.stdin.write(a8.tobytes())
proc.stdin.close(); proc.wait()
print("PRONTO", out, f"{TOTAL:.1f}s")
