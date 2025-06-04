import streamlit as st
import math

st.set_page_config(page_title="Concentric Cone Material & Layout Estimator", layout="centered")
st.title("📈 Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")

# --- Inputs
diameter = st.number_input("Tank Diameter (in inches)", min_value=1, value=168)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1, value=60)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])
# Optional: Override number of segments (gores) per course
segments_per_course = st.number_input(
    "Segments Per Course (Gores)", min_value=2, max_value=12, value=4, step=1,
    help="How many segments to divide each course into (4 is standard)"
)

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
def estimate_plate_usage_per_course(course_info, plate_width, plate_length, segments_per_course=4):
    results = []
    angle_rad = math.radians(angle)
    break_diams = course_info["Break Diameters (Top → Bottom)"]
    slant = course_info["Course Slant Height"]

    # Add all valid lengths for this plate width
    if plate_width == 96:
        plate_lengths = [240, 360, 480]
    elif plate_width == 120:
        plate_lengths = [240, 360, 480]
    elif plate_width == 48:
        plate_lengths = [96, 120, 144] + list(range(180, 481))
    elif plate_width == 60:
        plate_lengths = [96, 120, 144] + list(range(180, 481))
    else:
        plate_lengths = [plate_length]  # fallback

    for i in range(course_info["Number of Courses"]):
        d_top = break_diams[i]
        d_bottom = break_diams[i + 1]
        r_outer = d_top / 2
        r_inner = d_bottom / 2
        arc_angle = (2 * math.pi) / segments_per_course
        avg_radius = (r_outer + r_inner) / 2
        arc_width = arc_angle * avg_radius

        # Too tall?
        if slant > plate_width:
            results.append({
                "course": i + 1,
                "segments": segments_per_course,
                "fit": 0,
                "plates": "❌ Too tall for plate",
                "waste": "N/A"
            })
            continue

        best_option = None
        for length in sorted(plate_lengths):
            segments_fit = math.floor(length / arc_width)
            if segments_fit <= 0:
                continue
            plates_needed = math.ceil(segments_per_course / segments_fit)
            plate_area = plate_width * length

            # Area of each segment (sector ring)
            outer_area = math.pi * r_outer ** 2
            inner_area = math.pi * r_inner ** 2
            segment_area = (outer_area - inner_area) * (arc_angle / (2 * math.pi))
            total_segment_area = segment_area * segments_per_course
            total_plate_area = plates_needed * plate_area
            waste = round(total_plate_area - total_segment_area, 2)

            # Pick shortest viable plate
            if best_option is None or waste < best_option["waste"]:
                best_option = {
                    "course": i + 1,
                    "segments": segments_per_course,
                    "fit": segments_fit,
                    "plates": plates_needed,
                    "waste": waste,
                    "plate_length": length
                }

            if plates_needed == 1:
                break  # Optimal already

        if best_option:
            results.append(best_option)
        else:
            results.append({
                "course": i + 1,
                "segments": segments_per_course,
                "fit": 0,
                "plates": "❌ No fit",
                "waste": "N/A"
            })

    return results

# --- Optimizer
def optimize_plate_usage(area_needed, plate_options, course_info, segments_per_course):
    options = []
    for w, l in plate_options:
        course_layout = estimate_plate_usage_per_course(course_info, w, l, segments_per_course)
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

    best = optimize_plate_usage(cone_area, plate_options, course_info, segments_per_course)

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
