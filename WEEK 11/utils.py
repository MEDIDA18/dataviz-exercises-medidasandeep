import streamlit as st
import plotly.express as px


@st.cache_data
def load_data():
    df = px.data.gapminder()
    return df