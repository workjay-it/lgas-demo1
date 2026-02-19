import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection  # <--- Essential for Live Updates

# ────────────────────────────────────────────────
# 1. LIVE DATABASE CONNECTION
# ────────────────────────────────────────────────
# Ensure .streamlit/secrets.toml contains your spreadsheet URL
conn = st.connection("gsheets", type=GSheetsConnection)

def load_live_data():
    # ttl=0 ensures we fetch the latest data every time the app refreshes
    df = conn.read(ttl=0)
    
    # Cleaning Logic
    df["Location_PIN"] = df["Location_PIN"].astype(str).str.strip()
    for col in ["Last_Fill_Date", "Last_Test_Date", "Next_Test_Due"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

df = load_live_data()

# ────────────────────────────────────────────────
# 2. NAVIGATION
# ────────────────────────────────────────────────
st.sidebar.title("LeoGas Management 2026")
page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Cylinder Finder", "Simulate Refill", "Add New Cylinder", "Return & Penalty Log"]
)

# ... [Dashboard & Finder pages stay similar to your current code] ...

# ────────────────────────────────────────────────
# 3. NEW: RETURN & PENALTY LOG (Liability Tracking)
# ────────────────────────────────────────────────
if page == "Return & Penalty Log":
    st.title("Cylinder Return Portal")
    st.write("Scan or select a cylinder to calculate penalties and log issues.")

    # Dropdown for existing cylinders
    return_id = st.selectbox("Select Cylinder ID", options=sorted(df["Cylinder_ID"].unique()))
    
    if return_id:
        # Get specific cylinder row
        cyl_data = df[df["Cylinder_ID"] == return_id].iloc[0]
        st.info(f"Customer: {cyl_data['Customer_Name']} | Last Test: {cyl_data['Last_Test_Date'].date()}")

        with st.form("return_form"):
            condition = st.selectbox("Physical Condition", ["Good", "Dented", "Valve Leaking", "Rusting"])
            seal_intact = st.checkbox("Seal Intact?", value=True)
            
            # --- AUTOMATIC PENALTY CALCULATION ---
            base_fine = 0
            if condition != "Good":
                base_fine += 500  # Damage penalty
            if cyl_data["Overdue"]:
                base_fine += 1000 # Safety violation penalty (overdue test)
            
            st.warning(f"Calculated Liability: ₹{base_fine}")
            
            if st.form_submit_button("Confirm Return & Update Cloud"):
                # Update the DataFrame
                df.loc[df["Cylinder_ID"] == return_id, "Status"] = "Empty" if condition == "Good" else "Damaged"
                df.loc[df["Cylinder_ID"] == return_id, "Fill_Percent"] = 0
                
                # Push the update back to the Google Sheet
                conn.update(data=df)
                
                st.success(f"Return logged for {return_id}. Live database updated!")
                st.balloons()

# ────────────────────────────────────────────────
# 4. UPDATED: ADD NEW CYLINDER (Direct to Sheet)
# ────────────────────────────────────────────────
elif page == "Add New Cylinder":
    st.title("Register New Stock")
    with st.form("new_entry"):
        new_id = st.text_input("New Cylinder ID")
        cap = st.selectbox("Capacity", [12, 17, 19, 33])
        cust = st.text_input("Customer Name")
        
        if st.form_submit_button("Add Directly to System"):
            # Prepare new row dictionary
            new_row = {
                "Cylinder_ID": new_id,
                "Capacity_kg": cap,
                "Fill_Percent": 100,
                "Status": "Full",
                "Customer_Name": cust,
                "Next_Test_Due": (datetime.now() + pd.Timedelta(days=1825)).strftime("%Y-%m-%d"),
                "Overdue": False
            }
            # Append and Update
            updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Cylinder added to cloud!")
