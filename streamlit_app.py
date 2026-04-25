# Let's bring in the tools we need to build this dashboard
import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
import calendar
from datetime import datetime
import os
from dotenv import load_dotenv

# --- 1. SETTING THE STAGE ---
# Let's give the browser tab a nice title and make it wide so our charts have room to breathe
st.set_page_config(page_title="MoneyTrace AI", page_icon="💰", layout="wide")

# Streamlit forgets things every time a button is clicked, so we need to give it a "memory"
# Here we are creating an empty list to store the user's manual payment reminders
if 'reminders' not in st.session_state:
    st.session_state['reminders'] = pd.DataFrame(columns=['Name', 'Amount (€)', 'Category', 'Next Date', 'Frequency'])

# --- SETUP GEMINI API ---
load_dotenv()
GEMINI_API_KEY = os.getenv("AIzaSyC_88C4Gt9GH3yWXc8QV0cavT8fwzZ_Guw")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- HELPER FUNCTIONS ---
def categorize(desc):
    """Automatically assigns a category based on the transaction description."""
    desc = str(desc).lower()
    if any(x in desc for x in ['starbucks', 'esselunga', 'food', 'restaurant', 'mcdonalds', 'gelato']): return 'Dining & Groceries'
    if any(x in desc for x in ['amazon', 'zara', 'h&m', 'shop']): return 'Shopping'
    if any(x in desc for x in ['enel', 'rent', 'bill', 'vodafone']): return 'Bills'
    if any(x in desc for x in ['atm', 'uber', 'train', 'trenitalia', 'metro']): return 'Transport'
    if any(x in desc for x in ['salary', 'deposit', 'transfer']): return 'Income'

    #if it doesn'y match anything above, put it in 'Other' category
    return 'Other'

def get_ai_insights(df, persona, location):
    expenses = df[df['amount'] < 0]
    total_spent = expenses['amount'].abs().sum()
    
    # Get top 5 merchants with their actual spend amounts for better context
    top_merchants = expenses.groupby('description')['amount'].sum().abs().nlargest(3)
    merchant_string = ", ".join([f"{name} (€{amt:.2f})" for name, amt in top_merchants.items()])

    # 1. Create an empty list to hold our formatted text
    #merchant_list = []
    
    # 2. Loop through the top merchants one by one
    #for name, amt in top_merchants.items():
        
        # 3. Format the text nicely (e.g., "Zara (€50.00)")
        #formatted_text = f"{name} (€{amt:.2f})"
        
        # 4. Add it to our growing list
        #merchant_list.append(formatted_text)
        
    # 5. Glue the final list together with commas
    #merchant_string = ", ".join(merchant_list)
   
    prompt = f"""
    Act as a highly analytical and slightly blunt financial advisor. 
    The user is a {persona} living in {location}.
    They spent a total of €{total_spent:,.2f} this month.
    Their top 5 expense locations are: {merchant_string}.
    
    Provide a 2-part assessment:
    1. Financial Health Grade: (A, B, or C) with a 1-sentence brutally honest reason.
    2. Roast & Replace: Look at their top merchants. Pick the most wasteful one (like a specific coffee shop, fast fashion brand, or food delivery app). Tell them exactly why it's a bad financial habit and provide a specific, cheaper, and realistic alternative based on their location ({location}) and lifestyle ({persona}). Be direct.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"API Error: {str(e)}"

# --- MAIN UI ---
st.title("💰 MoneyTrace AI")
st.markdown("Leveraging **Gemini 2.5 Flash** for smarter financial tracking.")

uploaded_file = st.file_uploader("Upload your Bank CSV", type="csv")

if uploaded_file:
    # 1. Load and clean data
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip().lower() for c in df.columns] # standardize columns
    
    # Check for necessary columns
    if 'date' in df.columns and 'description' in df.columns and 'amount' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['amount_abs'] = df['amount'].abs()
        df['category'] = df['description'].apply(categorize)
        
        # Isolate expenses for visualizations
        expenses_df = df[df['amount'] < 0].copy()

        # --- CREATE TABS ---
        tab_dash, tab_ai, tab_reminders, tab_data = st.tabs([
            "📊 Daily Dashboard", 
            "🔮 AI & Forecasting", 
            "📅 Reminders", 
            "📋 Raw Data"
        ])

        # ==========================================
        # TAB 1: THE DASHBOARD 
        # ==========================================
        with tab_dash:
            # Feature: Top 3 Spending Podium
            st.subheader("🏆 Top 3 Spending Categories")
            top_cats = expenses_df.groupby('category')['amount_abs'].sum().nlargest(3)
            
            if not top_cats.empty:
                podium_cols = st.columns(len(top_cats))
                for i, (cat, val) in enumerate(top_cats.items()):
                    podium_cols[i].metric(f"#{i+1} {cat}", f"€{val:,.2f}")
            st.divider()

            # Main Charts
            c1, c2 = st.columns(2)
            
            with c1:
                st.metric("Total Monthly Spend", f"€{expenses_df['amount_abs'].sum():,.2f}")
                
                # Altair Horizontal Bar Chart (Replaces Plotly)
                top_merchants = expenses_df.groupby('description')['amount_abs'].sum().nlargest(10).reset_index()
                bar_chart = alt.Chart(top_merchants).mark_bar(cornerRadiusEnd=4).encode(
                    x=alt.X('amount_abs:Q', title="Amount (€)"),
                    y=alt.Y('description:N', sort='-x', title=""),
                    color=alt.Color('description:N', legend=None),
                    tooltip=['description', 'amount_abs']
                ).properties(title="Top 10 Expense Locations")
                
                st.altair_chart(bar_chart, use_container_width=True)
                
            with c2:
                st.metric("Transaction Count", len(df))
                
                # Streamlit Native Area Chart (Replaces Plotly)
                st.markdown("**Daily Balance Trend**")
                daily = df.groupby('date')['amount'].sum().reset_index()
                st.area_chart(daily, x='date', y='amount', color="#1f77b4")

        # ==========================================
        # TAB 2: AI & FORECASTING 
        # ==========================================
        with tab_ai:
            # --- Robust Forecast Math (Using Median) ---
            if not expenses_df.empty:
                # 1. Group by date to find the total spent on each active day
                daily_totals = expenses_df.groupby('date')['amount_abs'].sum()
                
                # 2. Find the median daily spend (bypasses massive outliers like rent)
                median_daily_spend = daily_totals.median()
                
                last_transaction_date = df['date'].max()
                days_passed = last_transaction_date.day
                
                if days_passed > 0:
                    total_days_in_month = calendar.monthrange(last_transaction_date.year, last_transaction_date.month)[1]
                    
                    # 3. Project the total using the median
                    forecasted_total = median_daily_spend * total_days_in_month
                    
                    st.metric(
                        label="Projected End-of-Month Spend", 
                        value=f"€{forecasted_total:,.2f}", 
                        delta=f"Based on a typical median spend of €{median_daily_spend:,.2f} per day", 
                        delta_color="off"
                    )
                
            st.divider()
            
             # --- NEW: Dynamic User Profile & Gemini Insights ---
            st.subheader("🤖 Financial Health Check & Roast")
                
             # 1. Let the user define themselves
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                user_persona = st.selectbox("Who are you?", ["Student", "Young Professional", "Freelancer", "Parent"])
            with p_col2:
                user_location = st.text_input("City/Location", value="Milan")
                    
            # 2. Add a button to trigger the AI
            if st.button("Generate Financial Roast"):
                with st.spinner("Analyzing your terrible spending habits..."):
                    # Pass all THREE variables to the function now
                    ai_advice = get_ai_insights(df, user_persona, user_location)
                    st.info(ai_advice)

        # ==========================================
        # TAB 3: REMINDERS (Interactive Form)
        # ==========================================
        with tab_reminders:
            st.subheader("⏰ Upcoming Payment Tracker")
            st.markdown("Manually set reminders for your recurring bills so you never miss a payment.")
            
            # Form to add new reminders
            with st.form("reminder_form"):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    r_name = st.text_input("Payment Name (e.g., Spotify, Gym)")
                    r_category = st.selectbox("Category", ["Bills", "Entertainment", "Transport", "Other"])
                with r_col2:
                    r_amount = st.number_input("Amount (€)", min_value=0.0, step=1.0, format="%.2f")
                    r_date = st.date_input("Next Payment Date")
                    
                r_freq = st.selectbox("Frequency", ["1-time", "Weekly", "Monthly", "Yearly"])
                
                submitted = st.form_submit_button("➕ Add Reminder")
                
                if submitted and r_name:
                    new_row = pd.DataFrame([{
                        'Name': r_name, 
                        'Amount (€)': r_amount, 
                        'Category': r_category, 
                        'Next Date': r_date.strftime("%Y-%m-%d"), 
                        'Frequency': r_freq
                    }])
                    st.session_state['reminders'] = pd.concat([st.session_state['reminders'], new_row], ignore_index=True)
                    st.success(f"Successfully added '{r_name}' to your schedule!")

            # Display the saved reminders
            st.divider()
            st.subheader("Your Scheduled Payments")
            
            if len(st.session_state['reminders']) > 0:
                st.dataframe(st.session_state['reminders'], use_container_width=True, hide_index=True)
            else:
                st.info("No reminders set yet. Use the form above to add your first one!")

        # ==========================================
        # TAB 4: RAW DATA 
        # ==========================================
        with tab_data:
            st.subheader("Transaction Ledger")
            st.dataframe(df, use_container_width=True)
            
    else:
        st.error("Missing columns! Please ensure your CSV has 'date', 'description', and 'amount' columns.")
        
else:
    st.info("Please upload a CSV file to begin.")
