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
def model_segment_geometry(d_top, d_bottom, segments_per_course):
    r_outer = d_top / 2
    r_inner = d_bottom / 2
    theta = (2 * math.pi) / segments_per_course  # arc angle in radians

    # Width: arc length (outer edge is the longest)
    arc_length_outer = r_outer * theta
    arc_length_inner = r_inner * theta
    segment_width = max(arc_length_outer, arc_length_inner)

    # Height: difference in radii (radial span of the sector)
    segment_height = r_outer - r_inner

    return segment_width, segment_height


def get_plate_options(moc):
    if moc == "Stainless Steel":
        return [(w, l) for w in [48, 60] for l in [96, 120, 144] + list(range(180, 481))]
    else:  # Carbon Steel
        return [(w, l) for w in [96, 120] for l in [240, 360, 480]]

def optimize_plate_usage(area_needed, plate_options, course_info):
    options = []
    for w, l in plate_options:
        plate_area = w * l
        course_layout = estimate_plate_usage_per_course(course_info, w, l)

        # ❌ Skip if any course is too tall for this plate
        if any(isinstance(result["plates"], str) for result in course_layout):
            continue

        # ✅ Only sum valid int plate counts
        plates_needed = sum(result["plates"] for result in course_layout if isinstance(result["plates"], int))
        total_waste = (plates_needed * plate_area) - area_needed

        options.append((plates_needed, (w, l), total_waste))

    # Prioritize fewest plates, then least waste
    options.sort(key=lambda x: (x[0], x[2]))
    return options[0] if options else None

    
    #Calculate courses and breaks
def calculate_courses_and_breaks(diameter, angle_deg, moc):
    total_slant = calculate_slant_height(diameter, angle_deg)
    angle_rad = math.radians(angle_deg)

    plate_widths = [48, 60] if moc == "Stainless Steel" else [96, 120]

    best_config = None
    for width in plate_widths:
        num_courses = math.ceil(total_slant / width)
        course_slant = total_slant / num_courses

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
            "Used Plate Width": width  # for reference/debug
        }

        if best_config is None or config["Number of Courses"] < best_config["Number of Courses"]:
            best_config = config

    return best_config


# 🔧 Arc Nesting Function
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

            # Segment bounding box
            arc_outer = r_outer * theta
            arc_inner = r_inner * theta
            segment_width = max(arc_outer, arc_inner)
            segment_height = r_outer - r_inner

            # Skip if too tall
            if segment_height > plate_width:
                continue

            segments_fit = math.floor(plate_length / segment_width)
            if segments_fit == 0:
                continue

            plates_needed = math.ceil(segments / segments_fit)
            waste = (plates_needed * plate_width * plate_length) - (segments * segment_width * segment_height)

            if best_option is None or plates_needed < best_option["plates"] or (
                plates_needed == best_option["plates"] and waste < best_option["waste"]
            ):
                best_option = {
                    "course": i + 1,
                    "segments": segments,
                    "fit": segments_fit,
                    "plates": plates_needed,
                    "waste": round(waste, 2)
                }

        if best_option:
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

# 🧠 Main button logic
    if st.button("Calculate Cone Layout"):
    # 1. Inputs and geometry
        slant_height = calculate_slant_height(diameter, angle)
        course_info = calculate_courses_and_breaks(diameter, angle, moc)
        cone_area = calculate_cone_area(diameter, angle)
        plate_options = get_plate_options(moc)

    # 2. Optimize plate usage using real segment geometry
        best = optimize_plate_usage(cone_area, plate_options, course_info)

    if best:
        plates_needed, (plate_width, plate_length), waste = best

        # 3. Estimate actual usage per course using modeled segments
        course_layout = estimate_plate_usage_per_course(course_info, plate_width, plate_length)


        # 4. Output summary
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
                    f"**{result['plates']} plate(s)**, Estimated Waste: {result['waste']} in²"
                )

       


        # 5. Summary line for Chris
        total_plates = sum(result["plates"] for result in course_layout if isinstance(result["plates"], int))
        st.markdown(f"**Summary → Total Plates Needed: {total_plates} using {plate_width}\" x {plate_length}\" plates**")

        # 6. Display course-level geometry
        st.subheader("🧱 Cone Course Layout")
        st.write(f"**Total Slant Height**: {course_info['Total Slant Height']} inches")
        st.write(f"**Number of Courses**: {course_info['Number of Courses']}")
        st.write(f"**Course Slant Height**: {course_info['Course Slant Height']} inches")
        st.write("**Break Diameters (top → bottom)**:")
        st.write(course_info["Break Diameters (Top → Bottom)"])
            else:
                st.error("❌ No viable plate layout found. Try reducing number of segments or using a different material.")

