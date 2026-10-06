#!/usr/bin/env python3
"""Play exactly ONE ZombsRoyale solo round through the Gymnasium env, recorded.

The env's reset() walks the explicit phase machine:
    menu -> lobby (SOLO clicked) -> plane (mason "ingame" / busy ticks)
    -> SPACE jump -> airborne (held-W input suppressed by falling)
    -> landed (tap answered AND held-W produces a continuous movement stream)
and the Gymnasium episode starts ON THE GROUND (phase=alive).
The episode ends shortly after ELIMINATION — detected via the client sending
42["setIsInRound", false], mason "waiting", match-socket close, or a send
silence + unanswered tap-probe fallback.
"""
import time

import numpy as np

from zombs_env import ZombsRoyaleEnv, W_A, A_A, S_A, D_A, E_A, R_A, FIRE_A

MOVE_ACTIONS = [W_A, W_A, W_A, A_A, D_A, S_A]  # bias forward (find action, dodge gas)
FIRE_PERIOD = 8
RELOAD_PERIOD = 22


def policy(t_since_jump, rng):
    if t_since_jump < 4:
        return W_A  # land moving
    if t_since_jump % RELOAD_PERIOD < 1.0:
        return R_A
    if t_since_jump % FIRE_PERIOD < 1.0:
        return FIRE_A
    if t_since_jump % 3 < 1.0:
        return E_A  # doors/chests while roaming
    return int(rng.choice(MOVE_ACTIONS))


def main():
    rng = np.random.default_rng(7)
    env = ZombsRoyaleEnv(record=True, max_steps=250, step_seconds=0.9)
    try:
        obs, info = env.reset(seed=7)
        print("obs0:", np.round(obs, 1).tolist(), flush=True)
        print("reset info:", info, flush=True)

        total = 0.0
        t0 = time.time()
        while True:
            a = policy(time.time() - t0, rng)
            obs, r, terminated, truncated, info = env.step(a)
            total += r
            if (env._step % 25) == 0 or terminated or truncated:
                print(f"step {env._step:3d}  t+{time.time()-t0:5.1f}s  a={info['last_action']:>10s}  "
                      f"r={r:+.2f}  ret={total:+.1f}  {info['phase']:>6s}  "
                      f"ticks={info['tick_rate']:5.1f}/s  size={info['tick_avg_size']:5.1f}B  "
                      f"sends={info['send_rate12']:5.2f}/s", flush=True)
            if terminated or truncated:
                print(f"EPISODE OVER: terminated={terminated} truncated={truncated} "
                      f"return={total:.1f} ground_time={info['ground_time']}s "
                      f"elim_reason={info['elim_reason']}", flush=True)
                print(f"phase history: {' -> '.join(info['phase_history'])}", flush=True)
                break
    finally:
        env.close()
    print("done", flush=True)


if __name__ == "__main__":
    main()
