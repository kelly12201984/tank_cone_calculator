import streamlit as st
import math
import matplotlib.pyplot as plt

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
    Calculates how many gore segments fit horizontally along the plate length.
    Gores are mirrored alternately (upright then upside-down) and placed side by side.
    """
    return max(1, plate_length // gore_width)

# --- Estimate per-course plate usage (realistic gore layout) ---
def estimate_plate_usage_per_course(course_info, plate_options, segments_per_course=4):
    """Return best plate usage for each course allowing different plate sizes."""
    results = []
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

        for plate_width, plate_length in plate_options:
            if slant > plate_width:
                continue  # gore slant does not fit plate width

            segments_fit = math.floor(plate_length / arc_width)
            if segments_fit <= 0:
                continue  # not even one gore fits

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
                "plate_width": plate_width,
                "plate_length": plate_length,
                "waste": waste,
                "gore_width": round(arc_width, 2),
            }

            if best_option is None or (option["plates"], option["waste"]) < (
                best_option["plates"], best_option["waste"]
            ):
                best_option = option
        if best_option:
            results.append(best_option)
        else:
            results.append({
                "course": i + 1,
                "segments": segments_per_course,
                "fit": 0,
                "plates": "❌ No fit",
                "plate_width": "N/A",
                "plate_length": "N/A",
                "waste": "N/A",
                "gore_width": round(arc_width, 2),
            })

    return results

# --- Visualization helper ---
def plot_course_layout(result, course_slant_height, max_width=None):
    """Return a matplotlib Figure showing gore layout on a plate."""
    width = result.get("plate_width")
    length = result.get("plate_length")
    fit = result.get("fit")
    gore_w = result.get("gore_width")

    if isinstance(width, str) or fit <= 0:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No fit", ha="center", va="center")
        ax.axis("off")
        return fig

    fig, ax = plt.subplots(figsize=(8, 4))
    # Draw plate boundary
    ax.add_patch(plt.Rectangle((0, 0), length, width, fill=False, edgecolor="black", linewidth=1.2))

    # Draw gore polygons alternating orientation
    colors = ["tab:blue", "tab:orange"]
    for idx in range(fit):
        x0 = idx * gore_w
        if idx % 2 == 0:
            poly = [(x0, 0), (x0 + gore_w / 2, course_slant_height), (x0 + gore_w, 0)]
        else:
            poly = [(x0, course_slant_height), (x0 + gore_w / 2, 0), (x0 + gore_w, course_slant_height)]
        patch = plt.Polygon(poly, closed=True, facecolor=colors[idx % 2], edgecolor="gray", alpha=0.4)
        ax.add_patch(patch)
        ax.text(x0 + gore_w / 2, course_slant_height / 2, str(idx + 1), ha="center", va="center", fontsize=8)

    ax.set_xlim(0, length)
    if max_width:
        ax.set_ylim(0, max_width)
    else:
        ax.set_ylim(0, width)
    ax.set_aspect("auto")
    ax.set_xlabel(f"Plate Length (in) — {length}\"")
    ax.set_ylabel(f"Plate Width (in) — {width}\"")
    ax.set_title(f"Course {result['course']} Layout")
    fig.tight_layout()
    return fig
                        
# --- Optimizer
def optimize_plate_usage(area_needed, plate_options, course_info, segments_per_course):
    """Choose per-course plate sizes to minimize plates then waste."""
    course_layout = estimate_plate_usage_per_course(course_info, plate_options, segments_per_course)

    if any(isinstance(res["plates"], str) for res in course_layout):
        return None

    total_plates = sum(res["plates"] for res in course_layout)
    total_waste = sum(res["waste"] for res in course_layout)

    return total_plates, "mixed", total_waste, course_layout

# --- UI button logic
if st.button("Calculate Cone Layout"):
    slant_height = calculate_slant_height(diameter, angle)
    course_info = calculate_courses_and_breaks(diameter, angle, moc)
    r_large = diameter / 2
    r_small = BOTTOM_DIAMETER / 2
    cone_area = math.pi * (r_large + r_small) * slant_height
    plate_options = get_plate_options(moc)
    max_width = max(w for w, _ in plate_options)

    best = optimize_plate_usage(cone_area, plate_options, course_info, segments_per_course)
if best:
        plates_needed, _, waste, layout = best

        used_sizes = {
            (res["plate_width"], res["plate_length"])
            for res in layout
            if isinstance(res["plates"], int)
        }
        plate_desc = ", ".join(f'{w}" x {l}"' for w, l in sorted(used_sizes)) if used_sizes else "N/A"

        st.subheader("🧱 Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Sizes**: {plate_desc}")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")

        st.subheader("🔨 Estimated Plate Usage Per Course")
        for result in layout:
            if isinstance(result["plates"], str):
                st.write(f"**Course {result['course']}**: {result['segments']} pieces ➝ ❌ {result['plates']}")
                fig = plot_course_layout(result, course_info["Course Slant Height"], max_width)
                st.pyplot(fig)
            else:
                st.write(
                    f"**Course {result['course']}**: {result['segments']} pieces ➝ "
                    f"fits {result['fit']} per plate of size {result['plate_width']}\" x {result['plate_length']}\" ➝ "
                    f"{result['plates']} plate(s) — Estimated Waste: {result['waste']} in²"
                )
                fig = plot_course_layout(result, course_info["Course Slant Height"], max_width)
                st.pyplot(fig)

        st.markdown(f"**Summary ➝ Total Plates Needed**: {plates_needed} using {plate_desc} plates")

        st.subheader("🏛️ Cone Course Layout")
        st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
        st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
        st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
        st.write("**Break Diameters (top → bottom)**:")
        st.json(course_info["Break Diameters (Top → Bottom)"])
else:
        st.error("❌ No viable plate layout found. Try reducing number of segments or using a different material.")
