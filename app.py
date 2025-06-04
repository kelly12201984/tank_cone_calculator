import streamlit as st
import math

st.set_page_config(page_title="Cone Material & Layout Estimator", layout="centered")

st.title("📐 Cone Material & Layout Estimator")
st.markdown("Enter the specs for the eccentric cone, and get an estimate of the optimal plate layout.")

# Inputs
diameter = st.number_input("Tank Diameter (in inches)", min_value=1)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

def calculate_slant_height(diameter, angle_deg):
    radius = diameter / 2
    angle_rad = math.radians(angle_deg)
    slant = radius / math.tan(angle_rad)
    return round(slant, 2)

def calculate_cone_area(diameter, angle_deg):
    radius = diameter / 2
    slant_height = calculate_slant_height(diameter, angle_deg)
    return math.pi * radius * slant_height


def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:  # Carbon Steel
        return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

def optimize_plate_usage(area_needed, plate_options):
    options = []
    for w, l in plate_options:
        plate_area = w * l
        plates_needed = math.ceil(area_needed / plate_area)
        total_waste = (plates_needed * plate_area) - area_needed
        options.append((plates_needed, (w, l), total_waste))
    options.sort(key=lambda x: (x[0], x[2]))  # Prioritize fewer plates and minimal waste
    return options[0] if options else None
def calculate_courses_and_breaks(diameter, angle_deg, moc):
    if moc == "Stainless Steel":
        plate_widths = [48, 60]
    else:
        plate_widths = [48, 60, 96]

    max_course_slant = max(plate_widths)
    radius = diameter / 2
    angle_rad = math.radians(angle_deg)
    total_slant = radius / math.tan(angle_rad)

    num_courses = math.ceil(total_slant / max_course_slant)
    course_slant = total_slant / num_courses  # make courses even

    break_diameters = []
    for i in range(num_courses + 1):
        rem_slant = total_slant - (i * course_slant)
        break_radius = rem_slant * math.tan(angle_rad)
        break_diameters.append(round(break_radius * 2, 2))

    return {
        "Total Slant Height": round(total_slant, 2),
        "Number of Courses": num_courses,
        "Course Slant Height": round(course_slant, 2),
        "Break Diameters (Top → Bottom)": break_diameters
    }

if st.button("Calculate Cone Layout"):
    slant_height = calculate_slant_height(diameter, angle)
    cone_area = math.pi * (diameter / 2) * slant_height
    plate_options = get_plate_options(moc)
    best = optimize_plate_usage(cone_area, plate_options)

    course_info = calculate_courses_and_breaks(diameter, angle, moc)


    st.subheader("🧱 Cone Course Layout")
    st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
    st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
    st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
    st.write("**Break Diameters (top → bottom)**:")
    st.write(course_info["Break Diameters (Top → Bottom)"])
    if best:
        plates_needed, (width, length), waste = best
        st.subheader("📊 Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Size**: {width}\" x {length}\"")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")
    else:
        st.error("No viable plate layout found.")
