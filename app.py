# Concentric Cone Material & Layout Estimator (Refined: Auto + Override)
import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Concentric Cone Estimator", layout="centered")
st.title("Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")
st.markdown("Small (bottom) diameter is fixed at 2 inches.")

# --- Inputs
BOTTOM_DIAMETER = 2
diameter = st.number_input("Tank Diameter (in inches)", min_value=1, value=168)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1, value=60)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

# --- Slant height calculation
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

def find_optimal_gores_per_course(course_info, plate_options):
    breaks = course_info["Break Diameters"]
    slant = course_info["Course Slant Height"]
    best_gores = []

    for i in range(course_info["Number of Courses"]):
        best = None
        d_top, d_bottom = breaks[i], breaks[i + 1]
        r_outer, r_inner = d_top / 2, d_bottom / 2

        for segs in range(2, 13, 2):
            arc_angle = (2 * math.pi) / segs
            avg_radius = (r_outer + r_inner) / 2
            arc_width = arc_angle * avg_radius

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
                    "Course": i + 1,
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
        best_gores.append(best)
    return best_gores

def override_gores_layout(course_info, plate_options, custom_gores):
    breaks = course_info["Break Diameters"]
    slant = course_info["Course Slant Height"]
    output = []

    for i, segs in enumerate(custom_gores):
        best = None
        d_top, d_bottom = breaks[i], breaks[i + 1]
        r_outer, r_inner = d_top / 2, d_bottom / 2
        arc_angle = (2 * math.pi) / segs
        avg_radius = (r_outer + r_inner) / 2
        arc_width = arc_angle * avg_radius

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
            best = {
                "Course": i + 1,
                "Gores": segs,
                "Plate Size": f"{plate_w}\" x {plate_l}\"",
                "Plates": plates,
                "Fit/Plate": fit,
                "Waste (in²)": waste,
                "Width": plate_w,
                "Length": plate_l,
                "Arc Width": round(arc_width, 2)
            }
            break
        output.append(best if best else {"Course": i + 1, "Gores": segs, "Plate Size": "N/A", "Plates": "No Fit", "Fit/Plate": 0, "Waste (in²)": "-"})
    return output

def plot_layout(result, slant_height):
    if isinstance(result["Plates"], str):
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No fit", ha="center", va="center")
        ax.axis("off")
        return fig

    fig, ax = plt.subplots(figsize=(8, 4))
    width, length = result["Width"], result["Length"]
    gore_w = result["Arc Width"]
    fit = result["Fit/Plate"]

    for i in range(fit):
        x0 = i * gore_w
        poly = [(x0, 0), (x0 + gore_w / 2, slant_height), (x0 + gore_w, 0)] if i % 2 == 0 else [(x0, slant_height), (x0 + gore_w / 2, 0), (x0 + gore_w, slant_height)]
        ax.add_patch(plt.Polygon(poly, closed=True, alpha=0.4))
    ax.add_patch(plt.Rectangle((0, 0), length, width, fill=False, edgecolor="black"))
    ax.set_xlim(0, length)
    ax.set_ylim(0, width)
    ax.set_title(f"Course {result['Course']} Layout")
    return fig

# --- Main Execution
if st.button("Calculate Layout"):
    course_info = calculate_courses_and_breaks(diameter, angle, moc)
    plate_options = get_plate_options(moc)

    st.subheader("Optimal Gores per Course (Auto-calculated)")
    optimal_layout = find_optimal_gores_per_course(course_info, plate_options)
    df_auto = pd.DataFrame(optimal_layout)
    st.table(df_auto[["Course", "Gores", "Plate Size", "Plates", "Fit/Plate", "Waste (in²)"]])

    st.markdown(f"**Total Slant Height:** {course_info['Total Slant Height']} inches")
    st.markdown(f"**Course Slant Height:** {course_info['Course Slant Height']} inches")
    st.markdown(f"**Break Diameters (top → bottom):** {course_info['Break Diameters']}")

    st.subheader("Override Gores per Course (Manual)")
    custom_gores = []
    for i in range(course_info["Number of Courses"]):
        gore = st.slider(f"Course {i+1} Gores", min_value=1, max_value=12, value=optimal_layout[i]["Gores"], step=1)
        custom_gores.append(gore)

    manual_layout = override_gores_layout(course_info, plate_options, custom_gores)
    df_manual = pd.DataFrame(manual_layout)

    st.subheader("Manual Layout Summary")
    st.table(df_manual[["Course", "Gores", "Plate Size", "Plates", "Fit/Plate", "Waste (in²)"]])

    st.subheader("Course Visual Layouts")
    for result in manual_layout:
        fig = plot_layout(result, course_info["Course Slant Height"])
        st.pyplot(fig)

    st.success("Layout calculated with both optimal and override gore counts.")
