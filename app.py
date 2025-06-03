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

    # Placeholder logic for now
    if moc == "Stainless Steel":
        plate_options = ["48/60 x 96", "48/60 x 120", "48/60 x 144", "48/60 x 180-480"]
    else:
        plate_options = ["96/120 x 240", "96/120 x 360", "96/120 x 480"]

    # Just return something rough and static for now
    st.write("✅ Suggested Plate Size:", plate_options[1])
    st.write("📏 Estimated Number of Courses:", 2)
    st.write("🧩 Pieces per Course:", "4 / 2")
    st.write("🔄 Break Diameter:", f"{tank_diameter / 2:.1f}\" (placeholder)")

    st.info("These results are just placeholders. Calculation logic is coming soon!")
