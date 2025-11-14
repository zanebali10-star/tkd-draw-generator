import math
import io
import os
import streamlit as st
import pandas as pd
from fpdf import FPDF

# ----------------------------
# Helpers
# ----------------------------
def next_power_of_two(n: int) -> int:
    return 1 if n == 0 else 2 ** (n - 1).bit_length()

def seed_with_byes(names):
    """Return a list length power-of-two, filling end with 'BYE' if needed."""
    n = len(names)
    size = next_power_of_two(n)
    if n == size:
        return names[:]
    return names[:] + ["BYE"] * (size - n)

def rounds_for(size):
    """Number of rounds for a knockout with 'size' entrants."""
    return int(math.log2(size)) if size > 0 else 0

# ----------------------------
# PDF Bracket (A4 portrait) using fpdf2
# ----------------------------
class BracketPDF(FPDF):
    def __init__(self, title):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.title_text = title
        self.set_auto_page_break(auto=False)
        self.add_page()
        # Fonts (Unicode-safe)
        reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(reg):
            os.makedirs("fonts", exist_ok=True)
            reg = "fonts/DejaVuSans.ttf"
        if not os.path.exists(bold):
            bold = "fonts/DejaVuSans-Bold.ttf"
        self.add_font("DejaVu", "", reg, uni=True)
        self.add_font("DejaVu", "B", bold, uni=True)

    def header(self):
        self.set_font("DejaVu", "B", 18)
        self.set_text_color(0, 0, 0)
        self.cell(0, 12, self.title_text, ln=1, align="C")
        self.ln(2)

    def box(self, x, y, w, h, text, fill_rgb, bold=False, align="L", txt_pad=1.5):
        r, g, b = fill_rgb
        self.set_fill_color(r, g, b)
        self.set_draw_color(0, 0, 0)
        self.rect(x, y, w, h, style="DF")
        self.set_text_color(0, 0, 0)
        self.set_font("DejaVu", "B" if bold else "", 10)
        # Truncate long text to fit
        max_chars = int((w - 2*txt_pad) * 0.6)  # coarse fit factor
        t = str(text)
        if len(t) > max_chars:
            t = t[:max_chars-1] + "…"
        self.set_xy(x + txt_pad, y + (h/2 - 3))
        self.cell(w - 2*txt_pad, 6, t, align=align)

    def connector(self, x1, y1, x2, y2, thickness=0.6):
        self.set_draw_color(0, 0, 0)
        self.set_line_width(thickness)
        self.line(x1, y1, x2, y2)

def make_bracket_pdf(category_name, names):
    names = [str(n).strip() for n in names if str(n).strip()]
    if len(names) < 2:
        raise ValueError("Need at least 2 competitors")

    seeds = seed_with_byes(names)
    size = len(seeds)
    rcount = rounds_for(size)

    # Page & layout
    left_margin = 10
    right_margin = 10
    top_margin = 20
    bottom_margin = 10
    page_w = 210
    page_h = 297
    usable_w = page_w - left_margin - right_margin
    usable_h = page_h - top_margin - bottom_margin

    # Column layout: one column per round; final column is the champion box
    col_w = usable_w / (rcount + 1)  # rounds + final
    box_h = min(12, max(8, usable_h / (size + rcount*2)))  # height per name box
    v_gap = max(3, (usable_h - (size * box_h)) / max(1, size))  # vertical spacing for first round

    # Colors (light fills)
    color_round = [
        (160, 196, 255),  # R1 blue-ish
        (255, 198, 255),  # R2 pink-ish
        (190, 255, 190),  # R3 green-ish
        (255, 236, 179),  # R4 yellow-ish
        (220, 220, 220),  # Final grey
    ]

    pdf = BracketPDF(title=f"{category_name} — Bracket")
    y_cursor = top_margin

    # Store centers of boxes per round to draw connectors
    centers_per_round = []

    # Round 1 boxes
    r = 0
    x = left_margin
    round_centers = []
    y = top_margin
    for i in range(size):
        pdf.box(x, y, col_w * 0.9, box_h, seeds[i], color_round[min(r, len(color_round)-2)])
        # center point on right edge for connector
        cx = x + col_w * 0.9
        cy = y + box_h / 2
        round_centers.append((cx, cy))
        y += box_h + v_gap
    centers_per_round.append(round_centers)

    # Subsequent rounds
    current_count = size
    for r in range(1, rcount + 1):  # include final as a "round"
        prev = centers_per_round[-1]
        this = []
        x = left_margin + r * col_w
        # vertical spacing doubles each round
        # compute vertical position as midpoints between pairs from previous round
        for i in range(0, len(prev), 2):
            # Determine the y for the winner box (midpoint between two previous centers)
            if i + 1 < len(prev):
                (x1, y1) = prev[i]
                (x2, y2) = prev[i+1]
            else:
                (x1, y1) = prev[i]
                (x2, y2) = prev[i]  # lone entry (bye cascades)
            mid_y = (y1 + y2) / 2

            # connector from prev boxes to the vertical join
            join_x = x - (col_w * 0.25)
            pdf.connector(x1, y1, join_x, y1)
            pdf.connector(x2, y2, join_x, y2)
            # vertical join
            pdf.connector(join_x, y1, join_x, y2)
            # connector to current box
            box_x = x
            box_y = mid_y - box_h / 2
            pdf.connector(join_x, mid_y, box_x, mid_y)

            # Place current round box
            fill = color_round[min(r, len(color_round)-1)]
            label = "Winner" if r < rcount else "Champion"
            pdf.box(box_x, box_y, col_w * 0.9, box_h, label, fill, bold=(r == rcount), align="C")

            # save center point of this box for next connectors
            this.append((box_x + col_w * 0.9, box_y + box_h / 2))

        centers_per_round.append(this)

    # Footer note
    pdf.set_xy(10, page_h - 8)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Generated by TKD Bracket Generator", align="R")

    # Output as bytes
    raw = pdf.output(dest="S")
    pdf_bytes = raw if isinstance(raw, (bytes, bytearray)) else raw.encode("latin1", "ignore")
    return io.BytesIO(bytes(pdf_bytes))

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="🥋 TKD Bracket Generator", layout="centered")
st.title("🥋 TKD Bracket Generator")
st.write("Upload a single Excel file. Each worksheet will produce one **A4 portrait, coloured, single-elimination bracket** PDF for wall display.")

uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded:
    try:
        xls = pd.ExcelFile(uploaded)
        st.success(f"Loaded file with sheets: {', '.join(xls.sheet_names)}")

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            # take first non-empty column as names
            name_col = df.columns[0]
            names = df[name_col].dropna().astype(str).tolist()

            st.subheader(f"📄 {sheet}")
            if len(names) < 2:
                st.warning("Not enough competitors to create a bracket on this sheet.")
                continue

            # Build & offer PDF
            try:
                pdf_buf = make_bracket_pdf(sheet, names)
                st.download_button(
                    label=f"⬇️ Download {sheet} bracket (PDF)",
                    data=pdf_buf,
                    file_name=f"{sheet}_bracket.pdf",
                    mime="application/pdf",
                    key=f"dl-{sheet}"
                )
            except Exception as e:
                st.error(f"Error generating bracket for '{sheet}': {e}")

    except Exception as e:
        st.error(f"Error reading Excel file: {e}")
else:
    st.info("Upload your tournament Excel to generate printable brackets.")
