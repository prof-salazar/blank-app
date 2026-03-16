import streamlit as st
import pandas as pd
import altair as alt
import google.generativeai as genai
import calendar

# --- 1. SETUP GEMINI ---
GEMINI_API_KEY = "AIzaSyC2E3oDdm8pKoYk3cqLfXRsQ7Z3copaaYE" # Paste your key back here
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. THE AI BRAIN ---
def get_ai_insights(df):
    # Prepare a summary for the AI
    total_spent = df[df['amount'] < 0]['amount'].abs().sum()
    top_merchants = df[df['amount'] < 0]['description'].value_counts().head(5).index.tolist()
    
    prompt = f"""
    Act as a professional financial advisor. 
    The user spent a total of €{total_spent:,.2f} this month.
    Their top 5 frequent merchants are: {', '.join(top_merchants)}.
    
    1. Give a 1-sentence 'Financial Health Grade' (A, B, or C) with a reason.
    2. Give one specific 'Pro-Tip' for a student living in Milan to save money.
    Keep the tone professional and concise.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"API Error: {str(e)}"

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="MoneyTrace AI", layout="wide")
st.title("💰 MoneyTrace AI")
st.markdown("Leveraging **Gemini 2.5 Flash** for smarter financial tracking.")

uploaded_file = st.file_uploader("Upload your Bank CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Basic Processing
    df['date'] = pd.to_datetime(df['date'])
    df['amount_abs'] = df['amount'].abs()
    
    # Isolate expenses for calculations
    expenses_df = df[df['amount'] < 0]

    # --- CREATE TABS ---
    tab_dash, tab_ai, tab_data = st.tabs(["📊 Daily Dashboard", "🔮 AI & Forecasting", "📋 Raw Data"])

    # ==========================================
    # TAB 1: THE DASHBOARD 
    # ==========================================
    with tab_dash:
        st.subheader("Current Month Snapshot")
        c1, c2 = st.columns(2)
        
        with c1:
            st.metric("Total Monthly Spend", f"€{expenses_df['amount_abs'].sum():,.2f}")
            
            # Replaced Plotly Pie Chart with a clean Altair Horizontal Bar Chart
            top_expenses = expenses_df.groupby('description')['amount_abs'].sum().nlargest(10).reset_index()
            
            bar_chart = alt.Chart(top_expenses).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X('amount_abs:Q', title="Amount (€)"),
                y=alt.Y('description:N', sort='-x', title=""),
                color=alt.Color('description:N', legend=None),
                tooltip=['description', 'amount_abs']
            ).properties(title="Top 10 Expense Locations")
            
            st.altair_chart(bar_chart, use_container_width=True)
            
        with c2:
            st.metric("Transaction Count", len(df))
            
            # Replaced Plotly Line Chart with Streamlit's Native Area Chart (Zero extra code!)
            daily = df.groupby('date')['amount'].sum().reset_index()
            st.markdown("**Daily Balance Trend**")
            st.area_chart(daily, x='date', y='amount', color="#1f77b4")
    # ==========================================
    # TAB 2: AI & FORECASTING 
    # ==========================================
    with tab_ai:
        st.subheader("End of Month Projections")
        
        # Forecast Math
        total_spent = expenses_df['amount_abs'].sum()
        last_transaction_date = df['date'].max()
        days_passed = last_transaction_date.day
        
        if days_passed > 0:
            total_days_in_month = calendar.monthrange(last_transaction_date.year, last_transaction_date.month)[1]
            average_daily_spend = total_spent / days_passed
            forecasted_total = average_daily_spend * total_days_in_month
            
            st.metric(
                label="Projected End-of-Month Spend", 
                value=f"€{forecasted_total:,.2f}", 
                delta=f"Based on a run-rate of €{average_daily_spend:,.2f} per day", 
                delta_color="off"
            )
            
        st.divider()
        
        # Gemini API Call
        st.subheader("🤖 Financial Health Check")
        with st.spinner("Gemini is analyzing your spending patterns..."):
            ai_advice = get_ai_insights(df)
        st.info(ai_advice)

    # ==========================================
    # TAB 3: DATA TABLE 
    # ==========================================
    with tab_data:
        st.subheader("Transaction Ledger")
        st.dataframe(df, use_container_width=True)

else:
    st.info("Please upload a CSV file to begin.")
