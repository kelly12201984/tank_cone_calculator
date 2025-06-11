# Concentric Cone Estimator (v2.0 - Fixed Gores, Visuals, Export)
import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd
import io

# --- Config
st.set_page_config(page_title="Concentric Cone Estimator", layout="centered")
st.title("Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")
st.markdown("Small (bottom) diameter is fixed at 2 inches.")

# --- Inputs
opportunity_id = st.text_input("Opportunity ID (optional, used in export file name)")
diameter = st.number_input("Tank Diameter (in inches)", min_value=1, value=168)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1, value=60)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

BOTTOM_DIAMETER = 2

# --- Calculations
def calculate_slant_height(diameter, angle_deg, bottom_diameter=BOTTOM_DIAMETER):
    r_large = diameter / 2
    r_small = bottom_diameter / 2
    angle_rad = math.radians(angle_deg)
    slant = (r_large - r_small) / math.sin(angle_rad)
    return round(slant, 2)

def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

def calculate_courses_and_breaks(diameter, angle_deg, moc):
    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]
    total_slant = calculate_slant_height(diameter, angle_deg)
    angle_rad = math.radians(angle_deg)
    bottom_radius = BOTTOM_DIAMETER / 2

    max_width = max(plate_widths)
    num_courses = 2
    while total_slant / num_courses > max_width:
        num_courses += 1

    course_slant = total_slant / num_courses
    used_width = next((w for w in sorted(plate_widths) if w >= course_slant), max_width)
    break_diameters = [round((bottom_radius + (total_slant - i * course_slant) * math.sin(angle_rad)) * 2, 2) for i in range(num_courses + 1)]

    return {
        "Total Slant Height": round(total_slant, 2),
        "Number of Courses": num_courses,
        "Course Slant Height": round(course_slant, 2),
        "Break Diameters": break_diameters,
        "Used Plate Width": used_width,
    }

def find_best_layout(course_num, segs, d_top, d_bottom, slant, plate_options):
    r_outer, r_inner = d_top / 2, d_bottom / 2
    arc_angle = (2 * math.pi) / segs
    avg_radius = (r_outer + r_inner) / 2
    arc_width = arc_angle * avg_radius
    best = None

    for plate_w, plate_l in plate_options:
        if slant > plate_w:
            continue
        fit = math.floor(plate_l / arc_width)
        if fit <= 0:
            continue
        plates = math.ceil(segs / fit)
        outer_area = math.pi * r_outer**2
        inner_area = math.pi * r_inner**2
        segment_area = (outer_area - inner_area) * (arc_angle / (2 * math.pi))
        waste = round((plates * plate_w * plate_l) - (segs * segment_area), 2)
        option = {
            "Course": course_num + 1,
            "Gores": segs,
            "Plate Size": f"{plate_w}\" x {plate_l}\"",
            "Plates": plates,
            "Fit/Plate": fit,
            "Waste (in²)": waste,
            "Width": plate_w,
            "Length": plate_l,
            "Arc Width": round(arc_width, 2)
        }
        if best is None or (option["Plates"], option["Waste (in²)"]) < (best["Plates"], best["Waste (in²)"]):
            best = option
    return best

def find_optimal_gores_per_course(course_info, plate_options):
    breaks = course_info["Break Diameters"]
    slant = course_info["Course Slant Height"]
    best_gores = []

    for i in range(course_info["Number of Courses"]):
        d_top, d_bottom = breaks[i], breaks[i + 1]
        best = None
        for segs in range(2, 13, 2):
            layout = find_best_layout(i, segs, d_top, d_bottom, slant, plate_options)
            if layout and (best is None or (layout["Plates"], layout["Waste (in²)"]) < (best["Plates"], best["Waste (in²)"])):
                best = layout
        best_gores.append(best)
    return best_gores

def override_gores_layout(course_info, plate_options, custom_gores):
    breaks = course_info["Break Diameters"]
    slant = course_info["Course Slant Height"]
    output = []

    for i, segs in enumerate(custom_gores):
        d_top, d_bottom = breaks[i], breaks[i + 1]
        layout = find_best_layout(i, segs, d_top, d_bottom, slant, plate_options)
        output.append(layout if layout else {"Course": i + 1, "Gores": segs, "Plate Size": "N/A", "Plates": "No Fit", "Fit/Plate": 0, "Waste (in²)": "-"})
    return output

def plot_layout(result):
    if isinstance(result["Plates"], str):
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No fit", ha="center", va="center")
        ax.axis("off")
        return fig

    fig, ax = plt.subplots(figsize=(10, 5))
    width = result["Width"]
    length = result["Length"]
    gore_w = result["Arc Width"]
    fit = result["Fit/Plate"]

    for i in range(fit):
        x0 = i * gore_w
        poly = [(x0, 0), (x0 + gore_w / 2, width), (x0 + gore_w, 0)] if i % 2 == 0 else [(x0, width), (x0 + gore_w / 2, 0), (x0 + gore_w, width)]
        ax.add_patch(plt.Polygon(poly, closed=True, alpha=0.4))
    ax.add_patch(plt.Rectangle((0, 0), length, width, fill=False, edgecolor="black"))
    ax.set_xlim(0, length)
    ax.set_ylim(0, width)
    ax.set_title(f"Course {result['Course']} Layout")
    return fig

# --- Execution
course_info = calculate_courses_and_breaks(diameter, angle, moc)
plate_options = get_plate_options(moc)

if "custom_gores" not in st.session_state or st.button("🔁 Recalculate Layout"):
    optimal_layout = find_optimal_gores_per_course(course_info, plate_options)
    st.session_state.custom_gores = [r["Gores"] for r in optimal_layout]

st.subheader("Override Gores per Course (Manual Override)")
custom_gores = []
for i in range(course_info["Number of Courses"]):
    gore = st.slider(f"Course {i + 1} Gores", min_value=1, max_value=12,
                     value=st.session_state.custom_gores[i], step=1, key=f"slider_{i}")
    custom_gores.append(gore)
st.session_state.custom_gores = custom_gores

optimal_layout = find_optimal_gores_per_course(course_info, plate_options)
manual_layout = override_gores_layout(course_info, plate_options, custom_gores)

# --- Display Tables
st.subheader("Optimal Gores per Course (Auto-calculated)")
st.table(pd.DataFrame(optimal_layout)[["Course", "Gores", "Plate Size", "Plates", "Fit/Plate", "Waste (in²)"]])

st.markdown(f"**Total Slant Height:** {course_info['Total Slant Height']} inches")
st.markdown(f"**Course Slant Height:** {course_info['Course Slant Height']} inches")
st.markdown(f"**Break Diameters (top → bottom):** {course_info['Break Diameters']}")

st.subheader("Manual Layout Summary")
df_manual = pd.DataFrame(manual_layout)
st.table(df_manual[["Course", "Gores", "Plate Size", "Plates", "Fit/Plate", "Waste (in²)"]])

# --- CSV Export (before visuals)
csv_buf = io.StringIO()
df_manual.to_csv(csv_buf, index=False)
file_name = f"{opportunity_id}_layout_summary.csv" if opportunity_id else "manual_layout_summary.csv"
st.download_button("📥 Download Manual Layout as CSV", csv_buf.getvalue(), file_name, "text/csv")

# --- Visuals
def plot_layout(result, slant):
        fig, ax = plt.subplots(figsize=(result["Length"] / 24, result["Width"] / 12))
        spacing = result["Arc Width"] * 0.05
        for i in range(result["Gores"]):
            x0 = i * (result["Arc Width"] + spacing)
            tri = [(x0, 0), (x0 + result["Arc Width"] / 2, slant), (x0 + result["Arc Width"], 0)] if i % 2 == 0 else [(x0, slant), (x0 + result["Arc Width"] / 2, 0), (x0 + result["Arc Width"], slant)]
            ax.add_patch(plt.Polygon(tri, closed=True, alpha=0.4))
        ax.add_patch(plt.Rectangle((0, 0), result["Length"], result["Width"], fill=False, edgecolor="black"))
        ax.set_xlim(0, result["Length"])
        ax.set_ylim(0, result["Width"])
        ax.set_title(f"Course {result['Course']} Layout")
        ax.set_xlabel("Plate Length (in)")
        ax.set_ylabel("Plate Width (in)")
        return fig

    st.subheader("Course Visual Layouts")
    for result in manual_layout:
        st.pyplot(plot_layout(result, st.session_state.course_info["Course Slant Height"]))

    st.success("Done! 🔆 Thank you for using Kelly's Cone Estimator!")
