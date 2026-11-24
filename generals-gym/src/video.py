"""Render a saved replay to a video (MP4 / GIF), no browser needed.

    python -m src.video replays/game.json -o replays/game.mp4

The renderer draws the same board the browser client draws -- rounded tiles,
castles, general stars, fog, live army counters -- plus a scoreboard header and
a turn counter, and pipes the frames into ``ffmpeg``.  To export without ffmpeg, choose a GIF output instead.

``ffmpeg`` comes from either ``imageio-ffmpeg`` (``pip install imageio-ffmpeg``)
or your ``PATH``.  The only Python dependency is Pillow.

Example::

    from game.replay import Replay
    from src.video import VideoOptions, render_replay

    replay = Replay.load("replays/game.json")
    render_replay(replay, "replays/game.mp4", VideoOptions(view="all"))
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from game.config import MOUNTAIN, NEUTRAL
from game.replay import Replay

# ------------------------------------------------------------------- palette
BG = (9, 12, 17)
PANEL = (17, 24, 35)
BOARD = (12, 17, 25)
FOG = (20, 27, 37)
MOUNTAIN_FILL = (43, 52, 68)
NEUTRAL_FILL = (138, 147, 162)
TEXT = (246, 249, 255)
TEXT_DARK = (21, 27, 36)
MUTED = (141, 154, 174)
GOLD = (255, 214, 130)
SEAT_COLORS = ((76, 141, 255), (255, 95, 95))
SEAT_LIGHT = ((160, 205, 255), (255, 165, 165))

FONT_CANDIDATES = {
    "bold": (
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ),
    "regular": (
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ),
}

_FONT_CACHE: dict[tuple[str, int], ImageFont.ImageFont] = {}


def font(kind: str, size: int) -> ImageFont.ImageFont:
    """Load a TTF at ``size`` (cached), falling back to Pillow's default font."""
    size = max(6, int(size))
    cached = _FONT_CACHE.get((kind, size))
    if cached is not None:
        return cached
    loaded: ImageFont.ImageFont | None = None
    for candidate in FONT_CANDIDATES[kind]:
        try:
            loaded = ImageFont.truetype(candidate, size)
            break
        except OSError:
            continue
    if loaded is None:  # pragma: no cover - depends on the system
        try:
            loaded = ImageFont.load_default(size=size)
        except TypeError:  # Pillow < 10.1
            loaded = ImageFont.load_default()
    _FONT_CACHE[(kind, size)] = loaded
    return loaded


def _direction(src_r: int, src_c: int, dst_r: int, dst_c: int) -> int | None:
    """Map a move to the engine's direction code (1 up, 2 down, 3 left, 4 right)."""
    if dst_r < src_r:
        return 1
    if dst_r > src_r:
        return 2
    if dst_c < src_c:
        return 3
    if dst_c > src_c:
        return 4
    return None


def _mix(a, b, t: float):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _darker(color, t: float):
    return _mix(color, (0, 0, 0), t)


def army_label(value: int) -> str:
    # Same abridging the browser client uses (1.2k, 34k).
    if value >= 10_000:
        return f"{round(value / 1000)}k"
    if value >= 1_000:
        return f"{value / 1000:.1f}k"
    return str(int(value))


# --------------------------------------------------------------------- options
@dataclass
class VideoOptions:
    """Look and feel of the rendered video."""

    cell: int = 34                 # cell size in the final (downscaled) frame
    scale: int = 2                 # supersampling factor while drawing
    fps: int = 12
    frames_per_turn: int = 2       # output repeats per recorded half-turn frame
    hold_first: float = 1.0        # seconds the opening frame stays up
    hold_last: float = 2.5         # seconds the final frame stays up
    view: str = "all"              # "seat0", "seat1" or "all" (omniscient)
    show_moves: bool = True        # draw an arrow for the last move
    show_result: bool = True       # end card with the result
    title: str | None = None

    def __post_init__(self) -> None:
        if self.view not in ("seat0", "seat1", "all"):
            raise ValueError("view must be 'seat0', 'seat1' or 'all'")
        if self.fps < 1:
            raise ValueError("fps must be >= 1")
        if self.frames_per_turn < 1:
            raise ValueError("frames_per_turn must be >= 1")
        if self.cell < 8:
            raise ValueError("cell must be >= 8")

    @property
    def seat(self) -> int | None:
        if self.view == "seat0":
            return 0
        if self.view == "seat1":
            return 1
        return None


# -------------------------------------------------------------------- renderer
class BoardRenderer:
    """Draws one frame of a replay, browser-style, at ``opts.scale``."""

    def __init__(self, replay: Replay, opts: VideoOptions) -> None:
        self.replay = replay
        self.opts = opts
        self.ss = max(1, int(opts.scale))
        s = self.ss
        self.cell = opts.cell * s
        self.pad = 22 * s
        self.header = 78 * s
        self.footer = 46 * s
        self.board = opts.cell * replay.w * s
        self.board_h = opts.cell * replay.h * s
        self.width = self.board + 2 * self.pad
        self.height = self.header + self.board_h + self.footer + 2 * self.pad

        self.names = replay.names()
        if opts.view == "all":
            self.viewer = None
        else:
            self.viewer = 0 if opts.view == "seat0" else 1

        self.out_width = self.width // s
        self.out_height = self.height // s
        # yuv420p needs even dimensions
        if self.out_width % 2:
            self.out_width -= 1
        if self.out_height % 2:
            self.out_height -= 1

        title = opts.title
        if title is None:
            title = f"{self.names[0]}  vs  {self.names[1]}"
        self.title = title

    # ------------------------------------------------------------------ piece
    def _cell_box(self, r: int, c: int) -> tuple[int, int, int, int]:
        cell = self.cell
        gap = max(1, int(round(cell * 0.045)))
        x = self.board_x + c * cell + gap
        y = self.board_y + r * cell + gap
        return x, y, cell - 2 * gap, cell - 2 * gap

    def _round(self, draw, box, radius, fill=None, outline=None, width=1):
        x, y, w, h = box
        draw.rounded_rectangle(
            [x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width
        )

    def _star(self, draw, cx: float, cy: float, radius: float, color):
        points = []
        for i in range(10):
            r = radius if i % 2 == 0 else radius * 0.44
            a = -np.pi / 2 + i * np.pi / 5
            points.append((cx + np.cos(a) * r, cy + np.sin(a) * r))
        draw.polygon(points, fill=color)

    def _castle(self, draw, x, y, w, h, color):
        draw.rectangle([x, y + h * 0.32, x + w, y + h], fill=color)
        draw.rectangle([x, y, x + w * 0.24, y + h * 0.36], fill=color)
        draw.rectangle([x + w * 0.38, y, x + w * 0.62, y + h * 0.36], fill=color)
        draw.rectangle([x + w * 0.76, y, x + w, y + h * 0.36], fill=color)

    def _arrow(self, draw, cx, cy, cell, direction, color):
        """A filled arrow head + shaft, centred on the source tile."""
        vec = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}.get(direction)
        if vec is None:
            return
        dx, dy = vec
        px, py = -dy, dx
        d = cell * 0.42
        tip = (cx + dx * d, cy + dy * d)
        neck = (cx + dx * d * 0.15, cy + dy * d * 0.15)
        tail = (cx - dx * d * 0.95, cy - dy * d * 0.95)
        head_w = d * 0.42
        shaft_w = d * 0.15
        draw.polygon([tip, (neck[0] + px * head_w, neck[1] + py * head_w),
                      (neck[0] - px * head_w, neck[1] - py * head_w)], fill=color)
        draw.polygon([(neck[0] + px * shaft_w, neck[1] + py * shaft_w),
                      (tail[0] + px * shaft_w, tail[1] + py * shaft_w),
                      (tail[0] - px * shaft_w, tail[1] - py * shaft_w),
                      (neck[0] - px * shaft_w, neck[1] - py * shaft_w)], fill=color)

    # ------------------------------------------------------------- components
    def _draw_header(self, draw: ImageDraw.ImageDraw, frame: dict, replay: Replay, index: int):
        s = self.ss
        x0 = self.pad
        y0 = int(self.pad * 0.55)
        draw.text((x0, y0), self.title, font=font("bold", 20 * s), fill=TEXT)

        scores = replay.scores(index)
        land = scores["land"]
        total = max(1, land[0] + land[1])
        bar_y = y0 + 34 * s
        bar_h = 8 * s
        bar_w = self.board
        left_w = int(bar_w * land[0] / total)
        draw.rounded_rectangle(
            [x0, bar_y, x0 + bar_w, bar_y + bar_h], radius=bar_h // 2, fill=(30, 39, 54)
        )
        if left_w > 0:
            draw.rounded_rectangle(
                [x0, bar_y, x0 + max(left_w, bar_h), bar_y + bar_h],
                radius=bar_h // 2,
                fill=SEAT_COLORS[0],
            )
        if left_w < bar_w:
            draw.rounded_rectangle(
                [x0 + left_w, bar_y, x0 + bar_w, bar_y + bar_h],
                radius=bar_h // 2,
                fill=SEAT_COLORS[1],
            )

        label_y = bar_y + bar_h + 10 * s
        stat_font = font("bold", 14 * s)
        labels = {}
        for seat in (0, 1):
            name = self.names[seat] if seat < len(self.names) else f"player {seat}"
            if self.viewer is not None:
                name = ("You · " if seat == self.viewer else "Enemy · ") + name
            labels[seat] = [
                f"{name} · {land[seat]} land · {scores['army'][seat]} army",
                f"{name} · {scores['army'][seat]} army",
                f"{name} · {scores['army'][seat]}",
                name,
            ]
        # longest wording that still leaves a comfortable gap between the seats
        gap = 14 * s
        chosen = labels[0][-1], labels[1][-1]
        for left, right in zip(labels[0], labels[1]):
            widths = draw.textlength(left, font=stat_font) + draw.textlength(
                right, font=stat_font
            )
            chosen = (left, right)
            if widths + gap <= bar_w:
                break
        left_text, right_text = chosen
        draw.text((x0, label_y), left_text, font=stat_font, fill=SEAT_LIGHT[0])
        tw = draw.textlength(right_text, font=stat_font)
        draw.text((x0 + bar_w - tw, label_y), right_text, font=stat_font,
                  fill=SEAT_LIGHT[1])
        del frame

    def _draw_footer(self, draw: ImageDraw.ImageDraw, frame: dict, replay: Replay):
        s = self.ss
        y = self.board_y + self.board_h + 14 * s
        turn = int(frame["t"])
        turn_text = f"turn {turn}"
        if replay.moves_per_turn == 2 and turn > 0:
            move_slot = 1 if int(frame.get("half_turn", 0)) else 2
            turn_text += f" · move {move_slot}/2"
        if replay.max_turns:
            turn_text += f" / {replay.max_turns}"
        draw.text((self.pad, y), turn_text, font=font("bold", 16 * s), fill=TEXT)

        bits = []
        if self.viewer is None:
            bits.append("full board")
        else:
            bits.append("fog of war" if replay.fog else "full board")
        if frame.get("done"):
            bits.append("final")
        label = "  ·  ".join(bits)
        width = draw.textlength(label, font=font("regular", 14 * s))
        draw.text((self.width - self.pad - width, y + 2 * s), label,
                  font=font("regular", 14 * s), fill=MUTED)

    def _draw_result(self, draw: ImageDraw.ImageDraw, replay: Replay):
        s = self.ss
        winner = int(replay.result.get("winner", -1))
        reason = str(replay.result.get("reason", ""))
        turns = int(replay.result.get("turns", 0))

        if winner < 0:
            headline, color = "Draw", MUTED
        elif self.viewer is None:
            name = self.names[winner] if winner < len(self.names) else f"player {winner}"
            headline, color = f"{name} wins", SEAT_LIGHT[winner]
        elif winner == self.viewer:
            headline, color = "Victory", SEAT_LIGHT[self.viewer]
        else:
            headline, color = "Defeat", SEAT_LIGHT[1 - self.viewer]

        cx = self.width // 2
        cy = self.board_y + self.board_h // 2
        panel_w = int(self.board * 0.86)
        panel_h = 124 * s
        overlay = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle([0, 0, panel_w - 1, panel_h - 1], radius=18 * s,
                             fill=(10, 14, 20, 244), outline=(52, 68, 94, 255),
                             width=2 * s)
        headline_font = font("bold", 30 * s)
        width = od.textlength(headline, font=headline_font)
        od.text(((panel_w - width) / 2, 26 * s), headline, font=headline_font,
                fill=color)
        sub = f"{reason}  ·  turn {turns}"
        sub_font = font("regular", 16 * s)
        width = od.textlength(sub, font=sub_font)
        od.text(((panel_w - width) / 2, 74 * s), sub, font=sub_font, fill=MUTED)
        draw._image.paste(overlay, (cx - panel_w // 2, cy - panel_h // 2), overlay)

    # ---------------------------------------------------------------- one frame
    def draw(self, index: int) -> Image.Image:
        replay = self.replay
        opts = self.opts
        s = self.ss
        frame = replay.frames[index]
        owner = replay.frame_owner(index)
        army = replay.frame_army(index)
        city = replay.frame_city(index) != 0
        generals = replay.generals(index)
        vis = (
            np.ones((replay.h, replay.w), dtype=bool)
            if self.viewer is None
            else replay.visible(index, self.viewer)
        )

        # tiles that changed since the previous frame get a short white flash
        changed = np.zeros_like(owner, dtype=bool)
        if index > 0:
            prev_owner = replay.frame_owner(index - 1)
            prev_army = replay.frame_army(index - 1)
            changed = (prev_owner != owner) | (prev_army != army)
            changed &= vis

        image = Image.new("RGB", (self.width, self.height), BG)
        draw = ImageDraw.Draw(image, "RGBA")

        # panel behind the board
        self.board_x = self.pad
        self.board_y = self.pad + self.header
        draw.rounded_rectangle(
            [self.board_x - 6 * s, self.board_y - 6 * s,
             self.board_x + self.board + 6 * s, self.board_y + self.board_h + 6 * s],
            radius=14 * s,
            fill=BOARD,
        )

        cell = self.cell
        radius = max(2, int(cell * 0.16))
        for r in range(replay.h):
            for c in range(replay.w):
                box = self._cell_box(r, c)
                x, y, w, h = box
                if not vis[r, c]:
                    self._round(draw, box, radius, fill=FOG)
                    if int(owner[r, c]) == MOUNTAIN or city[r, c]:
                        pad = cell * 0.24
                        draw.polygon(
                            [(x + w / 2, y + pad), (x + w - pad, y + h - pad), (x + pad, y + h - pad)],
                            fill=(255, 255, 255, 26),
                        )
                        draw.polygon(
                            [
                                (x + w / 2, y + pad),
                                (x + w / 2 + cell * 0.15, y + pad + cell * 0.26),
                                (x + w / 2 - cell * 0.15, y + pad + cell * 0.26),
                            ],
                            fill=(255, 255, 255, 46),
                        )
                    else:
                        dot = max(1.5, cell * 0.05)
                        draw.ellipse(
                            [x + w / 2 - dot, y + h / 2 - dot, x + w / 2 + dot, y + h / 2 + dot],
                            fill=(255, 255, 255, 14),
                        )
                    continue

                value = int(owner[r, c])
                if value == MOUNTAIN:
                    self._round(draw, box, radius, fill=MOUNTAIN_FILL)
                    pad = cell * 0.24
                    draw.polygon(
                        [(x + w / 2, y + pad), (x + w - pad, y + h - pad), (x + pad, y + h - pad)],
                        fill=(255, 255, 255, 26),
                    )
                    draw.polygon(
                        [
                            (x + w / 2, y + pad),
                            (x + w / 2 + cell * 0.15, y + pad + cell * 0.26),
                            (x + w / 2 - cell * 0.15, y + pad + cell * 0.26),
                        ],
                        fill=(255, 255, 255, 46),
                    )
                    continue

                if value == NEUTRAL:
                    fill = NEUTRAL_FILL
                elif value in (0, 1):
                    fill = SEAT_COLORS[value]
                else:
                    fill = NEUTRAL_FILL
                self._round(draw, box, radius, fill=fill)

                light_tile = value == NEUTRAL
                if city[r, c]:
                    self._castle(
                        draw,
                        x + w * 0.15,
                        y + h * 0.16,
                        w * 0.7,
                        h * 0.7,
                        (10, 15, 22, 52) if light_tile else (255, 255, 255, 66),
                    )
                    inset = max(1, int(cell * 0.07))
                    self._round(
                        draw,
                        (x + inset, y + inset, w - 2 * inset, h - 2 * inset),
                        max(2, int(radius * 0.7)),
                        outline=GOLD + (230,),
                        width=max(1, int(cell * 0.045)),
                    )

                general_seat = None
                for seat in range(2):
                    if generals[seat] == [r, c]:
                        general_seat = seat
                        break
                if general_seat is not None:
                    color = (10, 15, 22, 62) if light_tile else (255, 255, 255, 92)
                    self._star(draw, x + w / 2, y + h / 2, cell * 0.36, color)
                    self._star(draw, x + w * 0.23, y + h * 0.24, cell * 0.14,
                               (10, 15, 22, 150) if light_tile else (255, 255, 255, 240))

                if army[r, c] > 0:
                    label = army_label(int(army[r, c]))
                    base = cell * (0.36 if len(label) >= 3 else 0.46)
                    size = max(7, int(base))
                    f = font("bold", size)
                    cx = x + w / 2
                    cy = y + h / 2 + cell * 0.02
                    tw = draw.textlength(label, font=f)
                    if light_tile:
                        draw.text((cx - tw / 2, cy), label, font=f, fill=TEXT_DARK,
                                  anchor="lm")
                    else:
                        draw.text((cx - tw / 2, cy), label, font=f, fill=TEXT,
                                  anchor="lm",
                                  stroke_width=max(1, int(cell * 0.07)),
                                  stroke_fill=(6, 10, 16, 210))

                if changed[r, c]:
                    self._round(draw, box, radius, fill=(255, 255, 255, 34))

        # the general of the seat we are watching gets a soft ring
        if self.viewer is not None and generals[self.viewer] is not None:
            gr, gc = generals[self.viewer]
            box = self._cell_box(gr, gc)
            self._round(
                draw,
                box,
                radius,
                outline=SEAT_LIGHT[self.viewer] + (150,),
                width=max(2, int(cell * 0.12)),
            )

        # last-move arrows
        if opts.show_moves and index > 0:
            for move in frame.get("moves") or []:
                if not move:
                    continue
                start = int(move["from"])
                src_r, src_c = divmod(start, replay.w)
                dst_r, dst_c = divmod(int(move["to"]), replay.w)
                direction = _direction(src_r, src_c, dst_r, dst_c)
                if direction is None or not vis[src_r, src_c]:
                    continue
                cx = self.board_x + src_c * cell + cell / 2
                cy = self.board_y + src_r * cell + cell / 2
                alpha = 250 if move.get("half") else 225
                self._arrow(draw, cx, cy, cell, direction, (255, 255, 255, alpha))

        self._draw_header(draw, frame, replay, index)
        self._draw_footer(draw, frame, replay)
        if opts.show_result and index == len(replay.frames) - 1:
            self._draw_result(draw, replay)

        if s != 1:
            image = image.resize((self.out_width, self.out_height), Image.LANCZOS)
        return image


# ---------------------------------------------------------------- frame timing
def frame_plan(replay: Replay, opts: VideoOptions) -> list[int]:
    """Replay indices for the video, repeated to give each half-turn screen time."""
    if not len(replay):
        raise ValueError("replay has no frames")
    plan: list[int] = [0] * max(1, int(round(opts.hold_first * opts.fps)))
    for index in range(len(replay)):
        plan.extend([index] * opts.frames_per_turn)
    plan.extend([len(replay) - 1] * max(1, int(round(opts.hold_last * opts.fps))))
    return plan


def iter_frames(replay: Replay, opts: VideoOptions) -> Iterator[Image.Image]:
    renderer = BoardRenderer(replay, opts)
    cache: dict[int, Image.Image] = {}
    for index in frame_plan(replay, opts):
        image = cache.get(index)
        if image is None:
            image = renderer.draw(index)
            # only the last frame is worth remembering (intro / outro repeat)
            if len(cache) > 2:
                cache.clear()
            cache[index] = image
        yield image


# ----------------------------------------------------------------------- video
def find_ffmpeg() -> str | None:
    """Locate an ffmpeg binary (``imageio-ffmpeg`` first, then ``PATH``)."""
    try:  # pragma: no cover - optional dependency
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    return shutil.which("ffmpeg")


def render_mp4(
    replay: Replay,
    out_path: str | Path,
    opts: VideoOptions,
    ffmpeg: str | None = None,
) -> Path:
    """Encode the replay as an H.264 MP4 (silent)."""
    ffmpeg = ffmpeg or find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg not found -- `pip install imageio-ffmpeg` (or install ffmpeg), "
            "or write a GIF instead (--format gif)"
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    renderer = BoardRenderer(replay, opts)
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{renderer.out_width}x{renderer.out_height}",
        "-r", str(opts.fps), "-i", "-",
        "-an", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-vcodec", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for image in iter_frames(replay, opts):
            proc.stdin.write(image.tobytes())
    finally:
        proc.stdin.close()
    stderr = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed: {stderr.strip()[:800]}")
    return out_path


def render_gif(replay: Replay, out_path: str | Path, opts: VideoOptions) -> Path:
    """Encode the replay as an animated GIF (bigger, but always available)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames = list(iter_frames(replay, opts))
    duration = max(20, int(round(1000 / opts.fps)))
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        optimize=True,
    )
    return out_path


def render_replay(
    replay: Replay,
    out_path: str | Path,
    opts: VideoOptions | None = None,
    fmt: str | None = None,
) -> Path:
    """Render ``replay`` to ``out_path``; ``fmt`` overrides the suffix."""
    opts = opts or VideoOptions()
    out_path = Path(out_path)
    fmt = (fmt or out_path.suffix.lstrip(".") or "mp4").lower()
    if fmt in ("mp4", "m4v", "mov"):
        return render_mp4(replay, out_path, opts)
    if fmt in ("gif", "webp"):
        if fmt != "gif":
            out_path = out_path.with_suffix(".gif")
        return render_gif(replay, out_path, opts)
    raise ValueError(f"unsupported video format {fmt!r} (use mp4 or gif)")


# ------------------------------------------------------------------------- cli
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="python -m src.video",
        description="Render a saved generals-gym replay to an MP4 video or a GIF.",
    )
    ap.add_argument("replay", help="replay JSON written by --save-replay")
    ap.add_argument("-o", "--out", default=None,
                    help="output file (default: <replay>.mp4)")
    ap.add_argument("--format", choices=["mp4", "gif"], default=None,
                    help="output format (default: from the file suffix)")
    ap.add_argument("--view", choices=["seat0", "seat1", "all"], default="all",
                    help="whose eyes to watch through (default all)")
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--frames-per-turn", type=int, default=2,
                    help="repeat each half-turn state this many output frames (default 2)")
    ap.add_argument("--cell", type=int, default=34, help="tile size in pixels")
    ap.add_argument("--hold-first", type=float, default=1.0)
    ap.add_argument("--hold-last", type=float, default=2.5)
    ap.add_argument("--no-moves", action="store_true", help="do not draw move arrows")
    ap.add_argument("--title", default=None, help="override the header title")
    ap.add_argument("--max-frames", type=int, default=None,
                    help="stop after this many replay frames (for a quick preview)")
    return ap


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    replay = Replay.load(args.replay)
    if args.max_frames is not None and args.max_frames < 1:
        raise ValueError("--max-frames must be positive")
    if args.max_frames is not None and args.max_frames < len(replay):
        replay.frames = replay.frames[: args.max_frames]
    opts = VideoOptions(
        cell=args.cell,
        fps=args.fps,
        frames_per_turn=args.frames_per_turn,
        hold_first=args.hold_first,
        hold_last=args.hold_last,
        view=args.view,
        show_moves=not args.no_moves,
        title=args.title,
    )
    out = args.out or str(Path(args.replay).with_suffix(".mp4"))
    frames = len(frame_plan(replay, opts))
    print(
        f"rendering {len(replay)} replay frames ({frames} video frames, "
        f"{frames / opts.fps:.1f}s at {opts.fps} fps) -> {out}",
        flush=True,
    )
    path = render_replay(replay, out, opts, fmt=args.format)
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
