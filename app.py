# Concentric Cone Material & Layout Estimator (Visual Scaling + Best Manual Fit)
import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd
import io

st.set_page_config(page_title="Concentric Cone Estimator", layout="wide")
st.title("Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")
st.markdown("Small (bottom) diameter is fixed at 2 inches.")

BOTTOM_DIAMETER = 2

diameter = st.number_input("Tank Diameter (in inches)", min_value=1, value=168)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1, value=60)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

# Session state
if "layout_ready" not in st.session_state:
    st.session_state.layout_ready = False
if "custom_gores" not in st.session_state:
    st.session_state.custom_gores = []

if st.button("Calculate Layout"):
    st.session_state.layout_ready = True
    def calculate_slant_height(diameter, angle_deg):
        r_large = diameter / 2
        r_small = BOTTOM_DIAMETER / 2
        angle_rad = math.radians(angle_deg)
        return round((r_large - r_small) / math.sin(angle_rad), 2)

    def get_plate_options(moc):
        return [(w, l) for w in ([48, 60] if moc == "Stainless Steel" else [96, 120])
                for l in ([96, 120, 144] + list(range(180, 481)) if moc == "Stainless Steel" else [240, 360, 480])]

    def calculate_courses(diameter, angle, moc):
        plate_widths = [w for w, _ in get_plate_options(moc)]
        total_slant = calculate_slant_height(diameter, angle)
        angle_rad = math.radians(angle)
        bottom_radius = BOTTOM_DIAMETER / 2
        max_width = max(plate_widths)
        num_courses = 2
        while total_slant / num_courses > max_width:
            num_courses += 1
        course_slant = total_slant / num_courses
        breaks = [round((bottom_radius + (total_slant - i * course_slant) * math.sin(angle_rad)) * 2, 2)
                  for i in range(num_courses + 1)]
        return total_slant, course_slant, breaks, num_courses

    def find_best_layout(segs, d_top, d_bottom, slant, plate_options):
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
            waste = round((plates * plate_w * plate_l) - ((math.pi * (r_outer**2 - r_inner**2)) * (segs / (2 * math.pi))), 2)
            option = {
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

    def generate_layouts(breaks, slant, plate_options, num_courses, gores_override=None):
        layout = []
        for i in range(num_courses):
            segs = gores_override[i] if gores_override else None
            best = None
            if segs:
                best = find_best_layout(segs, breaks[i], breaks[i+1], slant, plate_options)
            else:
                for s in range(2, 13, 2):
                    opt = find_best_layout(s, breaks[i], breaks[i+1], slant, plate_options)
                    if not best or (opt["Plates"], opt["Waste (in²)"]) < (best["Plates"], best["Waste (in²)"]):
                        best = opt
            best.update({"Course": i + 1})
            layout.append(best)
        return layout

    total_slant, course_slant, break_diams, num_courses = calculate_courses(diameter, angle, moc)
    plates = get_plate_options(moc)
    optimal = generate_layouts(break_diams, course_slant, plates, num_courses)

    st.session_state.course_info = {
        "Total Slant Height": total_slant,
        "Course Slant Height": course_slant,
        "Break Diameters": break_diams,
        "Number of Courses": num_courses
    }
    st.session_state.plate_options = plates
    st.session_state.optimal_layout = optimal
    st.session_state.custom_gores = [row["Gores"] for row in optimal]

if st.session_state.layout_ready:
    st.subheader("Optimal Gores per Course (Auto-calculated)")
    df_auto = pd.DataFrame(st.session_state.optimal_layout)
    st.table(df_auto[["Course", "Gores", "Plate Size", "Plates", "Fit/Plate", "Waste (in²)"]])

    st.markdown(f"**Total Slant Height:** {st.session_state.course_info['Total Slant Height']} inches")
    st.markdown(f"**Course Slant Height:** {st.session_state.course_info['Course Slant Height']} inches")
    st.markdown(f"**Break Diameters (top → bottom):** {st.session_state.course_info['Break Diameters']}")

    st.subheader("Override Gores per Course")
    for i in range(st.session_state.course_info["Number of Courses"]):
        st.session_state.custom_gores[i] = st.slider(
            f"Course {i+1} Gores", 1, 12, st.session_state.custom_gores[i], key=f"gore_slider_{i}"
        )

    manual = generate_layouts(
        st.session_state.course_info["Break Diameters"],
        st.session_state.course_info["Course Slant Height"],
        st.session_state.plate_options,
        st.session_state.course_info["Number of Courses"],
        st.session_state.custom_gores
    )

    st.subheader("Manual Layout Summary")
    df_manual = pd.DataFrame(manual)
    st.table(df_manual[["Course", "Gores", "Plate Size", "Plates", "Fit/Plate", "Waste (in²)"]])

    csv_buffer = io.StringIO()
    df_manual.to_csv(csv_buffer, index=False)
    st.download_button("📥 Download Manual Layout as CSV", csv_buffer.getvalue(), "manual_layout_summary.csv", "text/csv")

    def plot_layout(result, slant_height):
        fig, ax = plt.subplots(figsize=(result["Length"] / 24, result["Width"] / 12))
        spacing = result["Arc Width"] * 0.05
        for i in range(result["Gores"]):
            x0 = i * (result["Arc Width"] + spacing)
            tri = [(x0, 0), (x0 + result["Arc Width"] / 2, slant_height), (x0 + result["Arc Width"], 0)] if i % 2 == 0 else [(x0, slant_height), (x0 + result["Arc Width"] / 2, 0), (x0 + result["Arc Width"], slant_height)]
            ax.add_patch(plt.Polygon(tri, closed=True, alpha=0.4))
        ax.add_patch(plt.Rectangle((0, 0), result["Length"], result["Width"], fill=False, edgecolor="black"))
        ax.set_xlim(0, result["Length"])
        ax.set_ylim(0, result["Width"])
        ax.set_title(f"Course {result['Course']} Layout")
        ax.set_xlabel("Plate Length (in)")
        ax.set_ylabel("Plate Width (in)")
        return fig

    st.subheader("Course Visual Layouts")
    for result in manual:
        st.pyplot(plot_layout(result, st.session_state.course_info["Course Slant Height"]))

    st.success("Layout complete. Visuals now reflect true plate size. CSV ready.")
