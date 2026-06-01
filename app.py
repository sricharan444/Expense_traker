import streamlit as st
import pandas as pd
import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Personal Expense Tracker", page_icon="💰", layout="centered")

# --- INITIALIZE SESSION STATE ---
# We use Streamlit's session state to keep track of data across reruns
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(
        columns=["Date", "Category", "Amount ($)", "Description"]
    )

# --- APP TITLE ---
st.title("💰 Personal Expense Tracker")
st.write("Track your daily spending, view summaries, and visualize where your money goes.")
st.markdown("---")

# --- SIDEBAR: ADD NEW EXPENSE ---
st.sidebar.header("Add New Expense")

with st.sidebar.form(key="expense_form", clear_on_submit=True):
    expense_date = st.date_input("Date", datetime.date.today())
    
    category = st.selectbox(
        "Category",
        ["Food & Dining", "Rent & Housing", "Utilities", "Transportation", "Entertainment", "Shopping", "Healthcare", "Other"]
    )
    
    amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, format="%.2f")
    description = st.text_input("Description (Optional)")
    
    submit_button = st.form_submit_button(label="Add Expense")

# Logic to append new data
if submit_button:
    new_data = pd.DataFrame([{
        "Date": expense_date.strftime("%Y-%m-%d"),
        "Category": category,
        "Amount ($)": amount,
        "Description": description
    }])
    
    # Concatenate the new expense to our session dataframe
    st.session_state.expenses = pd.concat([st.session_state.expenses, new_data], ignore_index=True)
    st.sidebar.success("Expense added successfully!")

# --- MAIN DASHBOARD ---
df = st.session_state.expenses

if df.empty:
    st.info("No expenses recorded yet. Use the sidebar to add your first expense!")
else:
    # --- METRICS SECTION ---
    total_spent = df["Amount ($)"].sum()
    num_transactions = len(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Expenses", value=f"${total_spent:,.2f}")
    with col2:
        st.metric(label="Total Transactions", value=num_transactions)
        
    st.markdown("---")
    
    # --- VISUALIZATION SECTION ---
    st.subheader("📊 Spending Breakdown by Category")
    
    # Group data by category for the chart
    category_totals = df.groupby("Category")["Amount ($)"].sum()
    
    # Display Streamlit's native bar chart or pie chart (using a bar chart here for clean UI)
    st.bar_chart(category_totals)
    
    st.markdown("---")
    
    # --- DATA TABLE SECTION ---
    st.subheader("📝 Expense Log")
    
    # Display the dataframe nicely
    st.dataframe(df, use_container_width=True)
    
    # --- ACTIONS (DOWNLOAD & CLEAR) ---
    col3, col4 = st.columns([1, 1])
    
    with col3:
        # Export to CSV feature
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Expenses as CSV",
            data=csv,
            file_name="expense_report.csv",
            mime="text/csv",
        )
        
    with col4:
        # Clear data button
        if st.button("🗑️ Clear All Data", type="primary"):
            st.session_state.expenses = pd.DataFrame(columns=["Date", "Category", "Amount ($)", "Description"])
            st.rerun()
