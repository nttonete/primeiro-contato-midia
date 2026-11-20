#!/usr/bin/env python3
"""Luz da Fé - página de Bíblia com marca-texto sincronizado palavra a palavra com a narração.

uso: pagina_sync.py <dados.json> <id> <audio_fonte(mp4/mp3)> <palavras_asr.json> <saida.mp4>

O tempo de cada palavra vem do reconhecimento de fala (Vosk) feito sobre o próprio áudio do vídeo,
então a caneta passa em cada palavra no momento em que ela é falada.
O áudio de <audio_fonte> é copiado sem alteração (voz + trilha).
"""
import sys, json, re, subprocess, unicodedata, difflib, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
LEFT, RIGHT = 125, 865
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SANSB = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FS, LH, INDENT, PGAP = 54, 78, 42, 14
TEXT = (52, 46, 40)
GREEN = (144, 215, 73)
NAVY = (42, 46, 66)
GOLD = (236, 190, 72)
T_READ0 = 1.2
import os
HOOK_END = float(os.environ.get('HOOK_END', '2.6'))  # gancho fica na tela até aqui (s)
LEAD = 0.06          # a caneta anda 60 ms à frente da fala (percepção de "junto")

dados_p, vid, src, asr_p, out_p = sys.argv[1:6]
D = [d for d in json.load(open(dados_p)) if d["id"] == vid][0]
f_txt = ImageFont.truetype(SERIF, FS)
f_num = ImageFont.truetype(SANSB, 26)
f_hdr = ImageFont.truetype(SANSB, 26)

# ---------------- layout ----------------
tokens = []   # cada token: dict(kind='w'|'n', text, para, hl)
for pi, p in enumerate(D["paras"]):
    for n, t in p["items"]:
        tokens.append(dict(kind="n", text=str(n), para=pi, hl=p["hl"]))
        for w in t.split():
            tokens.append(dict(kind="w", text=w, para=pi, hl=p["hl"]))

def tw(tok):
    f = f_num if tok["kind"] == "n" else f_txt
    return f.getlength(tok["text"])

SPACE = f_txt.getlength(" ")
lines = []   # lista de (y_baseline, [tokens com x])
y = 450 + 50
cur_para = None
i = 0
while i < len(tokens):
    pi = tokens[i]["para"]
    first = pi != cur_para
    if first and cur_para is not None:
        y += PGAP
    cur_para = pi
    x0 = LEFT + (INDENT if first else 0)
    # junta palavras na linha (número de versículo cola na palavra seguinte)
    groups = []
    j = i
    while j < len(tokens) and tokens[j]["para"] == pi:
        if tokens[j]["kind"] == "n" and j + 1 < len(tokens):
            groups.append([tokens[j], tokens[j + 1]]); j += 2
        else:
            groups.append([tokens[j]]); j += 1
    k = 0
    while k < len(groups):
        line = []; width = 0.0
        while k < len(groups):
            g = groups[k]
            gw = sum(tw(t) for t in g) + (4 if len(g) == 2 else 0)
            need = gw + (SPACE if line else 0)
            if line and x0 + width + need > RIGHT:
                break
            line.append((g, gw)); width += need; k += 1
        last = k >= len(groups)
        nat = sum(gw for _, gw in line)
        gaps = len(line) - 1
        sp = SPACE if (last or gaps == 0) else (RIGHT - x0 - nat) / gaps
        x = x0
        placed = []
        for g, gw in line:
            gx = x
            for t in g:
                t2 = dict(t); t2["x0"] = gx; t2["x1"] = gx + tw(t)
                placed.append(t2)
                gx = t2["x1"] + (4 if t["kind"] == "n" else 0)
            x += gw + sp
        lines.append(dict(y=y, toks=placed, full=not last, x0=x0))
        y += LH
        x0 = LEFT
    i = j
PH = max(2000, int(y + 150))

# ---------------- página (fundo + texto) ----------------
def paper(h):
    yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
    base = np.array([242, 235, 215], np.float32)
    dx = (xx - W / 2) / (W / 2)
    shade = 1 - 0.06 * np.clip(np.abs(dx) ** 2.5, 0, 1) - 0.07 * (dx < 0) * np.abs(dx) ** 2
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 2.2, (h, W)).astype(np.float32)
    img = base[None, None, :] * shade[..., None] + noise[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)

bg = paper(PH)
plain = Image.fromarray(bg.copy())
hlimg = Image.fromarray(bg.copy())

# retângulos do marca-texto por linha
hl_words = []          # palavras destacadas na ordem de leitura: (line_idx, x0, x1, text)
line_rect = {}
for li, L in enumerate(lines):
    hts = [t for t in L["toks"] if t["hl"]]
    if not hts:
        continue
    rx0 = hts[0]["x0"] - 6
    rx1 = (RIGHT + 8) if L["full"] else hts[-1]["x1"] + 6
    line_rect[li] = (rx0, rx1)
    for t in hts:
        if t["kind"] == "w":
            hl_words.append(dict(li=li, x0=t["x0"], x1=t["x1"], text=t["text"]))

dh = ImageDraw.Draw(hlimg)
for li, (rx0, rx1) in line_rect.items():
    yb = lines[li]["y"]
    dh.rectangle((rx0, yb - 47, rx1, yb + 20), fill=GREEN)

for img in (plain, hlimg):
    d = ImageDraw.Draw(img)
    hdr = D["hdr"]
    xh = LEFT
    for ch in hdr:
        d.text((xh, 380), ch, font=f_hdr, fill=(120, 110, 95), anchor="ls")
        xh += f_hdr.getlength(ch) + 5
    d.line((LEFT, 406, RIGHT, 406), fill=(170, 160, 140), width=2)
    for L in lines:
        for t in L["toks"]:
            if t["kind"] == "n":
                d.text((t["x0"], L["y"] - 26), t["text"], font=f_num, fill=TEXT, anchor="ls")
            else:
                d.text((t["x0"], L["y"]), t["text"], font=f_txt, fill=TEXT, anchor="ls")
plain = np.array(plain); hlimg = np.array(hlimg)

# ---------------- tempos das palavras (ASR) ----------------
def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)

asr = [w for w in json.load(open(asr_p)) if w.get("conf", 1) > 0.0]
A = [norm(w["word"]) for w in asr]
Tn = [norm(w["text"]) for w in hl_words]
sm = difflib.SequenceMatcher(None, Tn, A, autojunk=False)
ts = [None] * len(Tn); te = [None] * len(Tn)
for a0, b0, n in sm.get_matching_blocks():
    for k in range(n):
        ts[a0 + k] = asr[b0 + k]["start"]; te[a0 + k] = asr[b0 + k]["end"]
# blocos "replace" com mesmo nº de itens: casa 1 a 1 (ex.: "chegar-se" x "chegasse")
for tag, a0, a1, b0, b1 in sm.get_opcodes():
    if tag == "replace":
        if a1 - a0 == b1 - b0:
            for k in range(a1 - a0):
                ts[a0 + k] = asr[b0 + k]["start"]; te[a0 + k] = asr[b0 + k]["end"]
        else:   # distribui o trecho reconhecido proporcional ao tamanho das palavras
            s0, s1 = asr[b0]["start"], asr[b1 - 1]["end"]
            wts = [max(2, len(Tn[k])) for k in range(a0, a1)]
            acc = s0; tot = sum(wts)
            for k, wv in zip(range(a0, a1), wts):
                ts[k] = acc; acc += (s1 - s0) * wv / tot; te[k] = acc
# palavras sem tempo: preenche entre vizinhos
n = len(Tn)
k = 0
while k < n:
    if ts[k] is None:
        j = k
        while j < n and ts[j] is None:
            j += 1
        left = te[k - 1] if k > 0 else (asr[0]["start"] if asr else T_READ0)
        right = ts[j] if j < n else (left + 0.35 * (j - k))
        wts = [max(2, len(Tn[q])) for q in range(k, j)]
        tot = sum(wts); acc = left
        for q, wv in zip(range(k, j), wts):
            ts[q] = acc; acc += (right - left) * wv / tot; te[q] = acc
        k = j
    else:
        k += 1
# garante monotonia
for k in range(1, n):
    if ts[k] < te[k - 1] - 0.02 and ts[k] < ts[k - 1]:
        ts[k] = te[k - 1]
    te[k] = max(te[k], ts[k] + 0.05)
for k, w in enumerate(hl_words):
    w["ts"] = ts[k] - LEAD; w["te"] = te[k] - LEAD
matched = sum(nn for _, _, nn in sm.get_matching_blocks())
print(f"palavras: {n}, casadas pelo ASR: {matched}", flush=True)

READ_END = hl_words[-1]["te"] + LEAD
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout.strip())
T_CTA = READ_END + 0.6
TOTAL = dur

def head(t):
    """(linha, x) da ponta do marca-texto no instante t"""
    if t <= hl_words[0]["ts"]:
        w = hl_words[0]; return w["li"], w["x0"] - 6
    for k, w in enumerate(hl_words):
        if t < w["ts"]:
            p = hl_words[k - 1]; return p["li"], p["x1"]
        if t <= w["te"]:
            f = (t - w["ts"]) / max(1e-3, w["te"] - w["ts"])
            f = f * f * (3 - 2 * f) * 0.35 + f * 0.65
            x0 = w["x0"] - 6 if (k == 0 or hl_words[k - 1]["li"] != w["li"]) else hl_words[k - 1]["x1"]
            return w["li"], x0 + (w["x1"] - x0) * f
    w = hl_words[-1]
    return w["li"], line_rect[w["li"]][1]

# ---------------- elementos sobrepostos ----------------
def pill(text, size, fg):
    f = ImageFont.truetype(POP, size)
    tw_ = f.getlength(text); padx, h = 42, int(size * 1.95)
    w = int(tw_ + 2 * padx)
    im = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, 6 + w, 6 + h), radius=h // 2, fill=NAVY + (240,), outline=(200, 160, 60, 255), width=3)
    d.text((6 + w / 2, 6 + h / 2 + 2), text, font=f, fill=fg, anchor="mm")
    return im

def fit_pill(text, size, fg):
    while True:
        im = pill(text, size, fg)
        if im.width <= 820 or size <= 28:
            return im
        size -= 2

def rgba_np(im):
    a = np.array(im).astype(np.float32)
    return a[..., :3], a[..., 3:] / 255.0

P_HOOK = rgba_np(fit_pill(D["hook"], 52, (255, 255, 255)))
P_REF = rgba_np(fit_pill(D["ref"], 50, GOLD))

def make_pen():
    L, R = 560, 26
    im = Image.new("RGBA", (L + 80, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = 60
    d.polygon([(10, cy), (52, cy - 14), (52, cy + 14)], fill=(40, 70, 200, 255))        # ponta azul
    d.polygon([(10, cy), (22, cy - 4), (22, cy + 4)], fill=(20, 35, 120, 255))
    d.rectangle((52, cy - 16, 92, cy + 16), fill=(185, 190, 205, 255))                     # colar metálico
    d.rounded_rectangle((90, cy - R, L, cy + R), radius=R, fill=(222, 170, 52, 255))       # corpo dourado
    d.rectangle((90, cy - R, L - 20, cy - R + 12), fill=(246, 206, 98, 255))               # brilho
    d.rectangle((90, cy + R - 12, L - 20, cy + R), fill=(176, 126, 30, 255))               # sombra
    d.rectangle((150, cy - R, 160, cy + R), fill=(120, 80, 20, 255))                       # anel
    d.rounded_rectangle((330, cy - R - 6, 470, cy - R + 8), radius=6, fill=(196, 146, 40, 255))  # clipe
    d.rounded_rectangle((L - 40, cy - R - 2, L + 6, cy + R + 2), radius=12, fill=(168, 118, 26, 255))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.split()[3].point(lambda v: int(v * 0.35)))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    big = Image.new("RGBA", (im.width + 60, im.height + 60), (0, 0, 0, 0))
    big.alpha_composite(sh, (40, 46)); big.alpha_composite(im, (20, 20))
    ang = -27  # graus: corpo desce para a direita
    rot = big.rotate(ang, resample=Image.BICUBIC, expand=True)
    # posição da ponta depois da rotação
    cx, cyc = big.width / 2, big.height / 2
    px, py = 30 - cx, 80 - cyc
    a = math.radians(-ang)
    rx = px * math.cos(a) - py * math.sin(a) + rot.width / 2
    ry = px * math.sin(a) + py * math.cos(a) + rot.height / 2
    return rgba_np(rot), (rx, ry)

PEN, PEN_TIP = make_pen()

cta_f = ImageFont.truetype(POP, 74)
cta = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
dg = ImageDraw.Draw(cta)
for k, s in enumerate(("Siga para receber", "a Palavra todo dia")):
    dg.text((W / 2, 150 + k * 110), s, font=cta_f, fill=(255, 150, 60, 255), anchor="mm")
glow = cta.filter(ImageFilter.GaussianBlur(14))
cta2 = Image.new("RGBA", cta.size, (0, 0, 0, 0)); cta2.alpha_composite(glow)
dg = ImageDraw.Draw(cta2)
for k, s in enumerate(("Siga para receber", "a Palavra todo dia")):
    dg.text((W / 2, 150 + k * 110), s, font=cta_f, fill=(255, 241, 214, 255), anchor="mm")
CTA = rgba_np(cta2)

def blend(frame, rgb, a, x, y, alpha=1.0):
    h, w = a.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or alpha <= 0.003:
        return
    sa = a[y0 - y:y1 - y, x0 - x:x1 - x] * alpha
    region = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = (region * (1 - sa) + rgb[y0 - y:y1 - y, x0 - x:x1 - x] * sa).astype(np.uint8)

def ramp(t, a, b):
    return float(min(max((t - a) / (b - a), 0.0), 1.0))

# ---------------- render ----------------
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
       "-i", "-", "-i", src, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
       "-pix_fmt", "yuv420p", "-c:a", "copy", "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", out_p]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
first_li = hl_words[0]["li"]
cam = lines[first_li]["y"] - 0.45 * H
cam = min(max(cam, 0), PH - H)
NF = int(TOTAL * FPS)
PEN_IN, PEN_OUT = hl_words[0]["ts"] - 0.35, READ_END + 0.25
for fi in range(NF):
    t = fi / FPS
    li, hx = head(t)
    target = lines[li]["y"] - 0.45 * H
    target = min(max(target, 0), PH - H)
    cam += (target - cam) * 0.085
    top = int(round(cam))
    frame = plain[top:top + H].copy()
    # marca-texto: linhas anteriores completas + linha atual até a ponta
    if t >= hl_words[0]["ts"]:
        for lj, (rx0, rx1) in line_rect.items():
            if lj > li:
                continue
            xe = rx1 if lj < li else hx
            if lj == li and t > READ_END:
                xe = rx1
            yb = lines[lj]["y"]
            ya, yb2 = yb - 47 - top, yb + 21 - top
            if yb2 <= 0 or ya >= H:
                continue
            ya, yb2 = max(0, ya), min(H, yb2)
            xa, xb = int(rx0), int(min(xe, rx1))
            if xb > xa:
                frame[ya:yb2, xa:xb] = hlimg[top + ya:top + yb2, xa:xb]
    # caneta
    if PEN_IN <= t <= PEN_OUT + 0.5:
        a_in = ramp(t, PEN_IN, PEN_IN + 0.3)
        a_out = 1 - ramp(t, PEN_OUT, PEN_OUT + 0.45)
        k = min(a_in, a_out)
        slide = (1 - k) * 260
        bob = 3 * math.sin(t * 9)
        px = hx - PEN_TIP[0] + slide
        py = lines[li]["y"] + 6 - top - PEN_TIP[1] + bob + slide * 0.5
        blend(frame, PEN[0], PEN[1], px, py, k)
    # pílulas
    ah = min(ramp(t, 0.05, 0.35), 1 - ramp(t, HOOK_END - 0.3, HOOK_END))
    if ah > 0:
        blend(frame, P_HOOK[0], P_HOOK[1], (W - P_HOOK[1].shape[1]) / 2, 286 - P_HOOK[1].shape[0] / 2, ah)
    ar = min(ramp(t, HOOK_END + 0.2, HOOK_END + 0.5), 1 - ramp(t, T_CTA, T_CTA + 0.3))
    if ar > 0:
        blend(frame, P_REF[0], P_REF[1], (W - P_REF[1].shape[1]) / 2, 298 - P_REF[1].shape[0] / 2, ar)
    # chamada final
    if t >= T_CTA:
        a = ramp(t, T_CTA, T_CTA + 0.4)
        frame = (frame.astype(np.float32) * (1 - 0.82 * a) + np.array([40, 40, 54], np.float32) * 0.82 * a).astype(np.uint8)
        s = ramp(t, T_CTA + 0.15, T_CTA + 0.55)
        blend(frame, CTA[0], CTA[1], 0, 960 - 205 + (1 - s) * 30, s)
    fo = 1 - ramp(t, TOTAL - 0.45, TOTAL)
    if fo < 1:
        frame = (frame.astype(np.float32) * fo).astype(np.uint8)
    proc.stdin.write(frame.tobytes())
    if fi % 300 == 0:
        print(f"frame {fi} / {NF}", flush=True)
proc.stdin.close(); proc.wait()
print("PRONTO", out_p, flush=True)
