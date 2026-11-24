"""Tests for the policy/value network architecture."""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from bot.checkpoint import load_params, save_params
from bot.network import (
    Memory,
    NetConfig,
    PolicyValueNet,
    param_count,
    reset_memory,
)


def make_net(memory="gru", **kwargs):
    cfg = NetConfig(
        channels=kwargs.pop("channels", 8),
        num_blocks=kwargs.pop("num_blocks", 1),
        memory=memory,
        stack_frames=kwargs.pop("stack_frames", 3),
        global_context_every=kwargs.pop("global_context_every", 1),
        **kwargs,
    )
    return PolicyValueNet(cfg, grid_channels=10, num_scalars=7, height=5, width=5)


def make_inputs(net, t=4, key=jax.random.PRNGKey(0)):
    k1, k2, k3 = jax.random.split(key, 3)
    grids = jax.random.uniform(k1, (t, 10, net.height, net.width))
    scalars = jax.random.uniform(k2, (t, net.num_scalars))
    masks = jnp.ones((t, net.num_actions), dtype=bool)
    actions = jax.random.randint(k3, (t,), 0, net.num_actions)
    return grids, scalars, masks, actions


@pytest.mark.parametrize("memory", ["none", "gru", "stack"])
def test_shapes_and_param_count(memory):
    net = make_net(memory)
    params = net.init(jax.random.PRNGKey(0))
    assert param_count(params) > 0
    assert net.input_channels == 17 * (
        net.config.stack_frames if memory == "stack" else 1
    )

    grids, scalars, masks, actions = make_inputs(net)
    out = net.step(
        params, grids[0], scalars[0], masks[0], net.initial_memory(),
        key=jax.random.PRNGKey(1),
    )
    assert out.logits.shape == (net.num_actions,)
    assert out.log_prob.shape == ()
    assert out.value.shape == ()
    assert out.entropy.shape == ()
    assert out.action.shape == ()


def test_policy_head_respects_mask():
    net = make_net("none")
    params = net.init(jax.random.PRNGKey(0))
    grids, scalars, _, _ = make_inputs(net)

    mask = jnp.zeros((net.num_actions,), dtype=bool)
    mask = mask.at[7].set(True)          # only one legal action
    out = net.step(
        params, grids[0], scalars[0], mask, net.initial_memory(),
        key=jax.random.PRNGKey(1),
    )
    probs = jax.nn.softmax(out.logits)
    assert float(probs[7]) == pytest.approx(1.0, abs=1e-6)
    assert float(jnp.sum(probs) - probs[7]) == pytest.approx(0.0, abs=1e-6)
    assert int(out.action) == 7


def test_policy_logits_layout_matches_env_action_encoding():
    """Flat index ``tile * dir_actions + dir`` must match the env's layout."""
    from bot import nn

    net = make_net("none")
    params = net.init(jax.random.PRNGKey(0))
    grids, scalars, masks, _ = make_inputs(net, t=1)

    # Recompute the head by hand: its (dir, H, W) output must be transposed to
    # (H, W, dir) before flattening so index == tile * dir_actions + direction.
    h = net._trunk(params, net.encode_frame(grids[0], scalars[0]))
    h, _ = net._apply_memory(params, h, net.initial_memory())
    z = nn.silu(nn.layer_norm(params["policy"]["ln"],
                              nn.conv(params["policy"]["conv1"], h)))
    s = jnp.broadcast_to(scalars[0][:, None, None],
                         (net.num_scalars,) + h.shape[1:])
    raw = nn.conv(params["policy"]["conv2"],
                  jnp.concatenate([z, s], axis=0))          # (dir, H, W)
    expected = jnp.transpose(raw, (1, 2, 0)).reshape(-1)
    actual = net._policy_logits(params["policy"], h, masks[0], scalars[0])
    np.testing.assert_allclose(np.asarray(actual), np.asarray(expected), rtol=1e-5)


@pytest.mark.parametrize("memory", ["none", "gru", "stack"])
def test_sequence_matches_manual_stepping(memory):
    net = make_net(memory)
    params = net.init(jax.random.PRNGKey(0))
    grids, scalars, masks, actions = make_inputs(net, t=4)

    logps, values, entropies = net.sequence_forward(
        params, grids, scalars, masks,
        jnp.zeros((4,), dtype=bool), actions=actions,
    )
    memory = net.initial_memory()
    for t in range(4):
        out = net.step(
            params, grids[t], scalars[t], masks[t], memory,
            sample=False, action=actions[t],
        )
        assert float(out.log_prob) == pytest.approx(float(logps[t]), abs=1e-5)
        assert float(out.value) == pytest.approx(float(values[t]), abs=1e-5)
        assert float(out.entropy) == pytest.approx(float(entropies[t]), abs=1e-5)
        memory = out.memory


@pytest.mark.parametrize("memory", ["gru", "stack"])
def test_sequence_resets_memory_on_done(memory):
    net = make_net(memory)
    params = net.init(jax.random.PRNGKey(0))
    grids, scalars, masks, actions = make_inputs(net, t=5)
    dones = jnp.array([False, True, False, False, False])

    logps, _, _ = net.sequence_forward(
        params, grids, scalars, masks, dones, actions=actions
    )
    # Step 2 starts a new episode: it must equal a fresh rollout from there.
    fresh, _, _ = net.sequence_forward(
        params, grids[2:], scalars[2:], masks[2:], dones[2:], actions=actions[2:]
    )
    assert float(logps[2]) == pytest.approx(float(fresh[0]), abs=1e-5)
    assert float(logps[3]) == pytest.approx(float(fresh[1]), abs=1e-5)


def test_reset_memory_zeroes():
    net = make_net("gru")
    memory = net.initial_memory()
    noisy = jax.tree_util.tree_map(
        lambda x: x + jnp.ones_like(x), memory
    )
    reset = reset_memory(noisy, True)
    for leaf in jax.tree_util.tree_leaves(reset):
        assert float(jnp.sum(jnp.abs(leaf))) == 0.0
    kept = reset_memory(noisy, False)
    for a, b in zip(jax.tree_util.tree_leaves(kept), jax.tree_util.tree_leaves(noisy)):
        np.testing.assert_allclose(np.asarray(a), np.asarray(b))


def test_value_and_policy_depend_on_memory():
    net = make_net("gru")
    params = net.init(jax.random.PRNGKey(0))
    grids, scalars, masks, actions = make_inputs(net, t=2)
    a = net.step(params, grids[0], scalars[0], masks[0], net.initial_memory(),
                 key=jax.random.PRNGKey(1))
    b = net.step(params, grids[0], scalars[0], masks[0], a.memory,
                 key=jax.random.PRNGKey(1))
    assert float(jnp.abs(a.value - b.value)) > 0


def test_gradients_flow():
    net = make_net("gru")
    params = net.init(jax.random.PRNGKey(0))
    grids, scalars, masks, _ = make_inputs(net, t=2)

    def loss(p):
        out = net.step(p, grids[0], scalars[0], masks[0], net.initial_memory(),
                       sample=False, action=jnp.asarray(0))
        return out.value + out.log_prob

    grads = jax.grad(loss)(params)
    total = sum(float(jnp.sum(jnp.square(g))) for g in jax.tree_util.tree_leaves(grads))
    assert total > 0


def test_remat_does_not_change_outputs():
    net = make_net("gru")
    params = net.init(jax.random.PRNGKey(0))
    grids, scalars, masks, actions = make_inputs(net, t=4)
    dones = jnp.zeros((4,), dtype=bool)

    with_remat = net.sequence_forward(
        params, grids, scalars, masks, dones, actions=actions, remat=True
    )
    without_remat = net.sequence_forward(
        params, grids, scalars, masks, dones, actions=actions, remat=False
    )
    for a, b in zip(with_remat, without_remat):
        np.testing.assert_allclose(np.asarray(a), np.asarray(b), rtol=1e-5)


def test_value_and_policy_respond_to_global_scalars():
    """The heads must see the scalars: LayerNorm would otherwise normalise
    away the broadcast constant planes in the backbone."""
    net = make_net("none")
    params = net.init(jax.random.PRNGKey(0))
    grids, _, masks, _ = make_inputs(net, t=1)
    base = jnp.array([0.1, 0.2, 0.1, 0.3, 0.2, 0.0, 0.0])

    low = net.step(params, grids[0], base.at[1].set(0.05), masks[0],
                   net.initial_memory(), sample=False)
    high = net.step(params, grids[0], base.at[1].set(0.9), masks[0],
                    net.initial_memory(), sample=False)
    assert abs(float(high.value) - float(low.value)) > 1e-4
    assert float(jnp.abs(high.logits - low.logits).max()) > 1e-4


def test_checkpoint_roundtrip(tmp_path):
    net = make_net("gru")
    params = net.init(jax.random.PRNGKey(0))
    path = tmp_path / "params.npz"
    save_params(path, params)
    loaded = load_params(path, params)
    for a, b in zip(jax.tree_util.tree_leaves(loaded), jax.tree_util.tree_leaves(params)):
        np.testing.assert_allclose(np.asarray(a), np.asarray(b))


def test_no_coords_matches_readme_input_channels():
    net = make_net("none")
    assert net.frame_channels == 17
    net = PolicyValueNet(
        NetConfig(channels=8, num_blocks=1, memory="none", use_coords=True),
        grid_channels=10, num_scalars=7, height=5, width=5,
    )
    assert net.frame_channels == 19
