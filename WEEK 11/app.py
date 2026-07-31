import streamlit as st

st.set_page_config(
    page_title="Gapminder Dashboard",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Gapminder Dashboard")

st.markdown("""
## Welcome!

This dashboard explores the Gapminder dataset using multiple Streamlit pages.

Use the navigation menu on the left to explore:

- How do countries compare today?
- How has life expectancy changed over time?
- What explains the differences between countries?

This dashboard follows the Summary → Trend → Detail design.
""")