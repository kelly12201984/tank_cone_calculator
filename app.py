import openai
import streamlit as st

openai.api_key = st.secrets["openai"]["api_key"]


st.set_page_config(page_title="Cone Material Calculator", layout="centered")
st.title("📐 Cone Material & Layout Estimator")

st.markdown("Enter the specs for the eccentric cone, and get an estimate of the optimal plate layout.")

# --- Inputs ---
tank_diameter = st.number_input("Tank Diameter (in inches)", min_value=1)
angle_of_repose = st.number_input("Angle of Repose (in degrees)", min_value=1, max_value=89)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

# --- Button ---
if st.button("🔘 Calculate Cone Layout"):
    st.markdown("---")
    st.subheader("🧾 Recommended Layout")

def calculate_cone_layout(diameter, angle, moc):
    import math

    radius = diameter / 2
    height = radius / math.tan(math.radians(angle))
    slant_height = math.sqrt(radius**2 + height**2)
    surface_area = math.pi * radius * slant_height

    if moc == "Stainless Steel":
        plate_options = [(48, l) for l in [96, 120, 144, 180, 240, 360, 480]]
    else:  # Carbon Steel
        plate_options = [(96, l) for l in [240, 360, 480]]

    best_fit = None
    fewest_plates = float('inf')

    for width, length in plate_options:
        area = (width * length) / 144  # in² → ft²
        num_plates = surface_area / area
        if num_plates < fewest_plates:
            fewest_plates = num_plates
            best_fit = (width, length)

    return {
        "Tank Diameter (in)": diameter,
        "Angle of Repose (deg)": angle,
        "Material": moc,
        "Estimated Slant Height (in)": round(slant_height, 2),
        "Cone Surface Area (ft²)": round(surface_area, 2),
        "Recommended Plate Size (in)": f"{best_fit[0]} x {best_fit[1]}",
        "Estimated # of Plates Needed": math.ceil(fewest_plates)
   
  if st.button("Calculate Cone Layout"):
    result = calculate_cone_layout(diameter, angle, moc)
    st.subheader("📐 Recommended Layout")
    for key, val in result.items():
        st.write(f"**{key}:** {val}")
        
