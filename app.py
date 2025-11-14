import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

# -------------------------------
# STREAMLIT SETUP
# -------------------------------
st.set_page_config(page_title="TKD Bracket Generator", layout="centered")
st.title("🥋 TKD Bracket Generator (A4 Printable)")

st.write("Upload your Excel file. Each sheet will produce one printable bracket.")

uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded:
    excel = pd.ExcelFile(uploaded)
    sheets = excel.sheet_names
    st.success(f"Loaded sheets: {', '.join(sheets)}")

    for sheet in sheets:
        st.header(f"Bracket: {sheet}")

        try:
            df = pd.read_excel(uploaded, sheet_name=sheet)
            df.columns = [str(c).strip().lower() for c in df.columns]

            # REQUIRED COLUMNS
            required_cols = ["team", "name", "gender", "weight", "class", "draw_position"]
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")

            # Convert to strings + clean
            df = df.astype({
                "team": str,
                "name": str,
                "gender": str,
                "weight": str,
                "class": str,
                "draw_position": str
            })

            # -----------------------------------
            # ORDER COMPETITORS USING draw_position
            # -----------------------------------
            df["draw_position_num"] = pd.to_numeric(df["draw_position"], errors="coerce")
            df = df.sort_values("draw_position_num")

            names = df["name"].tolist()
            teams = df["team"].tolist()
            genders = df["gender"].tolist()
            weight_divs = df["weight"].tolist()     # e.g. "-24"
            classes = df["class"].tolist()
            n = len(names)

            # -----------------------------------
            # BUILD TITLE COMPONENTS
            # Using only: Gender + Weight Division + Class
            # -----------------------------------
            # Assume all rows in the sheet share the same:
            # gender, weight division, class
            def expand_gender(g):
                g = g.strip().upper()
                return "Female" if g == "F" else "Male"

            title_gender = expand_gender(genders[0])
            title_weight = weight_divs[0].replace("kg", "").strip()
            if not title_weight.endswith("kg"):
                title_weight = f"{title_weight}kg"

            # Class: from last field, e.g. "A" or "B"
            class_raw = classes[0].strip().split()[-1]
            title_class = class_raw.upper()

            title_text = f"{title_gender} ({title_weight}) – {title_class} Class"

            # -----------------------------------
            # BRACKET SIZE: nearest power of 2
            # -----------------------------------
            size = 1
            while size < n:
                size *= 2

            # pad to bracket size
            names += ["BYE"] * (size - n)
            teams += [""] * (size - n)
            classes += [""] * (size - n)

            # -----------------------------------
            # CREATE PDF
            # -----------------------------------
            pdf = FPDF("P", "mm", "A4")
            pdf.add_page()
            pdf.set_auto_page_break(False)

            # TITLE
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, title_text, 0, 1, "C")
            pdf.ln(4)

            # COLOURS (RGB)
            PINK = (255, 182, 193)
            BLUE = (173, 216, 230)
            YELLOW = (255, 204, 0)

            # SETTINGS
            cell_h = 12
            cell_w = 85
            y_start = 40
            y_gap = cell_h + 6

            pdf.set_font("Helvetica", size=14)

            # -----------------------------------
            # DRAW FIRST ROUND BOXES (PINK/BLUE)
            # -----------------------------------
            for i in range(size):
                y = y_start + i * y_gap
                colour = PINK if i % 2 == 0 else BLUE

                # coloured rectangle
                pdf.set_fill_color(*colour)
                pdf.rect(20, y, cell_w, cell_h, "F")

                # text
                pdf.set_xy(20, y + 3)
                if names[i] == "BYE":
                    pdf.cell(cell_w, 5, "BYE")
                else:
                    txt = f"{names[i]}  ({teams[i]})"
                    pdf.cell(cell_w, 5, txt)

            # -----------------------------------
            # YELLOW WINNER CONNECTOR BAR
            # -----------------------------------
            mid_y = y_start + (size * y_gap) / 2 - 10
            pdf.set_fill_color(*YELLOW)
            pdf.rect(120, mid_y, 50, 20, "F")

            pdf.set_xy(120, mid_y + 6)
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(50, 8, "WINNER", 0, 1, "C")

            # -----------------------------------
            # EXPORT PDF
            # -----------------------------------
            pdf_bytes = pdf.output(dest="S").encode("latin1")
            data = io.BytesIO(pdf_bytes)

            st.download_button(
                label=f"⬇️ Download {sheet} bracket",
                data=data,
                file_name=f"{sheet.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Error in sheet '{sheet}': {e}")
