"""Tests for replay recording and rendering (``game.replay`` / ``src.video``).

The video tests only touch the frame planner and a couple of decoded frames, so
they need nothing but Pillow; the ffmpeg encode is skipped when ffmpeg is not
installed.
"""

from __future__ import annotations

import json
import shutil

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from game import EnvConfig, GeneralsEnv
from game.replay import (
    FORMAT,
    Replay,
    ReplayRecorder,
    decode_rle,
    encode_rle,
)
from game.replay_html import player_html, write_html_player
from src.video import (
    BoardRenderer,
    VideoOptions,
    find_ffmpeg,
    frame_plan,
    render_gif,
    render_replay,
)


# --------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def game():
    """A short greedy-vs-random game on an 11x11 fogged board."""
    from bot.baselines import greedy_action

    cfg = EnvConfig(height=11, width=11, city_count=5, max_turns=60)
    env = GeneralsEnv(cfg, map_pool_size=0, seed=3)
    state = env.reset(jax.random.PRNGKey(3))
    recorder = ReplayRecorder(
        cfg,
        players=[("greedy", "bot"), ("random", "bot")],
        seed=3,
        meta={"source": "test"},
    )
    recorder.add(state)

    key = jax.random.PRNGKey(7)
    for _ in range(2 * cfg.max_turns):
        key, sub = jax.random.split(key)
        actions = jnp.stack(
            [greedy_action(state, 0, cfg, env.tables), env.sample_actions(sub, state)[1]]
        )
        state, rewards, info = env.step(state, actions)
        recorder.add(state, actions=actions, rewards=rewards)
        if bool(info["done"]):
            break
    recorder.result()
    return recorder, env, state


@pytest.fixture(scope="module")
def replay(game):
    recorder, _env, _state = game
    return Replay.from_dict(recorder.to_dict())


# ----------------------------------------------------------------- run-length
def test_rle_roundtrip():
    values = [0, 0, 0, -1, -2, -2, 1, 1, 1, 1]
    encoded = encode_rle(values)
    assert encoded == [[0, 3], [-1, 1], [-2, 2], [1, 4]]
    assert decode_rle(encoded, len(values)).tolist() == values


def test_rle_rejects_wrong_length():
    with pytest.raises(ValueError):
        decode_rle([[0, 2]], 5)


# -------------------------------------------------------------------- recorder
def test_recorder_header_and_frames(game):
    recorder, env, _state = game
    payload = recorder.to_dict()
    assert payload["format"] == FORMAT
    assert payload["game"]["h"] == env.config.height
    assert payload["game"]["w"] == env.config.width
    assert payload["players"][0]["name"] == "greedy"
    assert payload["players"][1]["kind"] == "bot"
    assert payload["meta"] == {"source": "test"}
    assert len(payload["frames"]) > 1
    first = payload["frames"][0]
    assert first["t"] == 0
    assert first["half_turn"] == 0
    assert payload["game"]["moves_per_turn"] == 2
    assert sum(n for _, n in first["o"]) == env.config.num_tiles
    assert "result" in payload and "turns" in payload["result"]


def test_recorder_marks_real_moves(game):
    recorder, env, _state = game
    moves = [m for frame in recorder.frames for m in (frame.get("moves") or []) if m]
    assert moves, "expected at least one recorded move"
    for move in moves[:20]:
        src = move["from"]
        dst = move["to"]
        sr, sc = divmod(src, env.config.width)
        dr, dc = divmod(dst, env.config.width)
        assert abs(sr - dr) + abs(sc - dc) == 1  # only 4-neighbour moves


def test_recorder_records_one_move_per_seat(game):
    recorder, _env, _state = game
    for frame in recorder.frames[1:]:
        assert len(frame["moves"]) == 2
        assert len(frame["acts"]) == 2


# --------------------------------------------------------------------- Replay
def test_replay_roundtrip(replay, tmp_path):
    path = replay.save(tmp_path / "replay.json")
    again = Replay.load(path)
    assert len(again) == len(replay)
    assert again.result == replay.result
    assert again.names() == ["greedy", "random"]
    owner = again.frame_owner(0)
    assert owner.shape == (again.h, again.w)
    assert set(np.unique(owner)).issubset({-2, -1, 0, 1})
    assert again.frame_army(0).shape == owner.shape


def test_replay_scores_match_the_engine(replay, game):
    _recorder, env, state = game
    owner = np.asarray(state.owner)
    army = np.asarray(state.army)
    index = len(replay) - 1
    scores = replay.scores(index)
    assert scores["land"] == [int((owner == p).sum()) for p in range(2)]
    assert scores["army"] == [
        int(np.where(owner == p, army, 0).sum()) for p in range(2)
    ]
    assert replay.generals(index) == [
        [int(state.general[p]) // env.config.width, int(state.general[p]) % env.config.width]
        if bool(state.alive[p]) else None
        for p in range(2)
    ]


def test_replay_visibility_follows_fog(replay):
    vis = replay.visible(0, 0)
    owner = replay.frame_owner(0)
    assert vis.shape == owner.shape
    assert vis[owner == 0].all()  # you always see your own tiles
    if replay.fog:
        assert not vis.all()
    assert replay.visible(0, 0)[owner != 0].sum() >= 0


def test_replay_rejects_foreign_files(tmp_path):
    path = tmp_path / "nope.json"
    path.write_text(json.dumps({"format": "something-else"}))
    with pytest.raises(ValueError):
        Replay.load(path)
    path.write_text(json.dumps({"format": FORMAT, "version": 99, "game": {"h": 2, "w": 2}}))
    with pytest.raises(ValueError):
        Replay.load(path)


# ---------------------------------------------------------------------- video
def test_frame_plan_respects_holds(replay):
    opts = VideoOptions(fps=10, frames_per_turn=2, hold_first=0.5, hold_last=1.0)
    plan = frame_plan(replay, opts)
    assert plan[0] == 0
    assert plan[5] == 0          # 0.5s * 10fps of the opening frame
    assert plan[-1] == len(replay) - 1
    assert plan.count(0) >= 5
    assert len(plan) == 5 + 2 * len(replay) + 10


def test_board_renderer_draws_and_stays_small(replay):
    opts = VideoOptions(cell=12, scale=2, view="all")
    renderer = BoardRenderer(replay, opts)
    image = renderer.draw(0)
    assert image.size == (renderer.out_width, renderer.out_height)
    assert renderer.out_width == 12 * replay.w + 44
    assert image.mode == "RGB"
    # the board actually has colour in it (not a blank canvas)
    assert len(np.unique(np.asarray(image).reshape(-1, 3), axis=0)) > 8


def test_seat_views_differ_under_fog(game):
    recorder, _env, state = game
    replay = Replay.from_dict(recorder.to_dict())
    assert replay.fog
    seat0 = BoardRenderer(replay, VideoOptions(cell=10, view="seat0")).draw(0)
    seat1 = BoardRenderer(replay, VideoOptions(cell=10, view="seat1")).draw(0)
    assert not np.array_equal(np.asarray(seat0), np.asarray(seat1))


def test_gif_export(replay, tmp_path):
    opts = VideoOptions(cell=10, fps=10, frames_per_turn=1, hold_first=0.1,
                        hold_last=0.1)
    out = render_gif(replay, tmp_path / "game.gif", opts)
    assert out.exists() and out.stat().st_size > 1000
    from PIL import Image

    with Image.open(out) as image:
        # Pillow merges consecutive identical frames (the still intro/outro)
        assert len(replay) <= image.n_frames <= len(frame_plan(replay, opts))


@pytest.mark.skipif(not find_ffmpeg(), reason="ffmpeg is not installed")
def test_mp4_export(replay, tmp_path):
    opts = VideoOptions(cell=10, fps=10, frames_per_turn=1, hold_first=0.1,
                        hold_last=0.1)
    out = render_replay(replay, tmp_path / "game.mp4", opts)
    assert out.exists() and out.stat().st_size > 2000
    assert out.read_bytes()[4:8] == b"ftyp"  # an MP4 container


# ----------------------------------------------------------------------- html
def test_html_player_is_self_contained(replay, tmp_path):
    out = write_html_player(replay, tmp_path / "replay.html")
    html = out.read_text()
    assert html.startswith("<!DOCTYPE html>")
    assert "const REPLAY = {" in html
    assert '"greedy"' in html and '"random"' in html
    assert "http://" not in html and "https://" not in html
    assert "<script src" not in html and "<link" not in html
    # the embedded JSON parses back to the same game
    data = html.split("const REPLAY = ", 1)[1].split(";\n", 1)[0]
    payload = json.loads(data)
    assert payload["format"] == FORMAT
    assert len(payload["frames"]) == len(replay)


def test_html_player_escapes_the_title(replay):
    html = player_html(replay, title="<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in html.split("<h1>")[1].split("</h1>")[0]
    assert "&lt;script&gt;" in html


def test_html_player_rejects_empty_replay():
    recorder = ReplayRecorder(EnvConfig(height=5, width=5), players=[("a", "bot"), ("b", "bot")])
    with pytest.raises(ValueError):
        player_html(Replay.from_dict(recorder.to_dict()))


# --------------------------------------------------------------------- cli/io
def test_cli_renders_a_gif(replay, tmp_path, monkeypatch):
    from src import video as video_module

    src = tmp_path / "r.json"
    replay.save(src)
    out = tmp_path / "r.gif"
    video_module.main([str(src), "-o", str(out), "--cell", "10", "--fps", "8",
                       "--frames-per-turn", "1", "--max-frames", "6",
                       "--hold-first", "0", "--hold-last", "0"])
    assert out.exists() and out.stat().st_size > 500


def test_render_replay_rejects_unknown_format(replay, tmp_path):
    with pytest.raises(ValueError):
        render_replay(replay, tmp_path / "x.avi", VideoOptions(), fmt="avi")


def test_no_ffmpeg_message_is_actionable(replay, tmp_path, monkeypatch):
    from src import video as video_module

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    monkeypatch.setattr(video_module, "find_ffmpeg", lambda: None)
    with pytest.raises(RuntimeError, match="imageio-ffmpeg"):
        video_module.render_mp4(replay, tmp_path / "x.mp4", VideoOptions(cell=8))


# ------------------------------------------------------------------- recorder
def test_greedy_bot_passes_canonically_when_boxed_in():
    from bot.baselines import greedy_action

    cfg = EnvConfig(height=3, width=3, city_count=0, fog=False)
    env = GeneralsEnv(cfg)
    # player 0's general is walled in forever; player 1 sits in a corner
    state = env.make_state(
        [
            "g1:1 # .",
            "# g0:9 #",
            ". # .",
        ]
    )
    action = int(greedy_action(state, 0, cfg, env.tables))
    assert action == 0  # pass, not "source tile 0, direction 0"


def test_training_loop_records_replays(tmp_path):
    """--save-replay-every writes a replay next to the run directory."""
    from src.train import main as train_main

    train_main(
        [
            "--preset", "smoke",
            "--total-updates", "1",
            "--out", str(tmp_path / "run"),
            "--channels", "4",
            "--blocks", "1",
            "--num-envs", "2",
            "--rollout-len", "2",
            "--eval-games", "1",
            "--save-replay-every", "1",
        ]
    )
    replays = sorted((tmp_path / "run" / "replays").glob("*.json"))
    assert len(replays) == 1
    replay = Replay.load(replays[0])
    assert len(replay) >= 1
    assert replay.names()[1] == "greedy"
    assert replay.meta["update"] == 1


def test_html_escapes_embedded_script_data(replay):
    payload = replay.to_dict()
    payload["players"][0]["name"] = "</script><script>alert(1)</script>"
    html = player_html(Replay.from_dict(payload))
    assert "</script><script>alert(1)</script>" not in html
    assert "\\u003c/script>" in html


def test_turn_limit_winner_is_not_a_capture(game):
    recorder, _, _ = game
    frame = dict(recorder.frames[-1], done=True, winner=0,
                 alive=[1, 1], t=recorder.config.max_turns)
    original = recorder.frames
    try:
        recorder.frames = [frame]
        assert recorder.result()["reason"] == "turn limit"
    finally:
        recorder.frames = original


@pytest.mark.skipif(not find_ffmpeg(), reason="ffmpeg is not installed")
def test_mp4_odd_dimensions(replay, tmp_path):
    out = render_replay(replay, tmp_path / "odd.mp4", VideoOptions(
        cell=11, fps=10, frames_per_turn=1, hold_first=0, hold_last=0))
    assert out.stat().st_size > 2000


def test_seat_view_renders_fogged_mountains_and_castles_identically():
    cfg = EnvConfig(height=5, width=5, city_count=1, fog=True)
    env = GeneralsEnv(cfg)
    state = env.make_state(
        [
            "g0:5 . . . #",
            ".    . . . .",
            ".    . . . .",
            ".    . . . .",
            "C:40 . . . g1:5",
        ]
    )
    rec = ReplayRecorder(cfg, players=[("p0", "bot"), ("p1", "bot")])
    rec.add(state)
    replay = Replay.from_dict(rec.to_dict())
    renderer = BoardRenderer(replay, VideoOptions(cell=20, scale=1, view="seat0"))
    img = np.asarray(renderer.draw(0))

    # Compare pixel patches of distant mountain (0, 4), distant castle (4, 0),
    # and distant plain tile (2, 2).
    def patch(r, c):
        x = renderer.board_x + c * renderer.cell
        y = renderer.board_y + r * renderer.cell
        return img[y : y + renderer.cell, x : x + renderer.cell]

    assert np.array_equal(patch(0, 4), patch(4, 0))
    assert not np.array_equal(patch(0, 4), patch(2, 2))

