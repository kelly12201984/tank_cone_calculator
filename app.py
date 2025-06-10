import streamlit as st
import math

st.set_page_config(page_title="Concentric Cone Material & Layout Estimator", layout="centered")
st.title("📈 Concentric Cone Material & Layout Estimator")
st.markdown(
    "Enter the specs for the concentric cone, and get an estimate of the optimal plate layout."
)
st.markdown("Small (bottom) diameter is fixed at 2 inches.")

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
BOTTOM_DIAMETER = 2  # fixed bottom opening of the truncated cone in inches

def calculate_slant_height(diameter, angle_deg, bottom_diameter=BOTTOM_DIAMETER):
    """Return the slant height of a truncated cone."""
    r_large = diameter / 2
    r_small = bottom_diameter / 2
    angle_rad = math.radians(angle_deg)
    slant = (r_large - r_small) / math.sin(angle_rad)
    return round(slant, 2)

# --- Plate options
def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:
        return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

# --- Cone course breakdown
def calculate_courses_and_breaks(diameter, angle_deg, moc, bottom_diameter=BOTTOM_DIAMETER):
    """Return course info ensuring each course fits available plate widths."""
    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]
    total_slant = calculate_slant_height(diameter, angle_deg, bottom_diameter)
    angle_rad = math.radians(angle_deg)
    bottom_radius = bottom_diameter / 2

    # Try two courses first, increasing until each course fits the widest plate
    max_width = max(plate_widths)
    num_courses = 2
    while total_slant / num_courses > max_width:
        num_courses += 1

    course_slant = total_slant / num_courses
    plate_widths.sort()
    used_width = next((w for w in plate_widths if w >= course_slant), max_width)

    break_diameters = []
    for i in range(num_courses + 1):
        rem_slant = total_slant - (i * course_slant)
        break_radius = bottom_radius + rem_slant * math.sin(angle_rad)
        break_diameters.append(round(break_radius * 2, 2))

    return {
        "Total Slant Height": round(total_slant, 2),
        "Number of Courses": num_courses,
        "Course Slant Height": round(course_slant, 2),
        "Break Diameters (Top → Bottom)": break_diameters,
        "Used Plate Width": used_width,
    }

# --- Helper: Calculate how many gores fit on a plate ---
def fit_gore_segments_on_plate(gore_width, plate_length):
    """
    Calculates how many gore segments (side by side) can fit on the plate.
    Gores are laid side by side like cookie cutters.
    """
    return max(1, plate_length // gore_width)

# --- Estimate per-course plate usage (realistic gore layout) ---
def estimate_plate_usage_per_course(course_info, plate_width, plate_lengths, segments_per_course=4):
    results = []
    angle_rad = math.radians(angle)
    break_diams = course_info["Break Diameters (Top → Bottom)"]
    slant = course_info["Course Slant Height"]

    for i in range(course_info["Number of Courses"]):
        d_top = break_diams[i]
        d_bottom = break_diams[i + 1]
        r_outer = d_top / 2
        r_inner = d_bottom / 2
        arc_angle = (2 * math.pi) / segments_per_course
        avg_radius = (r_outer + r_inner) / 2
        arc_width = arc_angle * avg_radius

        best_option = None

        for plate_length in plate_lengths:
            if slant > plate_width:
                continue  # skip: too tall to fit

            segments_fit = math.floor(plate_length / arc_width)
            if segments_fit <= 0:
                continue  # not even one fits

            plates_needed = math.ceil(segments_per_course / segments_fit)
            outer_area = math.pi * r_outer ** 2
            inner_area = math.pi * r_inner ** 2
            segment_area = (outer_area - inner_area) * (arc_angle / (2 * math.pi))
            plate_area = plate_width * plate_length
            waste = round((plates_needed * plate_area) - (segments_per_course * segment_area), 2)

            option = {
                "course": i + 1,
                "segments": segments_per_course,
                "fit": segments_fit,
                "plates": plates_needed,
                "plate_length": plate_length,
                "waste": waste
            }

            if best_option is None or option["waste"] < best_option["waste"]:
                best_option = option

        if best_option:
            results.append(best_option)
        else:
            results.append({
                "course": i + 1,
                "segments": segments_per_course,
                "fit": 0,
                "plates": "❌ No fit",
                "plate_length": "N/A",
                "waste": "N/A"
            })

    return results

# --- Optimizer
def optimize_plate_usage(area_needed, plate_options, course_info, segments_per_course):
    options = []
    plate_widths = sorted(set(w for w, _ in plate_options))
    plate_lengths = sorted(set(l for _, l in plate_options))

    for w in plate_widths:
        course_layout = estimate_plate_usage_per_course(course_info, w, plate_lengths, segments_per_course)

        if any(isinstance(result["plates"], str) for result in course_layout):
            continue

        plates_needed = sum(result["plates"] for result in course_layout if isinstance(result["plates"], int))
        total_waste = sum(result["waste"] for result in course_layout if isinstance(result["waste"], (int, float)))

        options.append((plates_needed, (w, "mixed"), total_waste, course_layout))

    options.sort(key=lambda x: (x[0], x[2]))  # prioritize fewer plates, then less waste
    return options[0] if options else None

# --- UI button logic
if st.button("Calculate Cone Layout"):
    slant_height = calculate_slant_height(diameter, angle)
    course_info = calculate_courses_and_breaks(diameter, angle, moc)
    r_large = diameter / 2
    r_small = BOTTOM_DIAMETER / 2
    cone_area = math.pi * (r_large + r_small) * slant_height
    plate_options = get_plate_options(moc)

    best = optimize_plate_usage(cone_area, plate_options, course_info, segments_per_course)

    if best:
        plates_needed, (plate_w, plate_l), waste, layout = best

        # Find if lengths vary
        used_lengths = {res["plate_length"] for res in layout if isinstance(res["plate_length"], (int, float))}
        plate_length_desc = f'{plate_w}" x {"mixed" if len(used_lengths) > 1 else list(used_lengths)[0]}"'

        st.subheader("🧱 Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Size**: {plate_length_desc}")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")

        st.subheader("🔨 Estimated Plate Usage Per Course")
        for result in layout:
            if isinstance(result["plates"], str):
                st.write(f"**Course {result['course']}**: {result['segments']} pieces ➝ ❌ {result['plates']}")
            else:
                st.write(
                    f"**Course {result['course']}**: {result['segments']} pieces ➝ "
                    f"fits {result['fit']} per plate of size {plate_w}\" x {result['plate_length']}\" ➝ "
                    f"{result['plates']} plate(s) — Estimated Waste: {result['waste']} in²"
                )

        st.markdown(f"**Summary ➝ Total Plates Needed**: {plates_needed} using {plate_length_desc} plates")

        st.subheader("🏛️ Cone Course Layout")
        st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
        st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
        st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
        st.write("**Break Diameters (top → bottom)**:")
        st.json(course_info["Break Diameters (Top → Bottom)"])
    else:
        st.error("❌ No viable plate layout found. Try reducing number of segments or using a different material.")

