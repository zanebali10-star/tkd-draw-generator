import math
import io
import streamlit as st
import pandas as pd
from fpdf import FPDF

# ---------------------------------------
# BASIC STREAMLIT SETUP
# ---------------------------------------
st.set_page_config(page_title="Bracket Generator", layout="centered")
st.title("🥋 TKD Bracket Generator (Printable A4 Sheets)")

st.write("Upload your Excel file. Each sheet will produce ONE printable coloured bracket.")

# ---------------------------------------
# FILE UPLOAD
# ---------------------------------------
uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded:
    excel = pd.ExcelFile(uploaded)
    sheets = excel.sheet_names
    st.success(f"Loaded file with sheets: {', '.join(sheets)}")

    # -----------------------------------
    # PROCESS EACH SHEET INTO A PDF
    # -----------------------------------
    for sheet in sheets:
        st.header(sheet)

        try:
            df = pd.read_excel(uploaded, sheet_name=sheet)
            df.columns = [str(c).strip().lower() for c in df.columns]

            # Expecting at least: name, club
            if "name" not in df or "club" not in df:
                st.error(f"Sheet '{sheet}' is missing required columns.")
                continue

            names = df["name"].tolist()
            clubs = df["club"].tolist()
            n = len(names)

            # Make bracket size nearest power of 2
            bracket_size = 1
            while bracket_size < n:
                bracket_size *= 2

            # Pad empty slots
            names += ["BYE"] * (bracket_size - n)
            clubs += [""] * (bracket_size - n)

            # -----------------------------------
            # CREATE PDF
            # -----------------------------------
            pdf = FPDF(orientation="P", unit="mm", format="A4")
            pdf.add_page()
            pdf.set_auto_page_break(False)

            pdf.set_font("Helvetica", "B", 22)
            pdf.cell(0, 15, sheet, 0, 1, "C")

            pdf.ln(5)

            # Colours matching your screenshot
            PINK = (255, 182, 193)
            BLUE = (173, 216, 230)
            YELLOW = (255, 204, 0)

            # Cell sizes
            cell_h = 12
            cell_w = 80

            y_start = 40
            y_gap = cell_h + 6

            # -----------------------------------
            # DRAW ROUND 1 BOXES
            # -----------------------------------
            pdf.set_font("Helvetica", size=14)

            for i in range(bracket_size):
                y = y_start + i * y_gap

                # Colour band
                pdf.set_fill_color(*PINK if i % 2 == 0 else BLUE)
                pdf.rect(20, y, cell_w, cell_h, "F")

                # Name
                pdf.set_xy(20, y + 3)
                txt = names[i]
                if names[i] != "BYE":
                    txt += f"  ({clubs[i]})"
                pdf.cell(cell_w, 5, txt)

            # -----------------------------------
            # SAVE PDF
            # -----------------------------------
            output = pdf.output(dest="S").encode("latin1")
            data = io.BytesIO(output)

            st.download_button(
                label=f"⬇️ Download bracket for {sheet}",
                data=data,
                file_name=f"{sheet.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Error generating bracket for '{sheet}': {e}")
