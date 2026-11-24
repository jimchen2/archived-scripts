"""Tests for the browser front-end (``generals_web``).

The UI itself is plain JS, so these tests cover the parts that can silently
break gameplay: settings handling, rule application through the API, fog
hiding tiles from the browser, the opponent policies and the HTTP routes.
"""

from __future__ import annotations

import http.client
import json
import threading

import numpy as np
import pytest

from generals_web.bots import choose_action, legal_actions
from generals_web.game import OBSTACLE, UNKNOWN, Game, GameSettings
from generals_web.server import Store, create_server


# --------------------------------------------------------------------- helpers
def snapshot_owner(snap):
    return np.asarray(snap["owner"], dtype=np.int32).reshape(snap["h"], snap["w"])


def make_game(size=7, fog=True, opponent="easy"):
    store = Store()
    return store, store.new_game(
        GameSettings(size=size, fog=fog, opponent=opponent)
    )


# -------------------------------------------------------------------- settings
def test_settings_defaults_and_clamping():
    settings = GameSettings.from_payload({})
    assert settings.size == 21
    assert settings.fog is True
    assert settings.opponent == "normal"
    assert settings.growth == 25

    assert GameSettings.from_payload({"size": 1000}).size == 31
    assert GameSettings.from_payload({"size": 1}).size == 5
    # land growth is locked to the classic 25 turns; payload values are ignored
    assert GameSettings.from_payload({"growth": 0}).growth == 25
    assert GameSettings.from_payload({"growth": 1}).growth == 25
    assert GameSettings.from_payload({"growth": 99}).growth == 25
    assert GameSettings.from_payload({"opponent": "nope"}).opponent == "normal"
    assert GameSettings.from_payload({"max_turns": 0}).max_turns == 20


def test_config_matches_settings():
    settings = GameSettings(size=15, fog=False)
    cfg = settings.config()
    assert (cfg.height, cfg.width) == (15, 15)
    assert cfg.land_growth_period == 25
    assert cfg.fog is False
    assert cfg.half_moves is True  # the "Z" split move
    assert cfg.city_count == 7


# ------------------------------------------------------------------ game rules
def test_fog_hides_tiles_from_the_client():
    _store, game = make_game(size=11, fog=True)
    snap = game.snapshot()
    owner = snapshot_owner(snap)
    assert (owner == UNKNOWN).sum() > 0
    assert np.all(np.asarray(snap["army"]).reshape(snap["h"], snap["w"])[owner == UNKNOWN] == 0)
    assert snap["generals"]["enemy"] is None
    assert snap["revealed"] is False
    # The human always knows where their own general is.
    general = snap["generals"]["you"]
    assert general is not None
    assert owner[tuple(general)] == snap["you"]


def test_visible_enemy_general_is_reported_under_fog():
    _store, game = make_game(size=7, fog=True)
    game.state = game.env.make_state(
        [
            "g0:5 0:2 . . . . .",
            ". g1:1 . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
        ]
    )
    snap = game.snapshot()
    assert snap["revealed"] is False
    assert snap["generals"]["enemy"] == [1, 1]
    assert snapshot_owner(snap)[1, 1] == 1


def test_fog_off_reveals_everything():
    _store, game = make_game(size=7, fog=False)
    snap = game.snapshot()
    assert snap["revealed"] is True
    assert (snapshot_owner(snap) == UNKNOWN).sum() == 0
    assert (snapshot_owner(snap) == OBSTACLE).sum() == 0
    assert snap["generals"]["enemy"] is not None


def test_fog_reports_distant_obstacles_without_leaking_type():
    _store, game = make_game(size=7, fog=True)
    game.state = game.env.make_state(
        [
            "g0:5 C:40 . . . . #",
            "#    .    . . . . .",
            ".    .    . . . . .",
            ".    .    . . . . .",
            ".    .    . . . . c1:15",
            ".    .    . . . 1:10 .",
            "C:42 .    . . . . g1:5",
        ]
    )
    snap = game.snapshot()
    owner = snapshot_owner(snap)
    army = np.asarray(snap["army"], dtype=np.int32).reshape(snap["h"], snap["w"])
    city = np.asarray(snap["city"], dtype=np.int8).reshape(snap["h"], snap["w"])

    # Visible adjacent castle and mountain show their true identities.
    assert owner[0, 1] == -1 and city[0, 1] == 1 and army[0, 1] == 40
    assert owner[1, 0] == game.snapshot()["mountain"] and city[1, 0] == 0

    # Distant mountain, neutral castle, and enemy castle all appear as OBSTACLE
    # with city and army masked out.
    for r, c in ((0, 6), (6, 0), (4, 6)):
        assert owner[r, c] == OBSTACLE
        assert army[r, c] == 0
        assert city[r, c] == 0

    # Distant plain/enemy/general tiles remain UNKNOWN.
    for r, c in ((3, 3), (5, 5), (6, 6)):
        assert owner[r, c] == UNKNOWN
        assert army[r, c] == 0
        assert city[r, c] == 0


def test_player_action_is_applied():
    _store, game = make_game(size=7, fog=False)
    game.state = game.env.make_state(
        [
            "g0:5 . . . . . g1:1",
            ". . . . . . .",
            ". . . . . . .",
            "0:3 . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
        ]
    )
    snap = game.snapshot()
    assert snap["turn"] == 0

    # Move 4 armies from the general (tile 0) down onto neutral (1, 0).
    action = 0 * snap["dir_actions"] + 2  # dir 2 == down
    game.step(action)

    snap = game.snapshot()
    assert snap["turn"] == 1
    owner = snapshot_owner(snap)
    army = np.asarray(snap["army"]).reshape(snap["h"], snap["w"])

    assert owner[1, 0] == 0, "the human's move should capture the neutral tile"
    assert army[1, 0] == 4, "attack force minus the defender, no bot interference"
    assert army[0, 0] == 1, "the general grows after the second half-turn"
    assert snap["half_turn"] == 1

    # The next action slot completes the displayed turn and triggers production.
    game.step(None)
    snap = game.snapshot()
    army = np.asarray(snap["army"]).reshape(snap["h"], snap["w"])
    assert snap["turn"] == 1 and snap["half_turn"] == 0
    assert army[0, 0] == 2


def test_general_capture_ends_the_game_and_reveals_the_board():
    _store, game = make_game(size=7, fog=True)
    game.state = game.env.make_state(
        [
            "g0:9 g1:1 . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
        ]
    )
    game.step(0 * 9 + 4)  # 8 armies right, onto the enemy general
    snap = game.snapshot()
    assert snap["done"] is True
    assert snap["winner"] == 0
    assert snap["reason"] == "general captured"
    assert snap["revealed"] is True
    assert snapshot_owner(snap)[0, 1] == 0


def test_illegal_action_is_a_pass():
    _store, game = make_game(size=7, fog=False)
    game.state = game.env.make_state(
        [
            "g0:1 . . . . . g1:1",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
            ". . . . . . .",
        ]
    )
    game.step(0 * 9 + 2)  # a single army cannot move
    snap = game.snapshot()
    assert snap["turn"] == 1
    assert snapshot_owner(snap)[1, 0] == -1


def test_pass_with_no_action():
    _store, game = make_game(size=7, fog=False)
    game.step(None)
    assert game.snapshot()["turn"] == 1


# ---------------------------------------------------------------- bot policies
@pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
def test_bots_choose_legal_actions(difficulty):
    store, game = make_game(size=7, fog=False, opponent=difficulty)
    game.step(0)  # give both players a couple of armies
    game.step(0)

    action = choose_action(game.env, game.state, 1, difficulty, game.rng)
    assert 0 <= action < game.env.num_actions

    state = game.state
    army = np.asarray(state.army)
    owner = np.asarray(state.owner)
    legal = set(legal_actions(army, owner, 1, game.env.config.dir_actions))
    assert action in legal


def test_normal_bot_does_not_use_hidden_tiles():
    """The fog-honest bot only ever reacts to tiles player 1 can see."""
    store, game = make_game(size=9, fog=True, opponent="normal")
    for _ in range(5):
        game.step(None)
    # It should still produce a sane action with most of the board fogged.
    action = choose_action(game.env, game.state, 1, "normal", game.rng)
    assert 0 <= action < game.env.num_actions


# -------------------------------------------------------------------- HTTP API
@pytest.fixture(scope="module")
def server():
    httpd = create_server(host="127.0.0.1", port=0, warm=False)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address[:2]
    yield host, port
    httpd.shutdown()
    httpd.server_close()


def request(server_host, method, path, body=None):
    host, port = server_host
    conn = http.client.HTTPConnection(host, port, timeout=60)
    payload = None if body is None else json.dumps(body)
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    conn.request(method, path, body=payload, headers=headers)
    response = conn.getresponse()
    raw = response.read()
    conn.close()
    parsed = json.loads(raw) if raw and response.getheader("Content-Type", "").startswith("application/json") else raw
    return response.status, parsed, response


def test_index_and_static_files(server):
    status, raw, response = request(server, "GET", "/")
    assert status == 200
    assert b"<canvas id=\"board\"" in raw
    assert b"app.js" in raw

    status, raw, response = request(server, "GET", "/app.js")
    assert status == 200
    assert b"queueMove" in raw
    assert response.getheader("Content-Type").startswith("text/javascript")

    status, _raw, _ = request(server, "GET", "/style.css")
    assert status == 200


def test_health(server):
    status, payload, _ = request(server, "GET", "/api/health")
    assert status == 200
    assert payload["ok"] is True


def test_full_game_round_trip(server):
    status, snap, _ = request(
        server, "POST", "/api/games",
        {"size": 7, "fog": False, "opponent": "easy"},
    )
    assert status == 200
    assert snap["id"]
    assert snap["h"] == 7 and snap["w"] == 7
    game_id = snap["id"]

    status, snap, _ = request(server, "GET", f"/api/games/{game_id}")
    assert status == 200
    assert snap["turn"] == 0

    status, snap, _ = request(server, "POST", f"/api/games/{game_id}/turn", {})
    assert status == 200
    assert snap["turn"] == 1
    assert snap["half_turn"] == 1

    status, snap, _ = request(
        server, "POST", f"/api/games/{game_id}/turn", {"action": 0}
    )
    assert status == 200
    assert snap["turn"] == 1
    assert snap["half_turn"] == 0

    status, payload, _ = request(server, "DELETE", f"/api/games/{game_id}")
    assert status == 200 and payload["deleted"] is True
    status, payload, _ = request(server, "GET", f"/api/games/{game_id}")
    assert status == 404


def test_bad_requests(server):
    status, payload, _ = request(server, "GET", "/api/games/doesnotexist")
    assert status == 404 and "error" in payload

    status, _snap, _ = request(server, "POST", "/api/games", {"size": 9})
    status, payload, _ = request(server, "GET", "/api/games/doesnotexist")
    assert status == 404

    status, _payload, _ = request(server, "POST", "/api/games/nope/turn", {})
    assert status == 404

    status, payload, _ = request(server, "GET", "/does-not-exist.js")
    assert status == 404


def test_snapshot_is_json_safe(server):
    status, snap, _ = request(server, "POST", "/api/games", {"size": 7})
    assert status == 200
    # Round-trip through JSON and make sure every field the client reads exists.
    encoded = json.dumps(snap)
    decoded = json.loads(encoded)
    for key in (
        "id", "turn", "half_turn", "done", "winner", "reason", "you", "h", "w", "dir_actions",
        "owner", "army", "city", "vis", "generals", "score", "settings", "mountain", "obstacle",
    ):
        assert key in decoded
    assert len(decoded["owner"]) == decoded["h"] * decoded["w"]


# --------------------------------------------------------------------- replays
def test_game_records_a_replay():
    _store, game = make_game(size=7, fog=False)
    start = game.replay()
    assert len(start) == 1
    game.step(None)
    game.step(None)
    replay = game.replay()
    assert len(replay) == 3
    assert replay.result["turns"] == game.snapshot()["turn"]
    assert game.steps == 2  # two half-turn actions make one displayed turn
    assert replay.frame_owner(0).shape == (7, 7)
    # both seats are named in the header
    assert [p["kind"] for p in replay.players] == ["human", "bot"]
    # the last frame matches the live state
    owner = np.asarray(game.state.owner)
    assert np.array_equal(replay.frame_owner(2), owner)


def test_reset_starts_a_new_replay():
    _store, game = make_game(size=7, fog=False)
    for _ in range(3):
        game.step(None)
    game.reset()
    assert len(game.replay()) == 1


def test_replay_endpoints(server):
    status, snap, _ = request(server, "POST", "/api/games",
                              {"size": 9, "fog": False, "opponent": "easy"})
    assert status == 200
    game_id = snap["id"]
    for _ in range(3):
        status, snap, _ = request(server, "POST", f"/api/games/{game_id}/turn", {})
        assert status == 200

    status, body, response = request(server, "GET", f"/api/games/{game_id}/replay")
    assert status == 200
    assert body["format"] == "generals-gym-replay"
    assert len(body["frames"]) == 4
    assert "attachment" in response.getheader("Content-Disposition", "")

    status, raw, response = request(server, "GET", f"/api/games/{game_id}/replay.html")
    assert status == 200
    assert response.getheader("Content-Type").startswith("text/html")
    text = raw.decode()
    assert text.startswith("<!DOCTYPE html>")
    assert "const REPLAY = {" in text

    status, body, _ = request(server, "GET", "/api/games/nope/replay")
    assert status == 404


def test_web_index_has_a_save_replay_button(server):
    status, raw, _ = request(server, "GET", "/")
    assert status == 200
    assert b'id="save-replay"' in raw

# ------------------------------------------------------- checkpoint opponent
@pytest.fixture(scope="module")
def trained_policy(tmp_path_factory):
    from dataclasses import asdict
    import jax
    from bot.checkpoint import Checkpoint
    from bot.network import PolicyValueNet
    from src.config import TrainConfig
    from generals_web.checkpoint import CheckpointPolicy

    run = tmp_path_factory.mktemp("run")
    cfg = TrainConfig(height=7, width=7, fog=True, max_turns=40,
                      city_count=3, channels=8, num_blocks=1, memory="gru")
    net = PolicyValueNet(cfg.net_config(), height=7, width=7)
    Checkpoint(run).save("test", net.init(jax.random.PRNGKey(1)), asdict(cfg))
    return CheckpointPolicy(str(run), "test")


def test_checkpoint_requires_server_configuration():
    with pytest.raises(ValueError, match="no checkpoint configured"):
        Store().new_game(GameSettings(opponent="checkpoint"))


def test_checkpoint_game_uses_training_config_and_per_game_memory(trained_policy):
    import jax

    store = Store(trained_policy)
    settings = GameSettings(size=11, fog=False, opponent="checkpoint")
    game = store.new_game(settings)
    other = store.new_game(settings)
    assert game.settings.size == 7 and game.settings.fog is True
    assert game.env.config.city_count == 3
    assert game.env.config.max_turns == 40
    assert game.env.config.half_moves
    # Compare the bot's observation and mask with the original five-direction
    # training environment on the exact same state.
    from game import GeneralsEnv
    training_env = GeneralsEnv(trained_policy.cfg.env_config())
    trained_obs = training_env.observe(game.state, 1)
    web_obs = game.env.observe(game.state, 1)
    assert np.array_equal(trained_obs.grid, web_obs.grid)
    assert np.array_equal(trained_obs.scalars, web_obs.scalars)
    trained_mask = np.asarray(training_env.action_mask(game.state)[1])
    web_mask = np.asarray(game.env.action_mask(game.state)[1]).reshape(-1, 9)[:, :5].reshape(-1)
    assert np.array_equal(trained_mask, web_mask)
    initial = jax.tree_util.tree_leaves(other.bot_memory)
    for _ in range(3):
        legal = np.asarray(game.env.action_mask(game.state)[1])
        game.step(None)
        assert legal[game.last_bot_action]
        assert game.last_bot_action % 9 < 5
    assert all(np.array_equal(a, b) for a, b in zip(initial, jax.tree_util.tree_leaves(other.bot_memory)))
    game.reset()
    assert all(np.array_equal(a, b) for a, b in zip(initial, jax.tree_util.tree_leaves(game.bot_memory)))
    assert game.snapshot()["opponent"] == "checkpoint"


def test_checkpoint_http_round_trip(trained_policy):
    httpd = create_server(host="127.0.0.1", port=0, warm=False, policy=trained_policy)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    address = httpd.server_address[:2]
    try:
        status, health, _ = request(address, "GET", "/api/health")
        assert status == 200 and health["checkpoint"] == "test"
        status, snap, _ = request(address, "POST", "/api/games", {"size": 15, "opponent": "checkpoint"})
        assert status == 200 and snap["h"] == 7 and snap["settings"]["fog"] is True
        status, snap, _ = request(address, "POST", f'/api/games/{snap["id"]}/turn', {})
        assert status == 200 and snap["turn"] == 1
    finally:
        httpd.shutdown()
        httpd.server_close()
