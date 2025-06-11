# Concentric Cone Estimator v2.1 – Stable Optimal, Manual Override, Accurate Visuals
import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd
import io

# --- UI + Inputs
st.set_page_config(page_title="Concentric Cone Estimator", layout="centered")
st.title("Concentric Cone Material & Layout Estimator")
st.markdown("Enter specs to estimate layout & material usage for a concentric cone.")
st.markdown("Small (bottom) diameter is fixed at 2 inches.")

opportunity_id = st.text_input("Opportunity ID (optional, used in export file name)")
diameter = st.number_input("Tank Diameter (in inches)", min_value=1, value=168)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1, value=60)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

BOTTOM_DIAMETER = 2

# --- Core Logic
def calculate_slant_height(diameter, angle_deg, bottom_diameter=BOTTOM_DIAMETER):
    r_large = diameter / 2
    r_small = bottom_diameter / 2
    angle_rad = math.radians(angle_deg)
    slant = (r_large - r_small) / math.sin(angle_rad)
    return round(slant, 2)

def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

def calculate_courses_and_breaks(diameter, angle_deg, moc):
    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]
    total_slant = calculate_slant_height(diameter, angle_deg)
    angle_rad = math.radians(angle_deg)
    bottom_radius = BOTTOM_DIAMETER / 2

    max_width = max(plate_widths)
    num_courses = 2
    while total_slant / num_courses > max_width:
        num_courses += 1

    course_slant = total_slant / num_courses
    used_width = next((w for w in sorted(plate_widths) if w >= course_slant), max_width)
    break_diameters = [round((bottom_radius + (total_slant - i * course_sl_*]()_
