import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt

st.set_page_config(page_title="NZ Property Tax & Mortgage Optimiser", layout="wide")

st.title("🏡 NZ Property Tax & Mortgage Optimisation Tool")

st.markdown("""
This tool helps New Zealand property investors optimise tax and mortgage strategies across multiple rental properties. 
It models the impact of deductible rental expenses, repayment types, and revolving credit on your owner-occupied home loan.
""")

# --- Sidebar Inputs ---
st.sidebar.header("🔧 Input Parameters")

# --- Owner-Occupied Inputs ---
st.sidebar.subheader("🏠 Owner-Occupied Home Loan")
home_loan = st.sidebar.number_input("Home Loan Balance ($)", value=975000, step=1000)
home_rate = st.sidebar.number_input("Home Loan Interest Rate (%)", value=4.99, step=0.01) / 100
home_term = st.sidebar.number_input("Home Loan Term (years)", value=30, step=1)
home_insurance = st.sidebar.number_input("Home Insurance ($/year)", value=4200, step=100)
home_rates = st.sidebar.number_input("Home Council Rates ($/year)", value=4300, step=100)

# --- Rental Portfolio Inputs ---
st.sidebar.subheader("🏘 Rental Portfolio")
num_rentals = st.sidebar.number_input("Number of Rental Properties", min_value=1, max_value=10, value=1)

rental_properties = []

for i in range(num_rentals):
    with st.sidebar.expander(f"Rental Property {i+1}"):
        loan = st.number_input(f"[{i+1}] Loan Balance ($)", value=385000, step=1000, key=f"loan_{i}")
        rate = st.number_input(f"[{i+1}] Interest Rate (%)", value=4.99, step=0.01, key=f"rate_{i}") / 100
        term = st.number_input(f"[{i+1}] Loan Term (years)", value=30, step=1, key=f"term_{i}")
        repayment_type = st.selectbox(f"[{i+1}] Repayment Type", ["Interest-Only", "Principal & Interest"], key=f"type_{i}")
        rent_weekly = st.number_input(f"[{i+1}] Weekly Rent ($)", value=760, key=f"rent_{i}")
        insurance = st.number_input(f"[{i+1}] Insurance ($/year)", value=3500, key=f"ins_{i}")
        rates = st.number_input(f"[{i+1}] Council Rates ($/year)", value=4300, key=f"rates_{i}")
        maintenance = st.number_input(f"[{i+1}] Maintenance ($/year)", value=2000, key=f"maint_{i}")
        mgmt_fee = st.number_input(f"[{i+1}] Property Mgmt Fee (%)", value=5.2, key=f"mgmt_{i}") / 100
        depreciation = st.number_input(f"[{i+1}] Chattel Depreciation ($)", value=1500, key=f"dep_{i}")

        rental_properties.append({
            "loan": loan,
            "rate": rate,
            "term": term,
            "type": repayment_type,
            "rent_weekly": rent_weekly,
            "insurance": insurance,
            "rates": rates,
            "maintenance": maintenance,
            "mgmt_fee": mgmt_fee,
            "depreciation": depreciation
        })

# --- Global Settings ---
st.sidebar.subheader("⚙️ Global Settings")
tax_rate = st.sidebar.number_input("Marginal Tax Rate (%)", value=33) / 100
projection_years = st.sidebar.slider("Projection Period (years)", 1, 10, 5)

# --- Calculations ---
total_rent = 0
total_expenses = 0
total_tax_savings = 0
total_cash_freed = 0

for prop in rental_properties:
    annual_rent = prop["rent_weekly"] * 52
    interest = prop["loan"] * prop["rate"]
    mgmt_cost = annual_rent * prop["mgmt_fee"]
    expenses = interest + prop["insurance"] + prop["rates"] + prop["maintenance"] + mgmt_cost + prop["depreciation"]
    tax_savings = min(expenses, annual_rent) * tax_rate

    if prop["type"] == "Interest-Only":
        monthly_pni = npf.pmt(prop["rate"] / 12, prop["term"] * 12, -prop["loan"])
        annual_pni = monthly_pni * 12
        cash_freed = annual_pni - interest
    else:
        cash_freed = 0

    total_rent += annual_rent
    total_expenses += expenses
    total_tax_savings += tax_savings
    total_cash_freed += cash_freed

# --- Revolving Credit Impact ---
balance = home_loan
annual_savings = []
principal_paid = []
cumulative_interest_saved = []
cumulative_saved = 0

for year in range(1, projection_years + 1):
    balance -= total_cash_freed
    interest_saved = balance * home_rate
    cumulative_saved += interest_saved
    annual_savings.append(interest_saved)
    principal_paid.append(total_cash_freed * year)
    cumulative_interest_saved.append(cumulative_saved)

# --- Output Summary ---
st.header("📊 Summary")

col1, col2 = st.columns(2)
with col1:
    st.subheader("🏘 Rental Portfolio Summary")
    st.write(f"**Total Annual Rent:** ${total_rent:,.0f}")
    st.write(f"**Total Rental Expenses:** ${total_expenses:,.0f}")
    st.write(f"**Total Tax Saved:** ${total_tax_savings:,.0f}")
    st.write(f"**Annual Cash Freed (from IO rentals):** ${total_cash_freed:,.0f}")

with col2:
    st.subheader("🏠 Home Loan Strategy")
    st.write(f"**Total Extra Paid into Revolving Credit ({projection_years} yrs):** ${total_cash_freed * projection_years:,.0f}")
    st.write(f"**Cumulative Interest Saved on Home Loan:** ${cumulative_saved:,.0f}")

# --- Chart ---
st.subheader("📈 Impact of Redirecting Rental Cash Flow to Home Loan")

chart_data = pd.DataFrame({
    "Year": list(range(1, projection_years + 1)),
    "Total Extra Paid ($)": principal_paid,
    "Cumulative Interest Saved ($)": cumulative_interest_saved
})

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(chart_data["Year"], chart_data["Total Extra Paid ($)"], label="Total Extra Paid", marker='o')
ax.plot(chart_data["Year"], chart_data["Cumulative Interest Saved ($)"], label="Interest Saved", marker='s')
ax.set_xlabel("Year")
ax.set_ylabel("Amount ($)")
ax.set_title("Owner-Occupied Loan Strategy")
ax.grid(True)
ax.legend()
st.pyplot(fig)
