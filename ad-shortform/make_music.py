"""광고용 오리지널 배경음악 합성 (저작권 걱정 없는 자체 제작 음원).

구성 (120 BPM, 1마디 = 2초, 총 32초)
  0~8초  : 긴장 - 시계 초침 틱, 낮은 단조 패드(Am), 심장박동 킥
  7~8초  : 라이저(노이즈 스윕) -> 8초 '드롭'
  8~26초 : 희망적인 업비트 테크 팝 - C-G-Am-F 진행, 플럭 아르페지오, 킥/클랩/하이햇, 베이스
  26~32초: CTA - 풀 편성 유지 후 마지막 임팩트 + 페이드아웃
"""
import sys
import wave

import numpy as np

SR = 44100
DUR = 32.0
BPM = 120
BEAT = 60 / BPM
N = int(SR * DUR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    L[i : i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 - pan))
    R[i : i + len(sig)] += sig * gain * np.sqrt(0.5 * (1 + pan))


def env(n, a=0.005, d=0.2, s=0.0, r=0.05, length=None):
    t = np.arange(n) / SR
    e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    if length:
        rel = np.clip((t - length) / r, 0, 1)
        e *= 1 - rel
    return e


def kick(dur=0.45):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) + 0.3 * np.sin(ph) * np.exp(-t * 40)


def clap():
    n = int(SR * 0.3)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    e = np.exp(-t * 18) + 0.6 * np.exp(-((t - 0.012) % 0.011) * 300) * (t < 0.035)
    sig = nz * e
    # 밴드패스 근사: 차분 + 스무딩
    sig = np.diff(np.concatenate([[0], sig]))
    return np.convolve(sig, np.ones(4) / 4, "same") * 0.9


def hat(open_=False):
    n = int(SR * (0.25 if open_ else 0.06))
    t = np.arange(n) / SR
    nz = np.diff(np.concatenate([[0], rng.standard_normal(n)]))
    return nz * np.exp(-t * (12 if open_ else 70)) * 0.35


def tick():
    n = int(SR * 0.04)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) + 0.5 * np.sin(2 * np.pi * 3600 * t)) * np.exp(-t * 160)


def pluck(note, dur=0.35):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = midi(note)
    sig = sum((0.6 ** k) * np.sin(2 * np.pi * f * (k + 1) * t) for k in range(5))
    return sig * np.exp(-t * 9) * env(n, a=0.002, d=10)


def pad(notes, dur, bright=0.3):
    n = int(SR * dur)
    t = np.arange(n) / SR
    sig = np.zeros(n)
    for nt in notes:
        for det in (-0.12, 0.0, 0.12):
            f = midi(nt + det)
            saw = 2 * ((f * t) % 1) - 1
            sig += (1 - bright) * np.sin(2 * np.pi * f * t) + bright * saw * 0.5
    a = np.clip(t / 0.25, 0, 1) * np.clip((dur - t) / 0.3, 0, 1)
    return sig * a / (len(notes) * 3)


def bass(note, dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = midi(note)
    sig = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t)
    return sig * env(n, a=0.004, d=0.25, s=0.55, r=0.04, length=dur - 0.04)


def riser(dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    k = np.linspace(40, 2, n).astype(int)
    out = np.empty(n)
    acc = 0.0
    for i in range(n):  # 점점 밝아지는 노이즈 스윕
        acc += (nz[i] - acc) / k[i]
        out[i] = acc
    sw = np.sin(2 * np.pi * np.cumsum(np.linspace(200, 1600, n)) / SR) * 0.25
    return (out * 2 + sw) * (t / dur) ** 2


def impact():
    n = int(SR * 2.5)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 8)) / SR) * np.exp(-t * 2.2)
    nz = rng.standard_normal(n) * np.exp(-t * 10) * 0.3
    return boom + nz


# ---------------- 0~8초 : 긴장 파트 ----------------
add(pad([45, 52, 57, 60], 8.2, bright=0.15), 0.0, 0.5)  # Am (저음)
for b in range(16):
    add(tick(), b * BEAT, 0.35, pan=0.3 if b % 2 else -0.3)  # 시계 초침
for b in range(0, 16, 2):
    add(kick(0.3), b * BEAT, 0.45)  # 심장박동
    add(kick(0.3), b * BEAT + 0.22, 0.25)
add(riser(1.0), 7.0, 0.35)

# ---------------- 8~32초 : 업비트 파트 ----------------
prog = [  # (베이스, 코드, 아르페지오 음)
    (36, [60, 64, 67, 72], [72, 76, 79, 84]),  # C
    (43, [59, 62, 67, 71], [71, 74, 79, 83]),  # G
    (45, [57, 60, 64, 69], [69, 72, 76, 81]),  # Am
    (41, [57, 60, 65, 69], [69, 72, 77, 81]),  # F
]
start, end = 8.0, 31.0
bar = 0
t0 = start
while t0 < end - 1e-6:
    bn, chord, arp = prog[bar % 4]
    add(pad(chord, 2.05, bright=0.35), t0, 0.32)
    for k in range(4):
        tb = t0 + k * BEAT
        add(kick(), tb, 0.9)
        add(bass(bn, BEAT * 0.48), tb + BEAT / 2, 0.55)
        if k in (1, 3):
            add(clap(), tb, 0.5)
        add(hat(), tb + BEAT / 2, 0.8, pan=0.25)
        add(hat(), tb + BEAT / 4, 0.35, pan=-0.25)
        add(hat(), tb + 3 * BEAT / 4, 0.35, pan=-0.25)
    pat = [0, 1, 2, 3, 2, 1, 2, 3]
    for j, idx in enumerate(pat):
        add(pluck(arp[idx]), t0 + j * BEAT / 2, 0.22, pan=-0.35 if j % 2 else 0.35)
    bar += 1
    t0 += 2.0
add(riser(1.0), 25.0, 0.25)  # CTA 진입 전 살짝 리프트
add(impact(), 8.0, 0.55)
add(impact(), 31.0, 0.6)
add(pad([48, 60, 64, 67, 72], 1.2, bright=0.4), 31.0, 0.5)

# ---------------- 마스터링 ----------------
def reverb(x):
    out = x.copy()
    for d, g in ((0.031, 0.35), (0.047, 0.3), (0.071, 0.25), (0.113, 0.2), (0.167, 0.15)):
        k = int(d * SR)
        out[k:] += x[:-k] * g
    return out

L2, R2 = reverb(L), reverb(R)
mix = np.stack([L2, R2], axis=1)
mix = np.tanh(mix * 1.4)  # 소프트 클리핑(라우드니스)
fade = np.ones(N)
fi = int(SR * 0.05)
fo = int(SR * 0.9)
fade[:fi] = np.linspace(0, 1, fi)
fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade[:, None]
mix /= np.max(np.abs(mix)) / 0.89

out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("wrote", out)
