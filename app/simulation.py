import numpy as np
import pandas as pd

def simulate_projectile(
    v0,
    angle_deg,
    h0,
    g,
    drag_coeff=0.0,
    include_air_resistance=True,
    dt=0.01,
    restitution=0.6,
    ground_friction=0.05,
    max_bounces=20
):
    """
    Simulate projectile motion with optional air resistance and ground bounces.

    Returns:
        traj: np.ndarray of shape (N, 2) with columns [x, y]
        total_time: float
        telem: pd.DataFrame with columns [t, x, y, vx, vy, ax, ay]
               and attrs:
                 - first_impact_x (float or None)
                 - first_impact_t (float or None)
    """
    angle_rad = np.radians(angle_deg)

    # Initial state
    vx = v0 * np.cos(angle_rad)
    vy = v0 * np.sin(angle_rad)
    x = 0.0
    y = float(h0)
    t = 0.0

    # Compute initial acceleration for a well-formed first telemetry row
    if include_air_resistance:
        ax = -drag_coeff * np.sign(vx) * abs(vx)
        ay = -g - drag_coeff * np.sign(vy) * abs(vy)
    else:
        ax = 0.0
        ay = -g

    # Storage
    traj = [(x, y)]
    ts, xs, ys, vxs, vys, axs, ays = [t], [x], [y], [vx], [vy], [ax], [ay]

    MAX_TIME = 60.0
    bounces = 0
    first_impact_x = None
    first_impact_t = None

    while t <= MAX_TIME:
        # Save previous step
        x_prev, y_prev = x, y
        vx_prev, vy_prev = vx, vy
        ax_prev, ay_prev = ax, ay
        t_prev = t

        # Integrate one step (semi-implicit Euler)
        vx = vx_prev + ax_prev * dt
        vy = vy_prev + ay_prev * dt
        x = x_prev + vx * dt
        y = y_prev + vy * dt
        t = t_prev + dt

        # Provisional accelerations for next step
        if include_air_resistance:
            ax = -drag_coeff * np.sign(vx) * abs(vx)
            ay = -g - drag_coeff * np.sign(vy) * abs(vy)
        else:
            ax = 0.0
            ay = -g

        # Ground crossing?
        if y < 0.0 and vy < 0.0:
            # Linear backtrack to y=0
            denom = (y_prev - y)
            alpha = (y_prev / denom) if denom != 0 else 0.0
            x = x_prev + alpha * (x - x_prev)
            y = 0.0
            t = t_prev + alpha * dt

            # First impact capture (pre-bounce flight ends here)
            if first_impact_x is None:
                first_impact_x = x
                first_impact_t = t

            # Bounce response
            vy = -vy * restitution
            vx = vx * (1.0 - ground_friction)

            bounces += 1
            if bounces >= max_bounces:
                # record and stop
                ts.append(t); xs.append(x); ys.append(y)
                vxs.append(vx); vys.append(vy); axs.append(ax); ays.append(ay)
                traj.append((x, y))
                break

            # Tiny-motion stop
            if abs(vy) < 0.05 and abs(vx) < 0.05:
                ts.append(t); xs.append(x); ys.append(y)
                vxs.append(vx); vys.append(vy); axs.append(ax); ays.append(ay)
                traj.append((x, y))
                break

        # Record this step
        ts.append(t); xs.append(x); ys.append(y)
        vxs.append(vx); vys.append(vy); axs.append(ax); ays.append(ay)
        traj.append((x, y))

        # If we are at rest on ground, stop
        if y == 0.0 and abs(vy) < 0.05 and abs(vx) < 0.05:
            break

    traj_arr = np.array(traj)
    telem = pd.DataFrame({
        "t": ts, "x": xs, "y": ys, "vx": vxs, "vy": vys, "ax": axs, "ay": ays
    })
    telem.attrs["first_impact_x"] = first_impact_x
    telem.attrs["first_impact_t"] = first_impact_t

    return traj_arr, t, telem
