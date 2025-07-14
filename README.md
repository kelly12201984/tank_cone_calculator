# Concentric Cone Material & Layout Estimator

A Streamlit-based app to help tank estimators calculate the plate layout and material needs for concentric cone bottoms on API-style tanks.

This tool estimates the number of gores per course, break diameters, and the optimal layout of flat plate segments — helping reduce manual calculation time and material waste.

---

## 🛠 Features

- **Real-world plate constraints** for Stainless and Carbon Steel
- **Automatic course splitting** if slant height exceeds available plate width
- **Gore optimization** for each course (2–12 gores, even numbers)
- **Manual override sliders** for custom control
- **Visual layout per course** (mimics how segments are nested and rotated)
- **CSV export** with optional Opportunity ID

---

## 🔢 Inputs

- **Tank Diameter** (inches)
- **Angle of Repose** (degrees)
- **Material of Construction** (Stainless or Carbon Steel)
- Optional: Opportunity ID (used for CSV filename)

---

## 🧠 How It Works

- Calculates slant height using sector geometry.
- Splits cone into multiple **horizontal courses**, each modeled as a sector of an annulus.
- Evaluates how many gores can **fit per plate** based on arc width and segment nesting.
- Picks layout with the **fewest plates and lowest waste** (based on area delta).
- Lets user manually adjust gores per course if desired.

---

## 📦 Example Output

- Total Slant Height: 55.43 inches  
- Course Slant Height: 27.72 inches  
- Break Diameters (top → bottom): [168.0, 85.3, 2.0]  
- Manual Layout Table:  
  | Course | Gores | Plate Size | Plates | Fit/Plate | Waste (in²) |
  |--------|-------|------------|--------|------------|-------------|
  | 1      | 4     | 60" x 144" | 2      | 2          | 280.12      |

---

## 🧪 Tech Stack

- **Python**
- **Streamlit**
- **pandas**
- **matplotlib**
- **math** (sector geometry)
- CSV export via `io.StringIO`

---

---

## 🙋‍♀️ Author

**Kelly Arseneau**  
Data Scientist | Real-world builder 

---

## 📝 Notes

This app was built for real-world use at a tank manufacturing company to explore ways to streamline estimation workflows. It models the layout process used by experienced estimators and provides a working prototype of a digital alternative to manual layout.
