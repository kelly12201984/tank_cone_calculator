
import streamlit as st
import math

st.set_page_config(page_title="Cone Material & Layout Estimator", layout="centered")

st.title("📐 Concentric Cone Material & Layout Estimator")
st.markdown("Enter the specs for the concentric cone, and get an estimate of the optimal plate layout.")

# Inputs
diameter = st.number_input("Tank Diameter (in inches)", min_value=1)
angle = st.number_input("Angle of Repose (in degrees)", min_value=1)
moc = st.selectbox("Material of Construction (MOC)", ["Stainless Steel", "Carbon Steel"])


def calculate_slant_height(diameter, angle_deg):
    radius = diameter / 2
    angle_rad = math.radians(angle_deg)
    slant = radius / math.sin(angle_rad)
    return round(slant, 2)


def calculate_cone_area(diameter, angle_deg):
    radius = diameter / 2
    slant_height = calculate_slant_height(diameter, angle_deg)
    return math.pi * radius * slant_height


def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:
        return [(w, l) for w in [96, 120] for l in [240, 360, 480]]


def calculate_courses_and_breaks(diameter, angle_deg, moc):
    angle_rad = math.radians(angle_deg)
    total_slant = calculate_slant_height(diameter, angle_deg)
    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]

    best_config = None

    for width in plate_widths:
        num_courses = math.ceil(total_slant / width)
        course_slant = total_slant / num_courses

        if course_slant > width:
            continue

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
            "Used Plate Width": width
        }

        if (best_config is None or
            config["Number of Courses"] < best_config["Number of Courses"] or
            (config["Number of Courses"] == best_config["Number of Courses"] and
             config["Used Plate Width"] < best_config["Used Plate Width"])):
            best_config = config

    return best_config


def estimate_plate_usage_per_course(course_info, plate_width, plate_length):
    break_diameters = course_info["Break Diameters (Top → Bottom)"]
    course_results = []

    for i in range(course_info["Number of Courses"]):
        d_top = break_diameters[i]
        d_bottom = break_diameters[i + 1]
        best_option = None

        for segments in [2, 4, 6, 8]:
            r_outer = d_top / 2
            r_inner = d_bottom / 2
            theta = (2 * math.pi) / segments
            arc_outer = r_outer * theta
            arc_inner = r_inner * theta
            segment_width = max(arc_outer, arc_inner)
            segment_height = r_outer - r_inner

            if segment_height > plate_width:
                continue

            segments_fit = math.floor(plate_length / segment_width)
            if segments_fit == 0:
                continue

            plates_needed = math.ceil(segments / segments_fit)
            waste = (plates_needed * plate_width * plate_length) - (segments * segment_width * segment_height)
            score = (plates_needed, round(waste, 2), abs(segments - 4))  # prefer 4 segments if tie

            if best_option is None or score < best_option["score"]:
                best_option = {
                    "course": i + 1,
                    "segments": segments,
                    "fit": segments_fit,
                    "plates": plates_needed,
                    "waste": round(waste, 2),
                    "score": score
                }

        if best_option:
            best_option.pop("score")
            course_results.append(best_option)
        else:
            course_results.append({
                "course": i + 1,
                "segments": "❌",
                "fit": 0,
                "plates": "Too tall or wide for plate",
                "waste": None
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


# Main execution
if st.button("Calculate Cone Layout"):
    slant_height = calculate_slant_height(diameter, angle)
    course_info = calculate_courses_and_breaks(diameter, angle, moc)
    cone_area = calculate_cone_area(diameter, angle)
    plate_options = get_plate_options(moc)
    best = optimize_plate_usage(cone_area, plate_options, course_info)

    if best:
        plates_needed, (plate_width, plate_length), waste = best
        course_layout = estimate_plate_usage_per_course(course_info, plate_width, plate_length)

        st.subheader("📊 Optimal Layout Recommendation")
        st.write(f"**Plates Required**: {plates_needed}")
        st.write(f"**Plate Size**: {plate_width}\" x {plate_length}\"")
        st.write(f"**Estimated Waste**: {round(waste, 2)} square inches")

        st.subheader("📐 Estimated Plate Usage Per Course")
        for result in course_layout:
            if isinstance(result["plates"], str):
                st.write(f"**Course {result['course']}**: ❌ {result['plates']}")
            else:
                st.write(
                    f"**Course {result['course']}**: {result['segments']} pieces → fits {result['fit']} per plate → "
                    f"{result['plates']} plate(s)** — Estimated Waste: {result['waste']} in²"
                )

        st.subheader("🧱 Cone Course Layout")
        st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
        st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
        st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
        st.write("**Break Diameters (top → bottom)**:")
        st.write(course_info["Break Diameters (Top → Bottom)"])
    else:
        st.error("❌ No viable plate layout found. Try reducing number of segments or using a different material.")
