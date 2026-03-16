MoneyTrace AI
An AI-powered personal finance dashboard built with Python, Streamlit, and Google Gemini 2.5 Flash.**

MoneyTrace AI bridges the gap between static expense tracking and proactive financial management. By combining robust data analysis (Pandas) with Generative AI, this application doesn't just show users where their money went—it analyzes their habits, projects future spending, and provides actionable, personalized financial advice.

Key Features

* Dynamic Dashboard:** Instantly visualize your spending with an Altair-powered horizontal bar chart mapping top expense locations, a daily balance trend area chart, and a "Top 3 Categories" metric podium.
*  Median-Based Run-Rate Forecasting:** Outlier-resistant financial modeling. Calculates the median daily spend to project accurate end-of-month totals, ignoring massive skewed data points like rent payments.
*  AI "Roast & Replace" Engine:** Context-aware financial advice. Users input their persona (e.g., Student, Freelancer) and city, and Gemini 2.5 Flash analyzes their top 5 merchants to deliver a brutally honest financial grade and specific, localized money-saving alternatives.
*  Interactive Payment Tracker:** A state-managed recurring payment dashboard. Users can manually log upcoming bills, categories, and frequencies, saved dynamically via Streamlit Session State.
* **🧹 Smart Categorization:** Automated keyword-based transaction sorting built directly into the data pipeline.

## Tech Stack

* Frontend & Framework: Streamlit
* Data Manipulation: Pandas, NumPy
* Data Visualization: Altair, Streamlit Native Charts
* Generative AI: Google Generative AI (Gemini 2.5 Flash)

## 📂 CSV Data Requirements

To use the app, upload a bank export CSV containing at least the following three columns (headers are case-insensitive and stripped of whitespace automatically):
1.  `date`: The transaction date (e.g., YYYY-MM-DD)
2.  `description`: The merchant or transaction name
3.  `amount`: The transaction value (negative numbers for expenses, positive for income)
