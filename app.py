import streamlit as st
import math

st.set_page_config(page_title="Cone Material & Layout Estimator", layout="centered")

st.title("📐 Cone Material & Layout Estimator")
st.markdown("Enter the specs for the eccentric cone, and get an estimate of the optimal plate layout.")

# Inputs
diameter = st.number_input("Tank Diameter (in inches)", min_value=1)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

def calculate_cone_area(diameter, angle_deg):
    radius = diameter / 2
    angle_rad = math.radians(angle_deg)
    height = radius * math.tan(angle_rad)
    slant_height = math.sqrt(radius**2 + height**2)
    return math.pi * radius * slant_height

def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:  # Carbon Steel
        return [(w, l) for w in [48, 60] for l in [96, 120, 144, 240, 360, 480]]

def optimize_plate_usage(area_needed, plate_options):
    options = []
    for w, l in plate_options:
        plate_area = w * l
        plates_needed = math.ceil(area_needed / plate_area)
        total_waste = (plates_needed * plate_area) - area_needed
        options.append((plates_needed, (w, l), total_waste))
    options.sort(key=lambda x: (x[0], x[2]))  # Prioritize fewer plates and minimal waste
    return options[0] if options else None

if st.button("Calculate Cone Layout"):
    cone_area = calculate_cone_area(diameter, angle)
    plate_options = get_plate_options(moc)
    best = optimize_plate_usage(cone_area, plate_options)

    if best:
        plates_needed, (width, length), waste = best
        st.subheader("📊 Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Size**: {width}\" x {length}\"")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")
    else:
        st.error("No viable plate layout found.")
