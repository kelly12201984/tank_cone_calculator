import streamlit as st
import math

st.set_page_config(page_title="Concentric Cone Material & Layout Estimator", layout="centered")
st.title("📈 Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")

# --- Inputs
diameter = st.number_input("Tank Diameter (in inches)", min_value=1, value=168)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1, value=60)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

# --- Slant height
def calculate_slant_height(diameter, angle_deg):
    radius = diameter / 2
    angle_rad = math.radians(angle_deg)
    slant = radius / math.sin(angle_rad)
    return round(slant, 2)

# --- Plate options
def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:
        return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

# --- Cone course breakdown
def calculate_courses_and_breaks(diameter, angle_deg, moc):
    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]
    total_slant = calculate_slant_height(diameter, angle_deg)
    angle_rad = math.radians(angle_deg)

    # Start with the narrowest plate width to create smaller, more realistic courses
    plate_widths.sort()

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

        if best_config is None or est_courses > best_config["Number of Courses"]:
            best_config = config

    return best_config

# --- Helper: Calculate how many gores fit on a plate ---
def fit_gore_segments_on_plate(gore_width, plate_length):
    """
    Calculates how many gore segments (side by side) can fit on the plate.
    Gores are laid side by side like cookie cutters.
    """
    return max(1, plate_length // gore_width)

# --- Estimate per-course plate usage (realistic gore layout) ---
def estimate_plate_usage_per_course(course_info, plate_width, plate_length):
    layout = []
    total_courses = course_info["Number of Courses"]
    course_slant = course_info["Course Slant Height"]
    break_diams = course_info["Break Diameters (Top → Bottom)"]
    angle_deg = math.degrees(math.atan(course_slant / ((break_diams[0] - break_diams[-1]) / 2)))
    angle_rad = math.radians(angle_deg)

    for i in range(total_courses):
        d_top = break_diams[i]
        d_bot = break_diams[i + 1]
        r1 = d_top / 2
        r2 = d_bot / 2
        slant_height = course_slant

        arc_length = math.pi * (r1 + r2)  # outer arc approx.
        flat_angle = arc_length / slant_height  # in radians
        arc_width = round(flat_angle * slant_height, 2)  # gore "chord width"

        segments = 4  # default
        gore_width = arc_width / segments
        fits = fit_gore_segments_on_plate(gore_width, plate_length)
        plates_needed = math.ceil(segments / fits)

        waste = (plates_needed * plate_width * plate_length) - (segments * slant_height * gore_width)

        layout.append({
            "course": i + 1,
            "segments": segments,
            "fit": fits,
            "plates": plates_needed,
            "waste": round(waste, 2)
        })

    return layout


# --- Optimizer
def optimize_plate_usage(area_needed, plate_options, course_info):
    options = []
    for w, l in plate_options:
        course_layout = estimate_plate_usage_per_course(course_info, w, l)
        if any(isinstance(result["plates"], str) for result in course_layout):
            continue
        plates_needed = sum(result["plates"] for result in course_layout if isinstance(result["plates"], int))
        plate_area = w * l
        total_waste = (plates_needed * plate_area) - area_needed
        options.append((plates_needed, (w, l), total_waste, course_layout))

    options.sort(key=lambda x: (x[0], x[2]))  # fewest plates, then least waste
    return options[0] if options else None

# --- UI button logic
if st.button("Calculate Cone Layout"):
    slant_height = calculate_slant_height(diameter, angle)
    course_info = calculate_courses_and_breaks(diameter, angle, moc)
    cone_area = math.pi * (diameter / 2) * slant_height
    plate_options = get_plate_options(moc)

    best = optimize_plate_usage(cone_area, plate_options, course_info)

    if best:
        plates_needed, (plate_w, plate_l), waste, layout = best

        st.subheader("🏗️ Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Size**: {plate_w}\" x {plate_l}\"")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")

        st.subheader("🔨 Estimated Plate Usage Per Course")
        for result in layout:
            if isinstance(result["plates"], str):
                st.write(f"**Course {result['course']}**: {result['plates']}")
            else:
                st.write(
                    f"**Course {result['course']}**: {result['segments']} pieces ➝ fits {result['fit']} per plate ➝ {result['plates']} plate(s)"
                    + f" — Estimated Waste: {result['waste']} in²"
                )

        st.markdown(f"**Summary ➝ Total Plates Needed**: {plates_needed} using {plate_w}\" x {plate_l}\" plates")

        st.subheader("🏛️ Cone Course Layout")
        st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
        st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
        st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
        st.write("**Break Diameters (top → bottom)**:")
        st.json(course_info["Break Diameters (Top → Bottom)"])
    else:
        st.error("❌ No viable plate layout found. Try reducing number of segments or using a different material.")
