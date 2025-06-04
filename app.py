import streamlit as st
import math

st.set_page_config(page_title="Cone Material & Layout Estimator", layout="centered")

st.title("\U0001F4C8 Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")

# Inputs
diameter = st.number_input("Tank Diameter (in inches)", min_value=1)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

# Constants
SEGMENTS_PER_COURSE = 4

# Slant height calculator
def calculate_slant_height(diameter, angle_deg):
    radius = diameter / 2
    angle_rad = math.radians(angle_deg)
    slant = radius / math.sin(angle_rad)
    return round(slant, 2)

# Plate options by MOC
def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:
        return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

# Break diameters by course

def calculate_courses_and_breaks(diameter, angle_deg, moc):
    total_slant = calculate_slant_height(diameter, angle_deg)
    angle_rad = math.radians(angle_deg)
    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]
    best_config = None

    for width in plate_widths:
        est_courses = math.ceil(total_slant / width)
        course_slant = total_slant / est_courses

        break_diameters = []
        for i in range(est_courses + 1):
            rem_slant = total_slant - (i * course_slant)
            break_radius = rem_slant * math.sin(angle_rad)
            break_diameters.append(round(break_radius * 2, 2))

        config = {
            "Total Slant Height": round(total_slant, 2),
            "Number of Courses": est_courses,
            "Course Slant Height": round(course_slant, 2),
            "Break Diameters (Top → Bottom)": break_diameters,
            "Used Plate Width": width
        }

        if best_config is None or config["Number of Courses"] < best_config["Number of Courses"]:
            best_config = config

    return best_config

# Arc layout logic per course

def estimate_plate_usage_per_course(course_info, plate_width, plate_length, segments_per_course=4):
    results = []
    diameters = course_info["Break Diameters (Top → Bottom)"]
    course_slant = course_info["Course Slant Height"]

    for i in range(course_info["Number of Courses"]):
        d_top = diameters[i]
        d_bot = diameters[i + 1]
        r1 = d_top / 2
        r2 = d_bot / 2
        r_avg = (r1 + r2) / 2
        arc_angle = (2 * math.pi) / segments_per_course
        arc_width = arc_angle * r_avg

        if course_slant > plate_width:
            results.append({"course": i+1, "segments": segments_per_course, "fit": 0, "plates": "❌ Too tall for plate"})
            continue

        fit_count = math.floor(plate_length / arc_width)
        plates = math.ceil(segments_per_course / fit_count) if fit_count > 0 else "Invalid"
        waste = (plates * plate_width * plate_length) - (arc_width * course_slant * segments_per_course) if isinstance(plates, int) else None

        results.append({"course": i+1, "segments": segments_per_course, "fit": fit_count, "plates": plates, "waste": waste})

    return results

# Optimizer
def optimize_plate_usage(area_needed, plate_options, course_info):
    options = []
    for w, l in plate_options:
        layout = estimate_plate_usage_per_course(course_info, w, l)
        if any(isinstance(r["plates"], str) for r in layout):
            continue
        plates = sum(r["plates"] for r in layout if isinstance(r["plates"], int))
        waste = (plates * w * l) - area_needed
        options.append((plates, (w, l), waste, layout))
    options.sort(key=lambda x: (x[0], x[2]))
    return options[0] if options else None

# Main logic
if st.button("Calculate Cone Layout"):
    slant = calculate_slant_height(diameter, angle)
    cone_area = math.pi * (diameter / 2) * slant
    course_info = calculate_courses_and_breaks(diameter, angle, moc)
    plate_options = get_plate_options(moc)
    best = optimize_plate_usage(cone_area, plate_options, course_info)

    if best:
        plates_needed, (w, l), waste, layout = best
        st.subheader("\U0001F3E2 Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Size**: {w}\" x {l}\"")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")

        st.subheader("\U0001F528 Estimated Plate Usage Per Course")
        for r in layout:
            if isinstance(r["plates"], str):
                st.write(f"**Course {r['course']}**: ❌ {r['plates']}")
            else:
                st.write(f"**Course {r['course']}**: {r['segments']} pieces → fits {r['fit']} per plate → **{r['plates']} plate(s)** — Estimated Waste: {round(r['waste'], 2)} in²")

        total = sum(r['plates'] for r in layout if isinstance(r['plates'], int))
        st.markdown(f"**Summary → Total Plates Needed: {total} using {w}\" x {l}\" plates**")

        st.subheader("\U0001F3D9 Cone Course Layout")
        st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
        st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
        st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
        st.write("**Break Diameters (top → bottom):**")
        st.json(course_info["Break Diameters (Top → Bottom)"])
    else:
        st.error("❌ No viable plate layout found. Try reducing number of segments or using a different material.")
