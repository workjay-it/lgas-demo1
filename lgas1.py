import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# Page Configuration
st.set_page_config(page_title="Leo Gas Cylinder Management", layout="wide")

# ────────────────────────────────────────────────
# 1. Initialize Supabase Connection
# ────────────────────────────────────────────────
# This automatically reads 'url' and 'key' from your Streamlit Secrets
conn = st.connection("supabase", type=SupabaseConnection)

@st.cache_data(ttl=600)  # Cache results for 10 minutes
def load_live_data():
    # Fetch all records from your Supabase table named 'cylinders'
    response = conn.table("cylinders").select("*").execute()
    df = pd.DataFrame(response.data)
    
    if not df.empty:
        # Data Cleaning: Fix PIN codes and convert dates
        df["Location_PIN"] = df["Location_PIN"].astype(str).str.replace(".0", "", regex=False).str.strip()
        for col in ["Last_Fill_Date", "Last_Test_Date", "Next_Test_Due"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Calculate Overdue status
        if "Next_Test_Due" in df.columns:
            df["Overdue"] = df["Next_Test_Due"] < pd.Timestamp.now()
    return df

df = load_live_data()

# ────────────────────────────────────────────────
# 2. Sidebar Navigation
# ────────────────────────────────────────────────
st.sidebar.title("Cylinder Management")
page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Cylinder Finder", "Simulate Refill", "Add New Cylinder", "Safety Info"]
)

# ────────────────────────────────────────────────
# 3. App Pages
# ────────────────────────────────────────────────

if page == "Dashboard":
    st.title("Live Tracking Dashboard")
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cylinders", len(df))
        col2.metric("Overdue", df["Overdue"].sum())
        col3.metric("Avg Fill", f"{df['Fill_Percent'].mean():.1f}%")
        st.dataframe(df.sort_values("Next_Test_Due"), use_container_width=True)
    else:
        st.warning("No data found in Supabase. Please add or import cylinders.")

elif page == "Cylinder Finder":
    st.title("Find Cylinder by PIN")
    pin_input = st.text_input("Enter 6-Digit PIN")
    if pin_input:
        results = df[df["Location_PIN"] == pin_input]
        st.table(results)

elif page == "Simulate Refill":
    st.title("Update Cylinder Refill")
    cylinder_id = st.selectbox("Select Cylinder", options=df["Cylinder_ID"].unique())
    new_fill = st.slider("New Fill %", 0, 100, 100)
    
    if st.button("Save Refill to Supabase"):
        # UPDATE record in Supabase
        conn.table("cylinders").update({
            "Fill_Percent": new_fill,
            "Last_Fill_Date": datetime.now().strftime("%Y-%m-%d")
        }).eq("Cylinder_ID", cylinder_id).execute()
        
        st.cache_data.clear()  # Clear cache to reflect changes
        st.success(f"Cylinder {cylinder_id} updated successfully!")

elif page == "Add New Cylinder":
    st.title("Register New Cylinder")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        new_id = c1.text_input("Cylinder ID (e.g., LEO-101)")
        cap = c1.selectbox("Capacity", [14, 19, 35, 47])
        pin = c2.text_input("PIN Code")
        name = c2.text_input("Customer Name")
        
        if st.form_submit_button("Add & Save"):
            if new_id and pin:
                # INSERT new record into Supabase
                next_test = datetime.now() + pd.Timedelta(days=1825)
                new_data = {
                    "Cylinder_ID": new_id,
                    "Capacity_kg": cap,
                    "Fill_Percent": 100,
                    "Last_Fill_Date": datetime.now().strftime("%Y-%m-%d"),
                    "Location_PIN": pin,
                    "Customer_Name": name,
                    "Status": "Active",
                    "Last_Test_Date": datetime.now().strftime("%Y-%m-%d"),
                    "Next_Test_Due": next_test.strftime("%Y-%m-%d")
                }
                
                conn.table("cylinders").insert(new_data).execute()
                st.cache_data.clear()
                st.success(f"New cylinder {new_id} added permanently!")
            else:
                st.error("Please fill required fields.")

elif page == "Safety Info":
    st.info("Emergency Helpline: 1906")
    st.write("- Keep cylinders upright.\n- Check for leaks with soapy water.")
