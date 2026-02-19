import streamlit as st
import pandas as pd

# ────────────────────────────────────────────────
# Load and clean the data (cached for performance)
# ────────────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("random_cylinders_hyderabad.csv")
        
        # Fix for PIN code matching issues
        df["Location_PIN"] = df["Location_PIN"].astype(str).str.strip()
        # Optional: force exactly 6 digits with leading zeros if needed
        # df["Location_PIN"] = df["Location_PIN"].str.zfill(6)
        
        # Convert date columns safely
        for col in ["Last_Fill_Date", "Last_Test_Date", "Next_Test_Due"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except FileNotFoundError:
        st.error("CSV file not found in the repository root. Please upload 'random_cylinders_hyderabad.csv' to your GitHub repo.")
        return pd.DataFrame()  # return empty df to avoid crash
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Load the data once
df = load_data()

# If no data loaded → early exit with message
if df.empty:
    st.stop()

# ────────────────────────────────────────────────
# Sidebar navigation (like Leo Gas style)
# ────────────────────────────────────────────────
st.sidebar.title("Cylinder Management App")
st.sidebar.markdown("Inspired by Leo Gas services")
page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "Cylinder Finder", "Safety Information", "Simulate Refill"]
)

# ────────────────────────────────────────────────
# Main content based on selected page
# ────────────────────────────────────────────────
if page == "Dashboard":
    st.title("Cylinder Tracking Dashboard")
    st.write(f"Currently showing **{len(df)}** cylinders across Hyderabad areas.")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=sorted(df["Status"].unique()),
            default=df["Status"].unique()
        )
    with col2:
        overdue_only = st.checkbox("Show Overdue Cylinders Only", value=False)

    # Apply filters
    filtered_df = df[df["Status"].isin(status_filter)]
    if overdue_only:
        filtered_df = filtered_df[filtered_df["Overdue"] == True]

    # Show table
    st.dataframe(
        filtered_df.sort_values("Next_Test_Due"),
        use_container_width=True,
        column_config={
            "Next_Test_Due": st.column_config.DateColumn("Next Test Due"),
            "Overdue": st.column_config.CheckboxColumn("Overdue")
        }
    )

    # Quick stats
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
            # Update in memory
            df.loc[df["Cylinder_ID"] == cylinder_id, "Fill_Percent"] = new_fill
            df.loc[df["Cylinder_ID"] == cylinder_id, "Last_Fill_Date"] = pd.Timestamp.now()
            
            # Try to save back (note: this only works locally or if repo allows write)
            try:
                df.to_csv("random_cylinders_hyderabad.csv", index=False)
                st.success(f"Refilled {cylinder_id} to {new_fill}%! (saved locally)")
            except:
                st.warning("Refill recorded in memory only (Streamlit Cloud is read-only). Download updated data manually if needed.")
    else:
        st.warning("No cylinders loaded. Please check your CSV file.")

# Footer
st.markdown("---")
st.caption("Cylinder Tracking Demo • Hyderabad • February 2026 • Built with Streamlit")