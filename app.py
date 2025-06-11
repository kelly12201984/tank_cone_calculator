# Concentric Cone Material & Layout Estimator (Stable CSV + Opportunity ID + Visual Fixes)
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

# --- User Input ---
opportunity_id = st.text_input("Opportunity ID (optional, used in export file name)")
diameter = st.number_input("Tank Diameter (in inches)", min_value=1, value=168)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1, value=60)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])

if "layout_ready" not in st.session_state:
    st.session_state.layout_ready = False
if "custom_gores" not in st.session_state:
    st.session_state.custom_gores = []

# --- Trigger Calculation ---
if st.button("Calculate Layout"):
    st.session_state.layout_ready = True
    def calculate_slant_height(d, a):
        r_large, r_small = d / 2, BOTTOM_DIAMETER / 2
        return round((r_large - r_small) / math.sin(math.radians(a)), 2)

    def get_plate_options(material):
        return [(w, l) for w in ([48, 60] if material == "Stainless Steel" else [96, 120])
                for l in ([96, 120, 144] + list(range(180, 481)) if material == "Stainless Steel" else [240, 360, 480])]

    def calculate_courses(d, a, material):
        widths = [w for w, _ in get_plate_options(material)]
        total = calculate_slant_height(d, a)
        angle_rad = math.radians(a)
        r_small = BOTTOM_DIAMETER / 2
        num = 2
        while total / num > max(widths):
            num += 1
        slant = total / num
        breaks = [round((r_small + (total - i * slant) * math.sin(angle_rad)) * 2, 2) for i in range(num + 1)]
        return total, slant, breaks, num

    def best_layout(segs, d_top, d_bottom, slant, options):
        r_outer, r_inner = d_top / 2, d_bottom / 2
        arc_angle = (2 * math.pi) / segs
        arc_width = arc_angle * ((r_outer + r_inner) / 2)
        best = None
        for w, l in options:
            if slant > w:
                continue
            fit = math.floor(l / arc_width)
            if fit <= 0:
                continue
            plates = math.ceil(segs / fit)
            waste = round((plates * w * l) - ((math.pi * (r_outer**2 - r_inner**2)) * (segs / (2 * math.pi))), 2)
            option = {
                "Gores": segs,
                "Plate Size": f"{w}\" x {l}\"",
                "Plates": plates,
                "Fit/Plate": fit,
                "Waste (in²)": waste,
                "Width": w,
                "Length": l,
                "Arc Width": round(arc_width, 2)
            }
            if best is None or (option["Plates"], option["Waste (in²)"]) < (best["Plates"], best["Waste (in²)"]):
                best = option
        return best

    def generate_layouts(breaks, slant, options, num_courses, override=None):
        out = []
        for i in range(num_courses):
            segs = override[i] if override else None
            best = None
            if segs:
                best = best_layout(segs, breaks[i], breaks[i+1], slant, options)
            else:
                for s in range(2, 13, 2):
                    trial = best_layout(s, breaks[i], breaks[i+1], slant, options)
                    if not best or (trial["Plates"], trial["Waste (in²)"]) < (best["Plates"], best["Waste (in²)"]):
                        best = trial
            best.update({"Course": i + 1})
            out.append(best)
        return out

    total, slant, breaks, count = calculate_courses(diameter, angle, moc)
    plate_options = get_plate_options(moc)
    optimal = generate_layouts(breaks, slant, plate_options, count)
    st.session_state.course_info = {
        "Total Slant Height": total,
        "Course Slant Height": slant,
        "Break Diameters": breaks,
        "Number of Courses": count
    }
    st.session_state.plate_options = plate_options
    st.session_state.optimal_layout = optimal
    st.session_state.custom_gores = [row["Gores"] for row in optimal]

# --- UI Rendering ---
if st.session_state.layout_ready:
    st.subheader("Optimal Gores per Course (Auto-calculated)")
    df_opt = pd.DataFrame(st.session_state.optimal_layout)
    st.table(df_opt[["Course", "Gores", "Plate Size", "Plates", "Fit/Plate", "Waste (in²)"]])

    st.markdown(f"**Total Slant Height:** {st.session_state.course_info['Total Slant Height']} inches")
    st.markdown(f"**Course Slant Height:** {st.session_state.course_info['Course Slant Height']} inches")
    st.markdown(f"**Break Diameters (top → bottom):** {st.session_state.course_info['Break Diameters']}")

    st.subheader("Override Gores per Course")
    for i in range(st.session_state.course_info["Number of Courses"]):
        st.session_state.custom_gores[i] = st.slider(
            f"Course {i+1} Gores", 1, 12, st.session_state.custom_gores[i], key=f"gore_slider_{i}"
        )

    manual_layout = generate_layouts(
        st.session_state.course_info["Break Diameters"],
        st.session_state.course_info["Course Slant Height"],
        st.session_state.plate_options,
        st.session_state.course_info["Number of Courses"],
        st.session_state.custom_gores
    )

    st.subheader("Manual Layout Summary")
    df_manual = pd.DataFrame(manual_layout)
    if opportunity_id:
        df_manual.insert(0, "Opportunity ID", opportunity_id)
    st.table(df_manual[[col for col in df_manual.columns if col != "Arc Width" and col != "Width" and col != "Length"]])

    # --- CSV Export ---
    csv_buf = io.StringIO()
    df_manual.to_csv(csv_buf, index=False)
    file_name = f"{opportunity_id}_layout_summary.csv" if opportunity_id else "manual_layout_summary.csv"
    st.download_button("📥 Download Manual Layout as CSV", csv_buf.getvalue(), file_name, "text/csv")

    # --- Visuals ---
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

    st.success("Done! Export includes optional Opportunity ID. Visuals scaled accurately.")
