import math
import io
import streamlit as st
import pandas as pd
from fpdf import FPDF

st.set_page_config(page_title="Bracket Generator", layout="centered")
st.title("🥋 TKD Bracket Generator (Printable A4 Sheets)")

st.write("Upload your Excel file. Each sheet will produce ONE printable coloured bracket.")

uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded:
    excel = pd.ExcelFile(uploaded)
    sheets = excel.sheet_names
    st.success(f"Loaded file with sheets: {', '.join(sheets)}")

    for sheet in sheets:
        st.header(sheet)

        try:
            df = pd.read_excel(uploaded, sheet_name=sheet)
            df.columns = [str(c).strip().lower() for c in df.columns]

            # FIX: Accept both "team" and "club"
            if "club" in df.columns:
                club_col = "club"
            elif "team" in df.columns:
                club_col = "team"
            else:
                st.error(f"Sheet '{sheet}' must contain a column named 'team' or 'club'.")
                continue

            if "name" not in df.columns:
                st.error(f"Sheet '{sheet}' needs a 'name' column.")
                continue

            names = df["name"].tolist()
            clubs = df[club_col].tolist()
            n = len(names)

            # Determine bracket size
            bracket_size = 1
            while bracket_size < n:
                bracket_size *= 2

            # Pad with BYEs
            names += ["BYE"] * (bracket_size - n)
            clubs += [""] * (bracket_size - n)

            # Build PDF
            pdf = FPDF("P", "mm", "A4")
            pdf.add_page()
            pdf.set_auto_page_break(False)

            pdf.set_font("Helvetica", "B", 22)
            pdf.cell(0, 15, sheet, 0, 1, "C")
            pdf.ln(5)

            # Colours
            PINK = (255, 182, 193)
            BLUE = (173, 216, 230)

            cell_h = 12
            cell_w = 80
            y_start = 40
            y_gap = cell_h + 6

            pdf.set_font("Helvetica", size=14)

            # Round 1 boxes only (simple printable form)
            for i in range(bracket_size):
                y = y_start + i * y_gap
                color = PINK if i % 2 == 0 else BLUE

                pdf.set_fill_color(*color)
                pdf.rect(20, y, cell_w, cell_h, "F")

                pdf.set_xy(20, y + 3)
                label = names[i]
                if names[i] != "BYE":
                    label += f"  ({clubs[i]})"

                pdf.cell(cell_w, 5, label)

            # Export PDF
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
