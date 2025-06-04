
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
            segment_arc = max(arc_outer, arc_inner)
            segment_radial = r_outer - r_inner

            # Side-by-side layout logic: segment_arc = "width", segment_radial = "height"
            if segment_arc > plate_width or segment_radial > plate_length:
                continue

            # Nest segments along plate length
            segments_fit = math.floor(plate_length / segment_radial)
            if segments_fit == 0:
                continue

            plates_needed = math.ceil(segments / segments_fit)
            used_area = segments * segment_arc * segment_radial
            waste = (plates_needed * plate_width * plate_length) - used_area
            score = (plates_needed, round(waste, 2), abs(segments - 4))  # prefer 4 segments if tied

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
                "plates": "Too big for plate (even flipped)",
                "waste": None
            })

    return course_results

#Per-Course Plate Optimization and Nesting

def optimize_plate_usage(area_needed, plate_options, course_info):
    options = []
    for w, l in plate_options:
        total_plates = 0
        total_waste = 0
        fits_all = True

        for i in range(course_info["Number of Courses"]):
            d_top = course_info["Break Diameters (Top → Bottom)"][i]
            d_bottom = course_info["Break Diameters (Top → Bottom)"][i + 1]
            slant = course_info["Course Slant Height"]

            arc_angle = (2 * math.pi) / 4  # 4 pieces per course
            r_outer = d_top / 2
            r_inner = d_bottom / 2
            avg_radius = (r_outer + r_inner) / 2
            arc_width = arc_angle * avg_radius

            if slant > w:
                fits_all = False
                break

            segments_fit = math.floor(l / arc_width)
            if segments_fit == 0:
                fits_all = False
                break

            plates_needed = math.ceil(4 / segments_fit)  # 4 segments per course
            plate_area = w * l
            course_area = math.pi * (r_outer**2 - r_inner**2) / 4
            waste = (plates_needed * plate_area) - course_area

            total_plates += plates_needed
            total_waste += waste

        if fits_all:
            options.append((total_plates, (w, l), total_waste))

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
