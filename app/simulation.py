import numpy as np

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
    
    angle_rad = np.radians(angle_deg)

    # Initial Velocities
    vx = v0 * np.cos(angle_rad)
    vy = v0 * np.sin(angle_rad)

    # Initial position
    x = 0
    y = float(h0)
    t=0

    # Store the trajecotry
    trajectory = [(x,y)]

    MAX_TIME = 30 #seconds

    bounces = 0

    # Run simulation until projectile hits the ground
    while t <= MAX_TIME:
        if include_air_resistance:
            ax = -drag_coeff * np.sign(vx) * abs(vx)
            ay = -g - drag_coeff * np.sign(vy) * abs(vy)
        else:
            ax = 0.0
            ay = -g

        x_prev, y_prev = x,y
        vx_prev, vy_prev = vx, vy

        #update velocities
        vx += ax * dt
        vy += ay * dt

        # update positions
        x += vx * dt
        y += vy * dt
        t += dt

        # answering did we cross the ground
        if y < 0.0 and vy < 0.0:
            denom = (y_prev - y)
            alpha = (y_prev / denom) if denom != 0 else 0.0
            x = x_prev + alpha * (x - x_prev)
            y = 0.0
            t = t -dt + alpha * dt

            vy = -vy * restitution
            vx = vx * (1.0 - ground_friction)

            bounces += 1
            if bounces >= max_bounces:
                trajectory.append((x,y))
                break

            if abs(vy) < 0.05 and abs(vx) < 0.05:
                trajectory.append((x,y))

        trajectory.append((x,y))

        if y == 0.0 and abs(vy) < 0.05 and abs(vx) < 0.05:
            break
    
    return np.array(trajectory), t
