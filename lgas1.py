import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Page Config
st.set_page_config(page_title="Leo Gas Cylinder Management", layout="wide")

# ────────────────────────────────────────────────
# Load and clean the data from Google Sheets
# ────────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)  # Data refreshes every minute
def load_live_data():
    # It automatically looks for the URL in your Secrets
    df = conn.read()
    
    # Fix formatting
    df["Location_PIN"] = df["Location_PIN"].astype(str).str.replace(".0", "", regex=False).str.strip()
    
    # Date conversions
    for col in ["Last_Fill_Date", "Last_Test_Date", "Next_Test_Due"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Re-calculate Overdue status based on current live date
    if "Next_Test_Due" in df.columns:
        df["Overdue"] = df["Next_Test_Due"] < pd.Timestamp.now()
        
    return df

df = load_live_data()

# ────────────────────────────────────────────────
# Sidebar navigation
# ────────────────────────────────────────────────
st.sidebar.title("Cylinder Management")
page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Cylinder Finder", "Simulate Refill", "Add New Cylinder", "Safety Info"]
)

# ────────────────────────────────────────────────
# Page: Dashboard
# ────────────────────────────────────────────────
if page == "Dashboard":
    st.title("Live Tracking Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cylinders", len(df))
    col2.metric("Overdue", df["Overdue"].sum())
    col3.metric("Avg Fill", f"{df['Fill_Percent'].mean():.1f}%")

    st.dataframe(df.sort_values("Next_Test_Due"), use_container_width=True)

# ────────────────────────────────────────────────
# Page: Simulate Refill (The "SAVE" part)
# ────────────────────────────────────────────────
elif page == "Simulate Refill":
    st.title("Update Cylinder Refill")
    cylinder_id = st.selectbox("Select Cylinder", options=df["Cylinder_ID"].unique())
    
    new_fill = st.slider("New Fill %", 0, 100, 100)
    
    if st.button("Save to Google Sheets"):
        # Update local dataframe
        df.loc[df["Cylinder_ID"] == cylinder_id, "Fill_Percent"] = new_fill
        df.loc[df["Cylinder_ID"] == cylinder_id, "Last_Fill_Date"] = pd.Timestamp.now()
        
        # PUSH TO CLOUD
        conn.update(data=df)
        st.cache_data.clear() # Force app to pull fresh data
        st.success(f"Cylinder {cylinder_id} updated successfully!")

# ────────────────────────────────────────────────
# Page: Add New Cylinder
# ────────────────────────────────────────────────
elif page == "Add New Cylinder":
    st.title("Register New Cylinder")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        new_id = c1.text_input("Cylinder ID")
        cap = c1.selectbox("Capacity", [14, 19, 35, 47])
        pin = c2.text_input("PIN Code")
        name = c2.text_input("Customer Name")
        
        if st.form_submit_button("Add & Save"):
            if new_id and pin:
                # Create new row
                new_row = pd.DataFrame([{
                    "Cylinder_ID": new_id,
                    "Capacity_kg": cap,
                    "Fill_Percent": 100,
                    "Last_Fill_Date": pd.Timestamp.now(),
                    "Location_PIN": pin,
                    "Customer_Name": name,
                    "Status": "Active",
                    "Last_Test_Date": pd.Timestamp.now(),
                    "Next_Test_Due": pd.Timestamp.now() + pd.Timedelta(days=1825)
                }])
                
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.cache_data.clear()
                st.success("New cylinder added to Google Sheets!")
            else:
                st.error("Please fill required fields.")

elif page == "Cylinder Finder":
    # PIN search logic from your previous code
    pin_input = st.text_input("Enter 6-Digit PIN")
    if pin_input:
        results = df[df["Location_PIN"] == pin_input]
        st.table(results)

elif page == "Safety Info":
    st.info("Emergency Helpline: 1906")
    st.write("- Keep cylinders upright.\n- Check for leaks with soapy water.")
