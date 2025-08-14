# Gravitational pull (in m/s^2) for each planet

PLANET_GRAVITIES = {
    "Earth": 9.81,
    "Moon": 1.62,
    "Mars": 3.73,
    "Jupiter": 24.79,
    "Gravity-Less": 0,
}

# Drag coefficients depending on what the projectile is moving through
DRAG_COEFFICIENTS = {
    "Vacuum": 0.0, 
    "Air": 0.4,
    "Water": 0.2,
}