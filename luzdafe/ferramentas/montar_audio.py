#!/usr/bin/env python3
"""Monta o áudio de um vídeo Luz da Fé: trilha ambiente sintetizada + voz (atrasada 1,2 s).

uso: montar_audio.py <voz.mp3> <saida_mix.m4a> <saida_voz_16k.wav>
Duração total = 1,2 + voz + 0,6 + 2,4 s (chamada final).
"""
import sys, os, subprocess
import numpy as np
from scipy.io import wavfile

voz, out_mix, out_asr = sys.argv[1:4]
SR = 44100
T_READ0 = float(os.environ.get('T0', '1.2'))

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout.strip())

VD = dur(voz)
TOTAL = T_READ0 + VD + float(os.environ.get('TAIL', '3.0'))

def music(total, seed=7):
    n = int(total * SR) + SR
    t = np.arange(n) / SR
    # progressão em Ré: D - Bm - G - A (4 s cada), acordes suaves
    chords = [[146.83, 220.00, 293.66, 369.99], [123.47, 185.00, 246.94, 293.66],
              [98.00, 146.83, 196.00, 246.94], [110.00, 164.81, 220.00, 277.18]]
    seg = 4.0
    out = np.zeros(n, np.float32)
    for k in range(int(total / seg) + 2):
        c = chords[k % 4]
        a, b = int(k * seg * SR), int((k + 1) * seg * SR + 1.5 * SR)
        b = min(b, n)
        if a >= n: break
        tt = t[a:b] - k * seg
        env = np.minimum(1, tt / 1.2) * np.clip((seg + 1.5 - tt) / 1.5, 0, 1)
        s = np.zeros(b - a)
        for i, f in enumerate(c):
            s += np.sin(2 * np.pi * f * tt + i) * (0.9 if i else 1.1)
            s += 0.25 * np.sin(2 * np.pi * f * 2 * tt + 0.5 * i)
        out[a:b] += (s * env * 0.06).astype(np.float32)
    # brilho suave (sino) a cada 2 s
    rng = np.random.default_rng(seed)
    notes = [587.33, 739.99, 880.0, 987.77, 1174.66]
    for k in range(int(total / 2)):
        a = int((0.5 + 2 * k) * SR); L = int(2.5 * SR)
        if a + L > n: break
        tt = np.arange(L) / SR
        f = notes[rng.integers(len(notes))]
        out[a:a + L] += (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 1.8) * 0.025).astype(np.float32)
    # eco simples para ambiência
    for d, g in ((0.23, 0.35), (0.41, 0.22), (0.67, 0.12)):
        k = int(d * SR)
        out[k:] += out[:-k] * g
    # fade in/out
    fi = int(1.0 * SR); out[:fi] *= np.linspace(0, 1, fi)
    end = int(total * SR); fo = int(1.2 * SR)
    out[end - fo:end] *= np.linspace(1, 0, fo); out[end:] = 0
    out = out[:end]
    out /= max(1e-6, np.abs(out).max())
    return out * 0.5

m = music(TOTAL)
wav_m = out_mix + ".music.wav"
wavfile.write(wav_m, SR, np.stack([m, m], 1).astype(np.float32))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav_m, "-i", voz, "-filter_complex",
                f"[0:a]volume=0.30[m];[1:a]aresample={SR},volume=1.6,adelay={int(T_READ0*1000)}|{int(T_READ0*1000)}[v];"
                f"[m][v]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]",
                "-map", "[a]", "-c:a", "aac", "-b:a", "160k", "-t", f"{TOTAL:.3f}", out_mix], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voz, "-af", f"adelay={int(T_READ0*1000)},apad=pad_dur=3",
                "-ac", "1", "-ar", "16000", out_asr], check=True)
print(f"ok voz={VD:.2f}s total={TOTAL:.2f}s")
