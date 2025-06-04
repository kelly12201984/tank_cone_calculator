import streamlit as st
import math

# --- UI Config ---
st.set_page_config(page_title="Cone Material & Layout Estimator", layout="centered")
st.title("📐 Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")

# --- Inputs ---
diameter = st.number_input("Tank Diameter (in inches)", min_value=1)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

# --- Geometry Functions ---
def calculate_slant_height(diameter, angle_deg):
    radius = diameter / 2
    angle_rad = math.radians(angle_deg)
    return round(radius / math.sin(angle_rad), 2)

def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:
        return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

def calculate_courses_and_breaks(diameter, angle_deg, moc):

    total_slant = calculate_slant_height(diameter, angle_deg)
    angle_rad = math.radians(angle_deg)

    # Get valid plate widths based on material
    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]
    best_config = None

    for plate_w in plate_widths:
        num_courses = math.ceil(total_slant / plate_w)
        course_slant = total_slant / num_courses

        break_diameters = []
        for i in range(num_courses + 1):
            rem_slant = total_slant - (i * course_slant)
            break_radius = rem_slant * math.sin(angle_rad)
            break_diameters.append(round(break_radius * 2, 2))

        config = {
            "Total Slant Height": round(total_slant, 2),
            "Number of Courses": num_courses,
            "Course Slant Height": round(course_slant, 2),
            "Break Diameters (Top → Bottom)": break_diameters,
            "Used Plate Width": plate_w
        }

        # Choose the config with fewer courses (shorter vertical breaks = better)
        if best_config is None or config["Number of Courses"] < best_config["Number of Courses"]:
            best_config = config

    return best_config


def estimate_plate_usage_per_course(course_info, plate_width, plate_length, segments_per_course=4):
    break_diameters = course_info["Break Diameters (Top → Bottom)"]
    course_slant = course_info["Course Slant Height"]
    course_results = []

    for i in range(course_info["Number of Courses"]):
        d_top = break_diameters[i]
        d_bottom = break_diameters[i + 1]
        r_outer = d_top / 2
        r_inner = d_bottom / 2
        arc_angle = (2 * math.pi) / segments_per_course
        avg_radius = (r_outer + r_inner) / 2
        arc_width = arc_angle * avg_radius

        if course_slant > plate_width:
            course_results.append({
                "course": i + 1,
                "segments": segments_per_course,
                "fit": 0,
                "plates": "❌ Too tall for plate"
            })
            continue

        segments_fit = math.floor(plate_length / arc_width)
        if segments_fit == 0:
            course_results.append({
                "course": i + 1,
                "segments": segments_per_course,
                "fit": 0,
                "plates": "❌ Too wide for plate"
            })
            continue

        plates_needed = math.ceil(segments_per_course / segments_fit)
        waste = (plates_needed * plate_width * plate_length) - (segments_per_course * arc_width * course_slant)

        course_results.append({
            "course": i + 1,
            "segments": segments_per_course,
            "fit": segments_fit,
            "plates": plates_needed,
            "waste": round(waste, 2)
        })

    return course_results

def optimize_plate_usage(area_needed, plate_options, course_info):
    options = []
    for w, l in plate_options:
        plate_area = w * l
        course_layout = estimate_plate_usage_per_course(course_info, w, l)
        if any(isinstance(result["plates"], str) for result in course_layout):
            continue
        plates_needed = sum(result["plates"] for result in course_layout if isinstance(result["plates"], int))
        total_waste = (plates_needed * plate_area) - area_needed
        options.append((plates_needed, (w, l), total_waste))
    options.sort(key=lambda x: (x[0], x[2]))
    return options[0] if options else None

# --- Main App Logic ---
if st.button("Calculate Cone Layout"):
    slant_height = calculate_slant_height(diameter, angle)
    cone_area = math.pi * (diameter / 2) * slant_height
    course_info = calculate_courses_and_breaks(diameter, angle, moc)
    plate_options = get_plate_options(moc)
    best = optimize_plate_usage(cone_area, plate_options, course_info)

    if best:
        plates_needed, (plate_width, plate_length), waste = best
        course_layout = estimate_plate_usage_per_course(course_info, plate_width, plate_length)

        st.subheader("🌆 Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Size**: {plate_width}\" x {plate_length}\"")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")

        st.subheader("🔨 Estimated Plate Usage Per Course")
        for result in course_layout:
            if isinstance(result["plates"], str):
                st.write(f"**Course {result['course']}**: ❌ {result['plates']}")
            else:
                st.write(f"**Course {result['course']}**: {result['segments']} pieces ➔ fits {result['fit']} per plate ➔ **{result['plates']} plate(s)** — Estimated Waste: {result['waste']} in²")

        total_plates = sum(result["plates"] for result in course_layout if isinstance(result["plates"], int))
        st.markdown(f"**Summary ➔ Total Plates Needed: {total_plates} using {plate_width}\" x {plate_length}\" plates**")

        st.subheader("🏩 Cone Course Layout")
        st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
        st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
        st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
        st.write("**Break Diameters (top → bottom):**")
        st.write(course_info["Break Diameters (Top → Bottom)"])
    else:
        st.error("❌ No viable plate layout found. Try reducing number of segments or using a different material.")

