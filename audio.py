"""Procedural WAV beeps via pygame.Sound (pygame-only dependency)."""

import io
import math
import struct
import wave


def _wav_bytes(samples: list[int], sample_rate: int = 22050) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(struct.pack("<" + "h" * len(samples), *samples))
    return buf.getvalue()


def sine_tone(freq: float, seconds: float, sample_rate: int = 22050, volume: float = 0.18) -> list[int]:
    n = max(1, int(sample_rate * seconds))
    amp = int(32767 * volume)
    out: list[int] = []
    for i in range(n):
        t = i / sample_rate
        s = amp * math.sin(2 * math.pi * freq * t)
        out.append(int(max(-32767, min(32767, s))))
    env = len(out)
    for i, v in enumerate(out):
        g = min(i, env - 1 - i) / max(env // 3, 1)
        mul = max(0.05, min(1.0, g * 2))
        out[i] = int(v * mul)
    return out


def load_sounds(pygame_pkg):
    """Build short UI/game event sounds."""
    pygame = pygame_pkg
    pygame.mixer.init(frequency=22050, size=-16, channels=1)

    def s(freq, dur):
        return pygame.mixer.Sound(_wav_bytes(sine_tone(freq, dur)))

    return {
        "move": s(440, 0.04),
        "rotate": s(680, 0.05),
        "lock": s(220, 0.06),
        "clear": s(520, 0.12),
        "tetris": s(320, 0.35),
        "gameover": s(120, 0.5),
        "pause": s(880, 0.05),
    }
