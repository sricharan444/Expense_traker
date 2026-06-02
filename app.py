import streamlit as st
import pandas as pd
import datetime
import pymongo

s="mongodb+srv://sricharannemana444_db_user:3wNfiA2p4ZSDLdKI@cluster0.c7gzq5w.mongodb.net/?appName=Cluster0"

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Expense Tracker", page_icon="🔐", layout="centered")

# --- 2. MONGODB CONNECTION ---
@st.cache_resource
def init_connection():
    # Safely pulls the cloud connection string from Streamlit's environment secrets
    return pymongo.MongoClient(st.secrets["mongo"]["connection_string"])

try:
    client = init_connection()
    db = client["expense_tracker_db"]  # Database name
    collection = db["expenses"]       # Collection (table) name
except Exception as e:
    st.error("Could not connect to MongoDB Cloud. Check your Streamlit Secrets configuration!")
    st.stop()

# --- 3. INITIALIZE LOGIN STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Mock User Credentials (For personal/family use)
USER_CREDENTIALS = {
    "alex": "password123",
    "sam": "mysecret99",
    "venkat": "venkat123"
}
    

# --- 4. USER INTERFACE LOGIC ---
if not st.session_state.logged_in:
    # --- LOGIN SCREEN ---
    st.title("🔐 Sign In")
    st.write("Log in to access your secure cloud database.")
    
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
                st.error("Invalid username or password.")

else:
    # --- MAIN TRACKER DASHBOARD (IF LOGGED IN) ---
    current_user = st.session_state.username
    
    # Header & Logout Section
    col_title, col_logout = st.columns([3, 1])
    with col_title:
        st.title(f"💰 {current_user.capitalize()}'s Expenses")
    with col_logout:
        st.write("") 
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    # Mobile-friendly Layout Tabs
    tab1, tab2 = st.tabs(["➕ Add Expense", "📊 View My Logs"])

    # TAB 1: ADD EXPENSE TO MONGODB
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
            # Structuring the data as a JSON/BSON Document
            expense_document = {
                "user": current_user,
                "date": expense_date.strftime("%Y-%m-%d"),
                "category": category,
                "amount": amount,
                "description": description
            }
            # Sending it to the cloud
            collection.insert_one(expense_document)
            st.success("Expense saved securely to MongoDB Atlas!")
            st.rerun()

    # TAB 2: FETCH & DISPLAY USER DATA
    with tab2:
        # Crucial: Filters MongoDB data so Alex only pulls Alex's entries
        cursor = collection.find({"user": current_user})
        raw_data = list(cursor)

        if not raw_data:
            st.info("You haven't recorded any expenses yet!")
        else:
            # Convert JSON results into a clean Pandas table
            user_df = pd.DataFrame(raw_data)
            
            # Clean up metadata (hide MongoDB unique IDs and internal user tags)
            user_df = user_df.drop(columns=["_id", "user"], errors="ignore")
            user_df.columns = ["Date", "Category", "Amount ($)", "Description"]

            # Visual Summaries
            total_spent = user_df["Amount ($)"].sum()
            st.metric(label="Your Total Spending", value=f"${total_spent:,.2f}")
            
            st.write("### Spending Breakdown")
            category_totals = user_df.groupby("Category")["Amount ($)"].sum()
            st.bar_chart(category_totals)
            
            st.write("### History Log")
            st.dataframe(user_df, use_container_width=True, hide_index=True)
