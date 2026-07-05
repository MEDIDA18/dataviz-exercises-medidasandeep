import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ── Page configuration ─────────────────────────────────────────────────────
st.set_page_config(page_title="World Happiness Dashboard",
                   page_icon="🌍",
                   layout="wide")

# ── Data ───────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
df = pd.read_csv(DATA_DIR / "world_happiness_2023.csv")

df.columns = [
    "Country", "Region", "Score", "GDP", "Social_Support",
    "Life_Expectancy", "Freedom", "Generosity", "Corruption"
]

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    regions = ["All"] + sorted(df["Region"].unique().tolist())
    selected_region = st.selectbox("Region", regions)
    top_n = st.slider("Show top N countries", 5, 30, 15)

# ── Filter data ────────────────────────────────────────────────────────────
filtered = df if selected_region == "All" else df[df["Region"] == selected_region]
top = filtered.nlargest(top_n, "Score").sort_values("Score")

# ── Title ──────────────────────────────────────────────────────────────────
st.title("🌍 World Happiness Dashboard")
st.caption("Source: World Happiness Report 2023 | Kaggle")

# ── KPI row ────────────────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric("Countries", len(filtered))
k2.metric(
    "Avg Happiness Score",
    f"{filtered['Score'].mean():.2f}",
    f"{filtered['Score'].mean() - df['Score'].mean():+.2f} vs global",
)
k3.metric(
    "Happiest in selection",
    filtered.nlargest(1, "Score")["Country"].values[0],
    f"Score: {filtered['Score'].max():.2f}",
)

st.divider()

# ── Row 1 ──────────────────────────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Happiness Rankings")
    fig1 = px.bar(
        top,
        x="Score",
        y="Country",
        orientation="h",
        color="Score",
        color_continuous_scale="Blues",
        range_color=[4.5, 8.5],
        labels={"Score": "Happiness Score (0–10)", "Country": ""},
    )
    fig1.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(range=[0, 8.5], gridcolor="#EEEEEE"),
        yaxis=dict(showgrid=False),
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=5, b=10),
    )
    fig1.update_traces(marker_line_width=0)
    st.plotly_chart(fig1, use_container_width=True)

with right:
    st.subheader("Score vs GDP")
    fig2 = px.scatter(
        filtered,
        x="GDP",
        y="Score",
        hover_name="Country",
        color_discrete_sequence=["#2E75B6"],
        labels={"GDP": "Log GDP per Capita", "Score": "Happiness Score"},
    )
    fig2.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(gridcolor="#EEEEEE"),
        yaxis=dict(gridcolor="#EEEEEE"),
        margin=dict(l=10, r=10, t=5, b=10),
    )
    fig2.update_traces(marker=dict(size=9, opacity=0.8))
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2 ──────────────────────────────────────────────────────────────────
st.subheader("Factor breakdown for top countries")
factors = ["GDP", "Social_Support", "Life_Expectancy", "Freedom"]
top10 = filtered.nlargest(10, "Score")

fig3 = px.bar(
    top10.melt(id_vars="Country", value_vars=factors),
    x="value",
    y="Country",
    color="variable",
    orientation="h",
    barmode="stack",
    color_discrete_sequence=["#2E75B6", "#70AD47", "#FFC000", "#AAAAAA"],
    labels={"value": "Contribution", "variable": "Factor", "Country": ""},
)
fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis=dict(gridcolor="#EEEEEE"),
    legend=dict(orientation="h", y=1.2),
    margin=dict(l=10, r=10, t=40, b=10),
)
fig3.update_traces(marker_line_width=0)
st.plotly_chart(fig3, use_container_width=True)

# ── Exercise Solution: Diverging Colour Scale ──────────────────────────────
st.divider()
st.subheader("Difference from Global Average Happiness Score")

exercise_df = filtered.copy()
global_avg = df["Score"].mean()
exercise_df["Difference"] = exercise_df["Score"] - global_avg

fig4 = px.bar(
    exercise_df.sort_values("Difference"),
    x="Difference",
    y="Country",
    orientation="h",
    color="Difference",
    color_continuous_scale="RdBu",
    color_continuous_midpoint=0,
    labels={
        "Difference": "Difference from Global Average",
        "Country": ""
    },
)

fig4.add_annotation(
    x=0,
    y=1.02,
    xref="x",
    yref="paper",
    text="Global Average (Midpoint)",
    showarrow=True,
    arrowhead=2,
)

fig4.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=10, r=10, t=40, b=10),
)

st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.caption("Built with Streamlit + Plotly")
