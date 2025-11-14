import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os

# --- Page setup ---
st.set_page_config(page_title="TKD Draw Generator", layout="centered")
st.title("🥋 TKD Draw Generator")
st.write("Upload your Excel file with competitor data to generate draws.")

# --- File upload ---
uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Read Excel
        df = pd.read_excel(uploaded_file)

        # --- Normalize column names ---
        df.columns = [str(col).strip().lower() for col in df.columns]
        st.write("Detected columns:", df.columns.to_list())

        # --- Map column variations ---
        column_map = {
            'team': 'club',
            'club': 'club',
            'name': 'name',
            'category': 'category',
            'division': 'category',
            'group': 'category',
            'gender': 'gender',
            'class': 'class',
            'weight': 'weight'
        }

        normalized = {}
        for col in df.columns:
            if col in column_map:
                normalized[column_map[col]] = df[col]

        # Build standardized DataFrame
        df = pd.DataFrame(normalized)

        # --- Handle missing columns gracefully ---
        if 'category' not in df.columns:
            df['category'] = "General"
        if 'club' not in df.columns:
            df['club'] = "Unknown Club"
        if 'name' not in df.columns:
            st.error("Missing a column for competitor names.")
            st.stop()

        # --- Display cleaned DataFrame ---
        st.success("✅ File uploaded and processed successfully!")
        st.dataframe(df)

        # --- Category selection ---
        categories = df['category'].unique().tolist()
        selected_category = st.selectbox("Select a category to generate draw:", categories)

        # --- Generate PDF ---
        if st.button("Generate PDF Draw"):
            try:
                # Filter by category
                draw_df = df[df['category'] == selected_category]

                # --- Create clean paginated PDF ---
                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()

                # --- Add Unicode-compatible font (DejaVu Sans) ---
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                if not os.path.exists(font_path):
                    os.makedirs("fonts", exist_ok=True)
                    font_path = "fonts/DejaVuSans.ttf"  # fallback if you later include this font
                pdf.add_font("DejaVu", "", font_path, uni=True)
                pdf.set_font("DejaVu", size=12)

                # Title
                pdf.set_font("DejaVu", 'B', 16)
                pdf.cell(0, 10, f"Draw for Category: {selected_category}", ln=True, align='C')
                pdf.ln(8)

                # Draw entries
                pdf.set_font("DejaVu", size=12)
                line_height = pdf.font_size * 1.5
                max_lines_per_page = 25
                count = 0

                for idx, row in draw_df.iterrows():
                    if count and count % max_lines_per_page == 0:
                        pdf.add_page()
                        pdf.set_font("DejaVu", 'B', 16)
                        pdf.cell(0, 10, f"Draw for Category: {selected_category} (cont.)", ln=True, align='C')
                        pdf.ln(8)
                        pdf.set_font("DejaVu", size=12)

                    name = str(row.get('name', '')).strip()
                    club = str(row.get('club', '')).strip()
                    weight = str(row.get('weight', '')).strip()
                    belt_class = str(row.get('class', '')).strip()

                    # Use standard dash to avoid en-dash issues
                    line_text = f"{idx + 1}. {name} - {club} | {belt_class} | {weight}"

                    pdf.cell(0, line_height, txt=line_text, ln=True)
                    count += 1

                # Convert PDF to bytes
                pdf_output = io.BytesIO(pdf.output(dest="S").encode("latin1"))

                # Download button
                st.download_button(
                    label="⬇️ Download PDF Draw",
                    data=pdf_output,
                    file_name=f"{selected_category}_draw.pdf",
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Error generating draw: {e}")

    except Exception as e:
        st.error(f"Error reading file: {e}")
