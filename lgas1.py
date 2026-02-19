import streamlit as st
import pandas as pd
from datetime import datetime

# ────────────────────────────────────────────────
# Load and clean the data (cached for performance)
# ────────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("random_cylinders_hyderabad.csv")
        
        # Fix for PIN code matching issues
        df["Location_PIN"] = df["Location_PIN"].astype(str).str.strip()
        
        # Convert date columns safely
        for col in ["Last_Fill_Date", "Last_Test_Date", "Next_Test_Due"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error("CSV file not found in the repository root. Please upload 'random_cylinders_hyderabad.csv' to your GitHub repo.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# ────────────────────────────────────────────────
# Sidebar navigation
# ────────────────────────────────────────────────
st.sidebar.title("Cylinder Management App")
st.sidebar.markdown("Inspired by Leo Gas services")
page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Cylinder Finder", "Safety Information", "Simulate Refill", "Add New Cylinder"]
)

# ────────────────────────────────────────────────
# Main pages
# ────────────────────────────────────────────────
if page == "Dashboard":
    st.title("Cylinder Tracking Dashboard")
    st.write(f"Currently showing **{len(df)}** cylinders across Hyderabad areas.")

    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=sorted(df["Status"].unique()),
            default=df["Status"].unique()
        )
    with col2:
        overdue_only = st.checkbox("Show Overdue Cylinders Only", value=False)

    filtered_df = df[df["Status"].isin(status_filter)]
    if overdue_only:
        filtered_df = filtered_df[filtered_df["Overdue"] == True]

    st.dataframe(
        filtered_df.sort_values("Next_Test_Due"),
        use_container_width=True,
        column_config={
            "Next_Test_Due": st.column_config.DateColumn("Next Test Due"),
            "Overdue": st.column_config.CheckboxColumn("Overdue")
        }
    )

    st.subheader("Quick Summary")
    colA, colB, colC = st.columns(3)
    colA.metric("Total Shown", len(filtered_df))
    colB.metric("Overdue", filtered_df["Overdue"].sum())
    colC.metric("Avg Fill Level", f"{filtered_df['Fill_Percent'].mean():.1f}%")

elif page == "Cylinder Finder":
    st.title("Cylinder Finder – PIN & Status")

    col_pin, col_status = st.columns([2, 3])

    with col_pin:
        pin_input = st.text_input("PIN Code", placeholder="500033", max_chars=6).strip()

    with col_status:
        selected_statuses = st.multiselect(
            "Show only these statuses",
            options=sorted(df["Status"].unique()),
            default=[],
            help="Leave empty to show all statuses"
        )

    if pin_input:
        if len(pin_input) == 6 and pin_input.isdigit():
            results = df[df["Location_PIN"] == pin_input]

            if selected_statuses:
                results = results[results["Status"].isin(selected_statuses)]

            if not results.empty:
                st.success(f"**{len(results)}** cylinders found in {pin_input}")

                overdue_in_area = results["Overdue"].sum()
                percent = (overdue_in_area / len(results) * 100) if len(results) > 0 else 0
                st.caption(f"Overdue in this area: **{overdue_in_area}** ({percent:.0f}%)")

                st.dataframe(
                    results.sort_values("Next_Test_Due"),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No cylinders match your PIN and status filters.")
        else:
            st.warning("Enter a valid 6-digit PIN.")

elif page == "Safety Information":
    st.title("LPG Safety & Best Practices")
    st.markdown("""
    ### Important Safety Tips
    - Always store cylinders in an upright position in a well-ventilated area
    - Check for leaks using soapy water (never use flame)
    - Install in well-ventilated spaces away from ignition sources
    - Replace cylinders showing rust, dents or damaged valves
    - In case of gas leak: ventilate area, do not switch on/off electrical appliances, evacuate & call emergency services

    **Emergency Contact (India)**: 1906 (Petroleum & Explosives Safety Organisation helpline)
    """)

    with st.expander("When to get cylinder tested"):
        st.write("Domestic LPG cylinders must undergo **hydrostatic testing every 5 years** as per Gas Cylinder Rules.")

elif page == "Simulate Refill":
    st.title("Simulate Cylinder Refill")
    if not df.empty:
        cylinder_id = st.selectbox("Select Cylinder ID", options=sorted(df["Cylinder_ID"].unique()))
        
        current_fill = df.loc[df["Cylinder_ID"] == cylinder_id, "Fill_Percent"].values[0]
        st.info(f"Current fill level: **{current_fill}%**")

        new_fill = st.slider("New Fill Percentage after Refill", 0, 100, 100)
        
        if st.button("Confirm Refill"):
            df.loc[df["Cylinder_ID"] == cylinder_id, "Fill_Percent"] = new_fill
            df.loc[df["Cylinder_ID"] == cylinder_id, "Last_Fill_Date"] = pd.Timestamp.now()
            
            try:
                df.to_csv("random_cylinders_hyderabad.csv", index=False)
                st.success(f"Refilled {cylinder_id} to {new_fill}%! (saved locally)")
            except:
                st.warning("Refill recorded in memory only (Streamlit Cloud is read-only). Download updated data manually if needed.")
    else:
        st.warning("No cylinders loaded. Please check your CSV file.")

elif page == "Add New Cylinder":
    st.title("Add New Cylinder")
    st.write("Enter details for a new cylinder. You can download the updated file afterwards.")

    with st.form("new_cylinder_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_id = st.text_input("Cylinder ID", placeholder="LEO-12345678", help="Must be unique")
            capacity = st.selectbox("Capacity (kg)", [12, 17, 19, 21, 33])
            fill_percent = st.slider("Current Fill %", 0, 100, 80)
            status = st.selectbox("Status", sorted(df["Status"].unique()))

        with col2:
            pin_code = st.text_input("Location PIN Code", placeholder="500033", max_chars=6)
            customer_name = st.text_input("Customer Name", placeholder="Sivajyothi J")
            last_fill = st.date_input("Last Fill Date", value=datetime.today().date())
            last_test = st.date_input("Last Test Date", value=(datetime.today() - pd.Timedelta(days=365*3)).date())

        submitted = st.form_submit_button("Add Cylinder & Download Updated CSV")

    if submitted:
        if not new_id or not pin_code or len(pin_code) != 6 or not pin_code.isdigit():
            st.error("Please fill Cylinder ID and a valid 6-digit PIN Code.")
        elif new_id in df["Cylinder_ID"].values:
            st.error("This Cylinder ID already exists. Please use a unique ID.")
        else:
            # Prepare new row
            next_test = pd.Timestamp(last_test) + pd.Timedelta(days=1827)  # ~5 years
            new_row = {
                "Cylinder_ID": new_id,
                "Capacity_kg": capacity,
                "Fill_Percent": fill_percent,
                "Last_Fill_Date": pd.Timestamp(last_fill).strftime("%Y-%m-%d"),
                "Last_Test_Date": pd.Timestamp(last_test).strftime("%Y-%m-%d"),
                "Status": status,
                "Location_PIN": pin_code,
                "Customer_Name": customer_name,
                "Next_Test_Due": next_test.strftime("%Y-%m-%d"),
                "Overdue": next_test < pd.Timestamp.now()
            }

            new_df = pd.DataFrame([new_row])
            updated_df = pd.concat([df, new_df], ignore_index=True)

            st.success("Cylinder added successfully (in memory)!")
            st.write("Preview of the new entry:")
            st.dataframe(new_df, use_container_width=True)

            # Create downloadable CSV
            csv = updated_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download updated cylinders CSV",
                data=csv,
                file_name="updated_cylinders_hyderabad.csv",
                mime="text/csv"
            )

# Footer
st.markdown("---")
st.caption("Cylinder Tracking Demo • Hyderabad • February 2026 • Built with Streamlit")