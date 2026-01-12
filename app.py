import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io

# ==========================================
# 1. CONFIGURATION
# ==========================================
# This must match the exact header name you typed in Excel
PASSWORD_COL_NAME = 'Password' 

# ==========================================
# 2. PDF GENERATION ENGINE
# ==========================================
def generate_pdf(row):
    """Creates a PDF file in memory for a specific rider."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # --- Helper to safely get text ---
    def get_txt(col_name):
        return str(row.get(col_name, '')).replace('nan', '')

    # --- Helper to safely get numbers ---
    def get_num(col_name):
        try:
            val = row.get(col_name, 0)
            return float(val) if pd.notna(val) else 0.0
        except:
            return 0.0

    # --- Header Information ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1 * inch, 10.5 * inch, "SALARY SLIP")
    
    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, 10 * inch, f"City: {get_txt('City')}")
    c.drawString(4.5 * inch, 10 * inch, f"Rider ID: {get_txt('Rider ID')}")
    
    c.drawString(1 * inch, 9.75 * inch, f"Name: {get_txt('Rider Name')}")
    c.drawString(4.5 * inch, 9.75 * inch, f"Bike No: {get_txt('Nov-25 Bike')}")
    
    c.drawString(1 * inch, 9.5 * inch, "Period: Nov-2025") # Update this manually every month if needed
    c.drawString(4.5 * inch, 9.5 * inch, "Aggregator: Talabat")
    
    c.line(0.5 * inch, 9.2 * inch, 7.5 * inch, 9.2 * inch)

    # --- Table Setup ---
    y = 8.8 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y, "EARNINGS")
    c.drawString(4.5 * inch, y, "DEDUCTIONS")
    y -= 0.3 * inch
    c.setFont("Helvetica", 10)

    # --- Mapping Data ---
    # Format: ("Label on PDF", "Exact Column Name in Excel")
    earnings = [
        ("Pickups Payment", "Rider Pickup Payment"),
        ("Dropoffs Payment", "Rider Dropoff Payment"),
        ("TDS Bonus", "TDS Bonus"),
        ("Arrears", "Arears"),
        ("Returns (LC)", "Deliveries - Return (LC)")
    ]

    deductions = [
        ("COD Deficit", "COD Deficit"),
        ("Clawback", "Clawback Deduction"),
        ("Salik", "Salik"),
        ("Low Perf (LP)", "LP"),
        ("Extra Sim", "Extra Sim"),
        ("Traffic Fines", "Fine"),
        ("Bike Repair", "Bike Repair"),
        ("Visa/Loan", "Visa"),
        ("Insurance", "Insurance"),
        ("Advance", "Advance"),
        ("C3 Charges", "C3 Charges"),
        ("Prev. Minus", "Oct Minus salaries"),
        ("Other", "Others"),
        ("RTA", "RTA")
    ]

    # Print Earnings
    start_y = y
    for label, col in earnings:
        amount = get_num(col)
        if amount != 0:
            c.drawString(1 * inch, y, label)
            c.drawRightString(3.5 * inch, y, f"{amount:,.2f}")
            y -= 0.2 * inch

    # Print Deductions
    d_y = start_y
    for label, col in deductions:
        amount = get_num(col)
        if amount != 0:
            c.drawString(4.5 * inch, d_y, label)
            c.drawRightString(7.5 * inch, d_y, f"{amount:,.2f}")
            d_y -= 0.2 * inch

    # --- Totals ---
    # We find the lowest point used by either column to draw the line
    final_y = min(y, d_y) - 0.5 * inch
    c.line(0.5 * inch, final_y + 0.15 * inch, 7.5 * inch, final_y + 0.15 * inch)
    
    gross = get_num('Gross salary') # Adjusted logic for whitespace below
    total_ded = get_num("Total Deduction'") # Handling the quote in your header
    net = get_num('Net Riders Salaries')

    c.setFont("Helvetica-Bold", 10)
    c.drawString(1 * inch, final_y, "Total Earnings")
    c.drawRightString(3.5 * inch, final_y, f"{gross:,.2f}")
    
    c.drawString(4.5 * inch, final_y, "Total Deductions")
    c.drawRightString(7.5 * inch, final_y, f"{total_ded:,.2f}")
    
    final_y -= 0.4 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * inch, final_y, "NET SALARY PAYABLE:")
    c.drawString(5.5 * inch, final_y, f"AED {net:,.2f}")

    c.save()
    buffer.seek(0)
    return buffer

# ==========================================
# 3. WEB APP INTERFACE
# ==========================================
st.set_page_config(page_title="Rider Salary Portal", layout="centered")

st.title("📦 Rider Salary Portal")
st.markdown("Enter your Rider ID and Password to download your slip.")

# --- Admin Section (Hidden in Sidebar) ---
with st.sidebar:
    st.header("Admin Panel")
    uploaded_file = st.file_uploader("Upload Salary CSV", type=['csv'])

# --- Main Logic ---
if uploaded_file is not None:
    try:
        # Read CSV. Header is on Row 5 (index 4) based on your file structure
        df = pd.read_csv(uploaded_file, header=4)
        
        # Clean Header Names (Remove spaces)
        df.columns = df.columns.str.strip()
        
        # Ensure IDs are strings
        df['Rider ID'] = df['Rider ID'].astype(str).str.replace('.0', '')
        
        # Check if Password column exists
        if PASSWORD_COL_NAME not in df.columns:
            st.error(f"❌ Error: Your CSV is missing the '{PASSWORD_COL_NAME}' column.")
        else:
            df[PASSWORD_COL_NAME] = df[PASSWORD_COL_NAME].astype(str).str.replace('.0', '')

            # --- Login Form ---
            with st.form("login_form"):
                col1, col2 = st.columns(2)
                uid = col1.text_input("Rider ID")
                pwd = col2.text_input("Password", type="password")
                submitted = st.form_submit_button("Search")

            if submitted:
                # Find the rider
                user = df[(df['Rider ID'] == uid) & (df[PASSWORD_COL_NAME] == pwd)]
                
                if not user.empty:
                    # Rider Found
                    rider_data = user.iloc[0]
                    st.success(f"Hello, {rider_data['Rider Name']}!")
                    
                    # Generate PDF
                    pdf_data = generate_pdf(rider_data)
                    
                    # Show Download Button
                    st.download_button(
                        label="📄 Download Salary Slip (PDF)",
                        data=pdf_data,
                        file_name=f"Salary_{uid}.pdf",
                        mime="application/pdf"
                    )
                else:
                    if uid or pwd:
                        st.error("❌ Invalid ID or Password.")

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("System is offline. Waiting for Admin to upload data.")