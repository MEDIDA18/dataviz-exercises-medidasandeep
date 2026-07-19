import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="CO2 Dashboard", page_icon="🌱", layout="wide")

# ── Data Loading & Dynamic Column Mapping ─────────────────────────────────────
@st.cache_data
def load_data():
    path = Path(__file__).parent / 'data' / 'co2_emissions.csv'
    
    if not path.exists():
        st.error(f"❌ Critical Error: Could not find your dataset file at: `{path.resolve()}`.")
        st.stop()
        
    df = pd.read_csv(path)
    
    # Clean up column names by stripping trailing/leading whitespaces
    df.columns = df.columns.str.strip()
    
    # Dynamic Column Fallbacks (Fixes the KeyError)
    # Find a column containing "Year" (case-insensitive)
    year_col = next((c for c in df.columns if 'year' in c.lower()), None)
    if not year_col:
        st.error("❌ Could not find a 'Year' column in your CSV. Please check your file headers.")
        st.stop()
    df['Year'] = df[year_col]
    df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-01-01')
    
    # Auto-detect Region & Country
    region_col = next((c for c in df.columns if 'region' in c.lower()), 'Region')
    country_col = next((c for c in df.columns if 'country' in c.lower() or 'name' in c.lower()), 'Country')
    if region_col in df.columns: df['Region'] = df[region_col]
    if country_col in df.columns: df['Country'] = df[country_col]

    # Auto-detect the CO2 Metrics to prevent KeyErrors
    co2_total_col = next((c for c in df.columns if 'total' in c.lower() and 'co2' in c.lower()), None)
    if not co2_total_col:
        # If no "total", just grab the first column with "co2" that isn't per capita
        co2_total_col = next((c for c in df.columns if 'co2' in c.lower() and 'capita' not in c.lower()), None)
        
    co2_capita_col = next((c for c in df.columns if 'capita' in c.lower()), None)
    
    # Final validation safety net
    if not co2_total_col:
        st.error(f"❌ Could not find a CO2 Emissions column. Your CSV columns are: `{list(df.columns)}`")
        st.stop()
        
    # Store detected names back into a session state dictionary for reference
    st.session_state['detected_total_metric'] = co2_total_col
    st.session_state['detected_capita_metric'] = co2_capita_col if co2_capita_col else co2_total_col
    
    return df

df = load_data()

st.title("🌱 CO2 Emissions Explorer")
st.caption("Source: Our World in Data — ourworldindata.org/co2-emissions")

# ── TASK 1: Sidebar Filters ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    
    # Region Filter
    if 'Region' in df.columns:
        regions = ['All'] + sorted(df['Region'].dropna().unique().tolist())
        selected_region = st.selectbox("Select Region", options=regions)
        if selected_region == 'All':
            available_countries = sorted(df['Country'].unique())
        else:
            available_countries = sorted(df[df['Region'] == selected_region]['Country'].unique())
    else:
        selected_region = "All"
        available_countries = sorted(df['Country'].unique())
        
    # Countries Multiselect
    selected_countries = st.multiselect(
        "Select Countries", 
        options=available_countries, 
        default=available_countries[:3] if available_countries else None
    )
    
    if not selected_countries:
        st.warning("⚠️ Please select at least one country to view data.")
        st.stop()
        
    # Date Range Input
    min_year = int(df['Year'].min())
    max_year = int(df['Year'].max())
    
    date_range = st.date_input(
        "Select Date Range",
        value=[pd.to_datetime(f"{min_year}-01-01"), pd.to_datetime(f"{max_year}-01-01")],
        min_value=pd.to_datetime(f"{min_year}-01-01"),
        max_value=pd.to_datetime(f"{max_year}-01-01")
    )
    
    if len(date_range) < 2:
        st.warning("⚠️ Please select both a start date and an end date.")
        st.stop()
        
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    
    # Metric Toggle (Mapped dynamically to your actual CSV column names)
    metric_options = {
        f"Total CO2 ({st.session_state['detected_total_metric']})": st.session_state['detected_total_metric']
    }
    if st.session_state['detected_capita_metric'] != st.session_state['detected_total_metric']:
        metric_options[f"CO2 per Capita ({st.session_state['detected_capita_metric']})"] = st.session_state['detected_capita_metric']
        
    selected_metric_label = st.radio("Select Metric", options=list(metric_options.keys()))
    metric = metric_options[selected_metric_label]
    
    highlight_top = st.checkbox("Show only top emitter highlighted")

# Apply filters
filtered = df[
    (df['Country'].isin(selected_countries)) &
    (df['Date'] >= start_date) &
    (df['Date'] <= end_date)
].sort_values('Date')


# ── TASK 2: Filter Summary Caption ───────────────────────────────────────────
num_countries = len(filtered['Country'].unique()) if not filtered.empty else 0
start_year = start_date.year
end_year = end_date.year

st.info(
    f"📊 **Filter State Summary:** {num_countries} countries selected | "
    f"Region: `{selected_region}` | "
    f"Timeline: `{start_year} – {end_year}` | "
    f"Active Column: `{metric}`"
)


# ── EXTENSION: KPI Row ────────────────────────────────────────────────────────
if not filtered.empty:
    last_year = filtered['Year'].max()
    first_year = filtered['Year'].min()
    
    df_last = filtered[filtered['Year'] == last_year]
    df_first = filtered[filtered['Year'] == first_year]
    
    total_co2_latest = df_last[metric].sum()
    total_co2_first = df_first[metric].sum()
    
    if total_co2_first > 0:
        pct_change = ((total_co2_latest - total_co2_first) / total_co2_first) * 100
    else:
        pct_change = 0.0
        
    if not df_last.empty:
        top_emitter_row = df_last.loc[df_last[metric].idxmax()]
        top_country = top_emitter_row['Country']
        top_val = top_emitter_row[metric]
    else:
        top_country, top_val = "N/A", 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(f"Total Selected ({last_year})", f"{total_co2_latest:,.1f}")
    kpi2.metric("Overall Range Change (%)", f"{pct_change:+.1f}%", delta=f"{pct_change:+.1f}%", delta_color="inverse")
    kpi3.metric(f"Top Emitter ({last_year})", f"{top_country}", f"{top_val:,.1f}")

st.markdown("---")


# ── TASK 3: Main Data Visualizations ─────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

if filtered.empty:
    st.warning("No data points match your choices.")
else:
    with col_left:
        country_totals = filtered.groupby('Country')[metric].max()
        top_emitter_country = country_totals.idxmax() if not country_totals.empty else None
        
        fig_line = go.Figure()
        
        for country in filtered['Country'].unique():
            df_c = filtered[filtered['Country'] == country]
            
            if highlight_top:
                if country == top_emitter_country:
                    line_color = "#E65100"
                    line_width = 3.5
                    show_label = True
                else:
                    line_color = "#D3D3D3"
                    line_width = 1.5
                    show_label = False
            else:
                line_color = None
                line_width = 2.5
                show_label = False
                
            fig_line.add_trace(go.Scatter(
                x=df_c['Year'], 
                y=df_c[metric],
                mode='lines+markers' if len(df_c) < 10 else 'lines',
                name=country,
                line=dict(color=line_color, width=line_width),
                text=country
            ))
            
            if highlight_top and show_label and not df_c.empty:
                last_row = df_c.iloc[-1]
                fig_line.add_annotation(
                    x=last_row['Year'],
                    y=last_row[metric],
                    text=f" 🏆 {country}",
                    showarrow=False,
                    xanchor="left",
                    font=dict(color="#E65100", size=12, family="Arial-Bold")
                )

        title_text = f"Historical Trend: {selected_metric_label}"
        if highlight_top and top_emitter_country:
            title_text = f"Historical Trend: <b>{top_emitter_country}</b> Emerges as the Dominant Emitter"
            
        fig_line.update_layout(
            title={"text": title_text, "font": {"size": 18}},
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(title="Year", showgrid=True, gridcolor="#F0F0F0"),
            yaxis=dict(title=selected_metric_label, showgrid=True, gridcolor="#F0F0F0"),
            hovermode="x unified",
            showlegend=not highlight_top
        )
        
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        last_available_year = filtered['Year'].max()
        df_bar_data = filtered[filtered['Year'] == last_available_year].sort_values(by=metric, ascending=True)
        
        colors = ['#4A90E2'] * len(df_bar_data)
        if highlight_top and not df_bar_data.empty:
            colors = ['#D3D3D3' if c != top_emitter_country else '#E65100' for c in df_bar_data['Country']]

        fig_bar = go.Figure(go.Bar(
            x=df_bar_data[metric],
            y=df_bar_data['Country'],
            orientation='h',
            marker_color=colors
        ))
        
        fig_bar.update_layout(
            title={"text": f"Ranking Profile ({last_available_year})", "font": {"size": 16}},
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(title=selected_metric_label, showgrid=True, gridcolor="#F0F0F0"),
            yaxis=dict(title="Country"),
            margin=dict(l=10, r=10, t=40, b=40)
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)