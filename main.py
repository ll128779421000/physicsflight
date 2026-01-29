import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os

from app.constants import PLANET_GRAVITIES, DRAG_COEFFICIENTS
from app.simulation import simulate_projectile

if "loaded_values" not in st.session_state:
    st.session_state.loaded_values = None
if "loaded_scenario_name" not in st.session_state:
    st.session_state.loaded_scenario_name = None

if "_pending_apply" in st.session_state and st.session_state._pending_apply is not None:
    for k, v in st.session_state._pending_apply.items():
        st.session_state[k] = v
    st.session_state._pending_apply = None

if "sim_has_run" not in st.session_state:
    st.session_state.sim_has_run = False

st.set_page_config(page_title="PhysicsFlight", layout="wide")
st.title("🚀 PhysicsFlight: Explore Projectile Motion")

# --- Sidebar controls ---
st.sidebar.header("Simulation Controls")
v0 = st.sidebar.slider("Initial velocity (m/s)", 0, 200, 50, key="v0")
angle = st.sidebar.slider("Launch angle (°)", 0, 90, 45, key="angle")
h0 = st.sidebar.slider("Initial height (m)", 0, 100, 0, key="h0")

planet = st.sidebar.selectbox("Planet", list(PLANET_GRAVITIES.keys()), key="planet")
medium = st.sidebar.selectbox("Medium", list(DRAG_COEFFICIENTS.keys()), key="medium")
air_res = st.sidebar.checkbox("Include medium resistance?", True, key="air_res")

# Bounce controls
restitution = st.sidebar.slider("Bounce (restitution)", 0.0, 1.0, 0.6, 0.05, key="restitution")
ground_friction = st.sidebar.slider("Ground friction (horizontal loss per bounce)", 0.0, 0.5, 0.05, 0.01, key="ground_friction")

# Scenarios
st.sidebar.markdown("---")
st.sidebar.subheader("Scenarios")

scenario_name = st.sidebar.text_input("Scenario name")
col_s1, col_s2 = st.sidebar.columns(2)
save_clicked = col_s1.button("Save")
load_clicked = col_s2.button("Load")

SCENARIO_FILE = "scenarios.json"

def load_scenarios():
    if not os.path.exists(SCENARIO_FILE):
        return {}
    try:
        with open(SCENARIO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}
    
def save_scenarios(data):
    with open(SCENARIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

scenarios = load_scenarios()

if save_clicked and scenario_name.strip():
    scenarios[scenario_name.strip()] = {
        "v0": v0, "angle": angle, "h0": h0,
        "planet": planet, "medium": medium, "air_res": air_res,
        "restitution": restitution, "ground_friction": ground_friction
    }
    save_scenarios(scenarios)
    st.sidebar.success(f"Saved '{scenario_name.strip()}'")

if scenarios:
    st.sidebar.caption("Saved: " + ", ".join(list(scenarios.keys())[:6]) + ("..." if len(scenarios) > 6 else ""))


loaded_values = None
if load_clicked and scenario_name.strip():
    key = scenario_name.strip()
    if key in scenarios:
        st.session_state.loaded_values = scenarios[key]
        st.session_state.loaded_scenario_name = key
        st.sidebar.success(f"Loaded '{key}'. Click 'Apply loaded' to push values through")
    else:
        st.sidebar.error(f"No scenario named '{key}' found")

if st.session_state.loaded_values is not None:
    if st.sidebar.button("Apply loaded"):
        # stash values to apply on next run, then rerun immediately
        st.session_state._pending_apply = dict(st.session_state.loaded_values)
        st.sidebar.success("Applied. Review values and click 'Run Simulation'")
        st.rerun()

#run = st.sidebar.button("Run Simulation")
if st.sidebar.button("Run Simulation"):
    st.session_state.sim_has_run = True

# --- Resolve constants & vacuum handling ---
g = PLANET_GRAVITIES[planet]
drag = DRAG_COEFFICIENTS[medium]
st.sidebar.markdown(f"**Gravity (g):** `{g} m/s²`")
st.sidebar.markdown(f"**Drag coefficient:** `{drag}`") 

if medium == "Vacuum":
    st.sidebar.caption("Air resistance disabled in Vacuum (drag = 0).")
    air_res_effective = False
else:
    air_res_effective = air_res

# --- Run block ---
if st.session_state.sim_has_run:
    # simulate
    data_with, time_with, tele_with = simulate_projectile(
        v0=v0, angle_deg=angle, h0=h0, g=g,
        drag_coeff=drag, include_air_resistance=air_res_effective,
        restitution=restitution, ground_friction=ground_friction
    )
    data_without, time_without, tele_without = simulate_projectile(
        v0=v0, angle_deg=angle, h0=h0, g=g,
        drag_coeff=0.0, include_air_resistance=False,
        restitution=restitution, ground_friction=ground_friction
    )

    # prep
    df_with = pd.DataFrame(data_with, columns=["x", "y"])
    df_without = pd.DataFrame(data_without, columns=["x", "y"])

    if not df_with.empty:
        apex_idx = df_with["y"].idxmax()
        apex_x = df_with.at[apex_idx, "x"]
        apex_y = df_with.at[apex_idx, "y"]
    else:
        apex_x = apex_y = 0.0

    impact_x = df_with["x"].iloc[-1] if not df_with.empty else 0.0
    impact_y = df_with["y"].iloc[-1] if not df_with.empty else 0.0

    first_x = tele_with.attrs.get("first_impact_x", None)
    first_t = tele_with.attrs.get("first_impact_t", None)

    # plot trajectories
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_with["x"], y=df_with["y"],
        mode="lines", name="With Resistance", line=dict(width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df_without["x"], y=df_without["y"],
        mode="lines", name="No Resistance", line=dict(width=3, dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=[apex_x], y=[apex_y],
        mode="markers+text", marker=dict(size=10),
        text=["Apex"], textposition="top center", name="Apex"
    ))
    fig.add_trace(go.Scatter(
        x=[impact_x], y=[impact_y],
        mode="markers+text", marker=dict(size=10),
        text=["Impact"], textposition="bottom right", name="Impact"
    ))

    if first_x is not None:
        fig.add_trace(go.Scatter(
            x=[first_x], y=[0.0],
            mode="markers+text",
            marker=dict(size=10),
            text=['First Impact'],
            textposition="bottom center",
            name="First Impact"
        ))
    fig.update_layout(
        title="Projectile Trajectory (with bounces)",
        xaxis_title="Distance (m)",
        yaxis_title="Height (m)",
        hovermode="x unified",
        height=520
    )
    st.subheader("🔎 Trajectory Comparison")
    st.plotly_chart(fig, use_container_width=True)

    # Teaching Animation
    st.markdown("### Animate Projectile (with resistance)")

    max_frame = len(df_with) - 1
    frame = st.slider("Frame", 0, max_frame, 0)

    fig_anim = go.Figure()

    # full path (faint)
    fig_anim.add_trace(go.Scatter(
        x=df_with["x"],
        y=df_with["y"],
        mode="lines",
        line=dict(width=2),
        name="Path"
    ))

    # Current projectile position
    fig_anim.add_trace(go.Scatter(
        x=[df_with["x"].iloc[frame]],
        y=[df_with["y"].iloc[frame]],
        mode="markers",
        marker=dict(size=12),
        name="Projectile"
    ))
    fig_anim.update_layout(
        xaxis_title="Distance (m)",
        yaxis_title="Height (m)",
        height=400
    )

    st.plotly_chart(fig_anim, use_container_width=True)

    # Speed over time
    st.markdown("### 📈 Speed over Time")
    speed_with = (tele_with["vx"]**2 + tele_with["vy"]**2)**0.5
    speed_without = (tele_without["vx"]**2 + tele_without["vy"]**2)**0.5
    fig_speed = go.Figure()
    fig_speed.add_trace(go.Scatter(x=tele_with["t"], y=speed_with, mode="lines",name="speed (with resistance)"))
    fig_speed.add_trace(go.Scatter(x=tele_without["t"], y=speed_without, mode="lines",name="speed (no resistance)", line=dict(dash="dash")))
    fig_speed.update_layout(xaxis_title="Time (s)", yaxis_title="Speed (m/s)", height=360)
    st.plotly_chart(fig_speed, use_container_width=True)

    # velocity-time chart
    st.markdown("### 📈 Vertical Velocity over Time")
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(
        x=tele_with["t"], y=tele_with["vy"],
        mode="lines", name="vy (with resistance)"
    ))
    fig_v.add_trace(go.Scatter(
        x=tele_without["t"], y=tele_without["vy"],
        mode="lines", name="vy (no resistance)", line=dict(dash="dash")
    ))
    fig_v.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Vertical Velocity vy (m/s)",
        height=420
    )
    st.plotly_chart(fig_v, use_container_width=True)

    # Horizontal velocity-time chart
    st.markdown("### 📈 Horizontal Velocity over Time")
    fig_vx = go.Figure()
    fig_vx.add_trace(go.Scatter(x=tele_with["t"],y=tele_with['vx'], 
                                mode="lines", name="vx (with resistance)"))
    fig_vx.add_trace(go.Scatter(x=tele_without["t"],y=tele_without['vx'], 
                                mode="lines", name="vx (no resistance)", line=dict(dash="dash")))
    fig_vx.update_layout(xaxis_title="Time (s)", yaxis_title="Horizonal Velocity vx (m/s)",height=360)
    st.plotly_chart(fig_vx,use_container_width=True)

    # Acceleration-time chart
    st.markdown('### 📈 Vertical Acceleration over Time')
    fig_a = go.Figure()
    fig_a.add_trace(go.Scatter(x=tele_with["t"], y=tele_with["ay"], mode="lines", name="ay (with resistance)"))
    fig_a.add_trace(go.Scatter(x=tele_without["t"], y=tele_without["ay"], mode="lines", name="ay (no resistance)", line=dict(dash="dash")))
    fig_a.update_layout(xaxis_title="Time (s)", yaxis_title="Vertical Acceleration ay (m/s2)", height=360)
    st.plotly_chart(fig_a, use_container_width=True)

    # stats
    st.markdown("### 🧠 Trajectory Stats")
    lines = [
        f"- **Max Height (with resistance):** `{apex_y:.2f} m`",
        f"- **Final Range (after bounces):** `{impact_x:.2f} m`",
        f"- **Total Sim Time:** `{time_with:.2f} s`",
    ]
    if first_x is not None and first_t is not None:
        lines.insert(1, f"- **First Impact Range/Time (pre-bounce):** `{first_x:.2f} m`, `{first_t:.2f} s`")
    st.markdown("\n".join(lines))

    # explainer
    with st.expander("What's happening in this scenario?"):
        st.markdown(f"""
                    - The projectile is launched at **{v0} m/s** and **{angle}** degrees from a height of **{h0} m**.
                    - On **{planet}**, gravity is **{g:.2f} m/s2**, which affects how quickly it falls.
                    - The medium is **{medium}**, so drag is **{drag}** and:
                        - In Vacuum, there is *no* air resistance
                        - In Air/Water, drag slows both the horizontal and the vertical motion.
                    - Bounces use:
                        - **Restitution = {restitution}** --> how bouncy the surface is.
                        - **Ground friction = {ground_friction}** --> how quickly it loses horizontal speed
                    """)

    # Download telemetry data (with & without resistance)
    csv_with = tele_with.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Telemetry (with resistance) CSV",
        data=csv_with,
        file_name="telemetry_with_resistance.csv",
        mime="text/csv"
    )
    csv_without = tele_without.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Telemetry (no resistance) CSV",
        data=csv_without,
        file_name="telemetry_no_resistance.csv",
        mime="text/csv"
    )

else:
    st.info("Use the sidebar to set parameters and click **Run Simulation**.")
