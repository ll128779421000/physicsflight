import streamlit as st
from app.constants import PLANET_GRAVITIES, DRAG_COEFFICIENTS
from app.simulation import simulate_projectile
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

st.set_page_config(page_title='PhysicsFlight', layout='wide')
st.title("PhysicsFlight: Explore Projectile Motion")

st.sidebar.header('Simulation Controls')
v0 = st.sidebar.slider('Initial Velocity (m/s)', 0,200,50)
angle = st.sidebar.slider('Launch Angle (degrees)', 0,90,45)
h0 = st.sidebar.slider('Initial Height (m)', 0,100,0)
restitution = st.sidebar.slider("Bounce (restitution)", 0.0, 1.0,0.6,0.05)
ground_friction = st.sidebar.slider("Ground Friction (horizontal loss per bounce",0.0,0.5,0.05,0.01)
planet = st.sidebar.selectbox('Planet', list(PLANET_GRAVITIES.keys()))
medium = st.sidebar.selectbox('Medium', list(DRAG_COEFFICIENTS.keys()))
drag = DRAG_COEFFICIENTS[medium]
st.sidebar.markdown(f"**Drag Coefficient:** {drag}")
air_res = st.sidebar.checkbox('Include medium resistance?',True)

if st.sidebar.button('Run Simulation'):
    g = PLANET_GRAVITIES[planet]
    drag = DRAG_COEFFICIENTS[medium]
    
    data_with, time_with = simulate_projectile(
        v0=v0,
        angle_deg=angle,
        h0=h0,
        g=PLANET_GRAVITIES[planet],
        drag_coeff=DRAG_COEFFICIENTS[medium],
        include_air_resistance=air_res, 
        restitution=restitution, 
        ground_friction=ground_friction)
    data_without, time_without = simulate_projectile(
        v0=v0,
        angle_deg=angle,
        h0=h0,
        g=PLANET_GRAVITIES[planet],
        drag_coeff=0.0,
        include_air_resistance=False, 
        restitution=restitution, 
        ground_friction=ground_friction)

    df_with = pd.DataFrame(data_with, columns=['x','y'])
    df_without = pd.DataFrame(data_without, columns=['x','y'])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_with['x'], y=df_with['y'],
                    mode='lines', name='With Medium Resistance',
                    line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df_without['x'], y=df_without['y'],
                    mode='lines', name='No Medium Resistance',
                    line=dict(color='red', dash='dash')))
    
    fig.update_layout(title='Projectile Trajectory Motion',
                      xaxis_title='Distance (m)',
                      yaxis_title='Height (m)',
                      height = 500,
                      template='plotly_white')
    
    st.plotly_chart(fig,use_container_width=True)

else:
    st.info('Use the sidebar to input parameters and run simulation')