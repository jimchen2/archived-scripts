"""Minimal, dependency-free neural-network layers in pure JAX.

The parameter tree is a plain nested dict of arrays (no framework bookkeeping),
which makes checkpointing trivial and keeps the code easy to read and modify.
All layers work on a *single* sample with a channel-first layout ``(C, H, W)``;
batching is done with ``jax.vmap`` in :mod:`bot.network`.

Conventions
-----------
* ``*_init`` functions take a PRNG key and return a dict of parameters.
* ``*_apply`` functions (named after the layer) take ``(params, x)`` and return
  the transformed array.
* Initialisation follows He/Xavier-style fan-in scaling, so the activations
  stay well behaved through the deep residual backbone.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp

# ---------------------------------------------------------------------------
# initialisers
# ---------------------------------------------------------------------------


silu = jax.nn.silu


def _he_normal(key: jax.Array, shape: tuple[int, ...], scale: float = 2.0):
    """Truncated-normal init with fan-in variance scaling (He for ReLU/SiLU)."""
    return jax.nn.initializers.variance_scaling(
        scale, "fan_in", "truncated_normal"
    )(key, shape)


def dense_init(
    key: jax.Array, in_features: int, out_features: int, scale: float = 2.0
) -> dict:
    """A ``Dense`` layer: ``(in_features,) -> (out_features,)``."""
    return {
        "w": _he_normal(key, (in_features, out_features), scale),
        "b": jnp.zeros((out_features,), dtype=jnp.float32),
    }


def dense(p: dict, x: jax.Array) -> jax.Array:
    return x @ p["w"] + p["b"]


def conv_init(
    key: jax.Array,
    in_channels: int,
    out_channels: int,
    kernel: int = 3,
    scale: float = 2.0,
) -> dict:
    """A ``kernel x kernel`` convolution with ``SAME`` padding.

    Weight layout is ``OIHW`` (out, in, kh, kw), which is what
    ``jax.lax.conv_general_dilated`` expects.
    """
    return {
        "w": _he_normal(key, (out_channels, in_channels, kernel, kernel), scale),
        "b": jnp.zeros((out_channels,), dtype=jnp.float32),
    }


def conv(p: dict, x: jax.Array, padding: str = "SAME") -> jax.Array:
    """Apply a convolution to ``(C, H, W)`` and return ``(O, H, W)``."""
    y = jax.lax.conv_general_dilated(
        x[None],                      # add batch axis: (1, C, H, W)
        p["w"],
        window_strides=(1, 1),
        padding=padding,
        dimension_numbers=("NCHW", "OIHW", "NCHW"),
    )
    return y[0] + p["b"][..., None, None]


# ---------------------------------------------------------------------------
# normalisation
# ---------------------------------------------------------------------------


def layer_norm_init(channels: int) -> dict:
    return {
        "scale": jnp.ones((channels,), dtype=jnp.float32),
        "bias": jnp.zeros((channels,), dtype=jnp.float32),
    }


def layer_norm(p: dict, x: jax.Array, eps: float = 1e-5) -> jax.Array:
    """LayerNorm over ``(C, H, W)`` with per-channel affine parameters.

    Normalising every element of the feature map (rather than per channel, as
    BatchNorm would) keeps the statistics independent of the batch dimension,
    which is what makes it safe inside ``jax.lax.scan`` and under PPO's
    changing batch statistics.  Per-channel scale/bias is the usual choice for
    convolutional features and keeps the layer translation-equivariant.
    """
    mean = jnp.mean(x, axis=(0, 1, 2), keepdims=True)
    var = jnp.var(x, axis=(0, 1, 2), keepdims=True)
    y = (x - mean) * jax.lax.rsqrt(var + eps)
    return y * p["scale"][..., None, None] + p["bias"][..., None, None]


# ---------------------------------------------------------------------------
# squeeze-and-excitation and global context
# ---------------------------------------------------------------------------


def se_init(key: jax.Array, channels: int, ratio: int = 4) -> dict:
    """Squeeze-and-Excitation: channel-wise gating from a global descriptor."""
    hidden = max(channels // ratio, 4)
    k1, k2 = jax.random.split(key)
    return {
        "w1": dense_init(k1, channels, hidden),
        "w2": dense_init(k2, hidden, channels, scale=1.0),
    }


def se_apply(p: dict, x: jax.Array) -> jax.Array:
    """Scale each channel by a sigmoid gate computed from global average pool."""
    s = jnp.mean(x, axis=(1, 2))                  # (C,)
    s = jax.nn.silu(dense(p["w1"], s))
    s = jax.nn.sigmoid(dense(p["w2"], s))
    return x * s[:, None, None]


def context_init(key: jax.Array, channels: int, hidden: int | None = None) -> dict:
    """Global-context block parameters.

    The block pools the map to a vector, passes it through a small MLP, then
    *concatenates* the broadcast vector back onto the feature map and projects
    back to ``channels`` with a 1x1 convolution.  This gives every local 3x3
    filter access to board-level information (army totals, where the fighting
    is happening) without destroying the spatial layout.
    """
    hidden = hidden or channels // 2
    k1, k2, k3 = jax.random.split(key, 3)
    return {
        "w1": dense_init(k1, channels, hidden),
        "w2": dense_init(k2, hidden, channels, scale=1.0),
        "proj": conv_init(k3, channels * 2, channels, kernel=1, scale=1.0),
    }


def context_apply(p: dict, x: jax.Array) -> jax.Array:
    g = jnp.mean(x, axis=(1, 2))                  # (C,)
    g = jax.nn.silu(dense(p["w1"], g))
    g = dense(p["w2"], g)
    g = jnp.broadcast_to(g[:, None, None], x.shape)
    return conv(p["proj"], jnp.concatenate([x, g], axis=0))


# ---------------------------------------------------------------------------
# ConvGRU
# ---------------------------------------------------------------------------


def conv_gru_init(key: jax.Array, in_channels: int, channels: int) -> dict:
    """ConvGRU cell parameters (3x3 convolutions, ``channels`` hidden maps)."""
    k_xz, k_hz, k_xh, k_hh = jax.random.split(key, 4)
    return {
        # gates: [update | reset]
        "xz": conv_init(k_xz, in_channels, 2 * channels),
        "hz": conv_init(k_hz, channels, 2 * channels),
        # candidate hidden state
        "xh": conv_init(k_xh, in_channels, channels),
        "hh": conv_init(k_hh, channels, channels),
    }


def conv_gru_apply(p: dict, x: jax.Array, h: jax.Array | None) -> jax.Array:
    """One ConvGRU step.

    Parameters
    ----------
    x: ``(C_in, H, W)`` input features.
    h: ``(C, H, W)`` previous hidden state, or ``None`` for zeros.
    """
    if h is None:
        h = jnp.zeros((p["hh"]["w"].shape[1],) + x.shape[1:], dtype=x.dtype)
    gates = jax.nn.sigmoid(conv(p["xz"], x) + conv(p["hz"], h))
    z, r = jnp.split(gates, 2, axis=0)
    candidate = jnp.tanh(conv(p["xh"], x) + conv(p["hh"], r * h))
    return (1.0 - z) * h + z * candidate


def layer_norm_vec_init(features: int) -> dict:
    """LayerNorm for a 1-D feature vector (used by the value head)."""
    return {
        "scale": jnp.ones((features,), dtype=jnp.float32),
        "bias": jnp.zeros((features,), dtype=jnp.float32),
    }


def layer_norm_vec(p: dict, x: jax.Array, eps: float = 1e-5) -> jax.Array:
    mean = jnp.mean(x)
    var = jnp.var(x)
    return (x - mean) * jax.lax.rsqrt(var + eps) * p["scale"] + p["bias"]
