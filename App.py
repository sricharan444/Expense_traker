import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Secure Expense Tracker", page_icon="🔐", layout="centered")

# --- INITIALIZE LOGIN STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- SIMPLE USER DATABASE ---
# For a quick setup, define your users and passwords here.
# (For production, never store passwords in plain text, but this works great for personal use!)
USER_CREDENTIALS = {
    "alex": "password123",
    "sam": "mysecret99",
    "guest": "welcome"
}

# --- 1. LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.title("🔐 Sign In")
    st.write("Please log in to access your personal expense dashboard.")
    
    with st.form("login_form"):
        username_input = st.text_input("Username").strip().lower()
        password_input = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button:
            if username_input in USER_CREDENTIALS and USER_CREDENTIALS[username_input] == password_input:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success(f"Welcome back, {username_input.capitalize()}!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

# --- 2. MAIN APP COMPONENT (LOGGED IN) ---
else:
    current_user = st.session_state.username
    
    # --- DATABASE CONNECTION ---
    # Connect to Google Sheets using Streamlit's native GSheets connection
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Read existing data from the sheet
        all_data = conn.read(ttl="0d") # ttl="0d" forces it to clear cache and read live data
    except Exception as e:
        st.error("Database connection error. Make sure your secrets are configured!")
        st.stop()

    # --- TOP NAV / LOGOUT ---
    col_title, col_logout = st.columns([3, 1])
    with col_title:
        st.title(f"💰 {current_user.capitalize()}'s Expenses")
    with col_logout:
        st.write("") # spacing
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    # --- MOBILE-FRIENDLY TABS ---
    tab1, tab2 = st.tabs(["➕ Add Expense", "📊 View My Logs"])

    # TAB 1: ADD NEW EXPENSE
    with tab1:
        st.subheader("Log a New Expense")
        with st.form(key="expense_form", clear_on_submit=True):
            expense_date = st.date_input("Date", datetime.date.today())
            category = st.selectbox(
                "Category",
                ["Food & Dining", "Rent & Housing", "Utilities", "Transportation", "Entertainment", "Shopping", "Healthcare", "Other"]
            )
            amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, format="%.2f")
            description = st.text_input("Description (Optional)")
            
            submit_button = st.form_submit_button(label="Save Expense")

        if submit_button:
            # Format new entry including the current logged-in username
            new_entry = pd.DataFrame([{
                "User": current_user,
                "Date": expense_date.strftime("%Y-%m-%d"),
                "Category": category,
                "Amount ($)": amount,
                "Description": description
            }])
            
            # Combine old data with new data and push it back to the cloud sheet
            updated_df = pd.concat([all_data, new_entry], ignore_index=True)
            conn.update(data=updated_df)
            st.success("Expense saved securely to the cloud!")
            st.rerun()

    # TAB 2: USER'S PERSONAL DASHBOARD
    with tab2:
        # Filter the global sheet so the user ONLY sees rows where "User" matches their username
        if not all_data.empty and "User" in all_data.columns:
            user_df = all_data[all_data["User"] == current_user]
        else:
            user_df = pd.DataFrame(columns=["User", "Date", "Category", "Amount ($)", "Description"])

        if user_df.empty:
            st.info("You haven't recorded any expenses yet!")
        else:
            # --- METRICS ---
            total_spent = user_df["Amount ($)"].astype(float).sum()
            st.metric(label="Your Total Spending", value=f"${total_spent:,.2f}")
            
            # --- CHART ---
            st.write("### Spending Breakdown")
            category_totals = user_df.groupby("Category")["Amount ($)"].sum()
            st.bar_chart(category_totals)
            
            # --- LOG TABLE ---
            st.write("### History Log")
            # Hide the "User" column when showing it to them since they know who they are
            display_df = user_df.drop(columns=["User"])
            st.dataframe(display_df, use_container_width=True, hide_index=True)
