import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import run_query, QUERIES
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Page Config ───
st.set_page_config(
    page_title="ChainSight | Supply Chain Intelligence",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0F1117;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }

    /* KPI Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(
            135deg, #161B22 0%, #1C2333 100%
        );
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    /* KPI Value */
    div[data-testid="metric-container"] 
    [data-testid="stMetricValue"] {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #00D4AA !important;
    }
    

    /* KPI Label */
    div[data-testid="metric-container"]
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #8B949E !important;
        font-weight: 500 !important;
    }

    /* Section Headers */
    h2, h3 {
        color: #E6EDF3 !important;
        font-weight: 600 !important;
    }

    /* Divider */
    hr {
        border-color: #30363D !important;
        margin: 20px 0 !important;
    }

    /* Dataframe */
    .dataframe {
        background-color: #161B22 !important;
        border-radius: 10px !important;
    }

    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(
            90deg, #00D4AA, #0066FF
        ) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
    }

    /* Sidebar filters */
    .stMultiSelect > div {
        background-color: #1C2333 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
    }

    /* Alert boxes */
    .alert-box {
        background: linear-gradient(
            135deg, #1C2333, #161B22
        );
        border-left: 4px solid #FF6B6B;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 8px 0;
        color: #E6EDF3;
        font-size: 14px;
    }

    .alert-success {
        border-left-color: #00D4AA;
    }

    .alert-warning {
        border-left-color: #FFB347;
    }

    /* Top header bar */
    .header-bar {
        background: linear-gradient(
            90deg, #0066FF22, #00D4AA22
        );
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 24px;
    }

    /* Chart containers */
    .chart-container {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ── Load Data ───
@st.cache_data
def load_all_data():
    orders_df = run_query("SELECT * FROM orders")
    risk_df = run_query("SELECT * FROM risk_scores")
    return orders_df, risk_df

orders_df, risk_df = load_all_data()

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🔗 ChainSight")
    st.markdown(
        "*Supply Chain Intelligence Platform*"
    )
    st.divider()

    st.markdown("### 🔧 Filters")

    selected_region = st.multiselect(
        "🌍 Region",
        options=sorted(
            orders_df['region'].dropna().unique()
        ),
        default=[]
    )

    selected_shipping = st.multiselect(
        "🚢 Shipping Mode",
        options=sorted(
            orders_df['shipping_mode'].dropna().unique()
        ),
        default=[]
    )

    selected_risk = st.multiselect(
        "⚠️ Risk Category",
        options=['Low Risk', 'Medium Risk', 'High Risk'],
        default=[]
    )

    selected_year = st.multiselect(
        "📅 Year",
        options=[2015, 2016, 2017, 2018],
        default=[]
    )

    st.divider()
    st.markdown(
        "📊 **Data:** 180,519 orders\n\n"
        "📅 **Period:** 2015–2018\n\n"
        "🌍 **Markets:** Global"
    )

# ── Apply Filters ──
filtered_orders = orders_df.copy()
filtered_risk = risk_df.copy()

filtered_orders['order_date'] = pd.to_datetime(
    filtered_orders['order_date']
)

if selected_region:
    filtered_orders = filtered_orders[
        filtered_orders['region'].isin(selected_region)
    ]
if selected_shipping:
    filtered_orders = filtered_orders[
        filtered_orders['shipping_mode'].isin(
            selected_shipping
        )
    ]
if selected_year:
    filtered_orders = filtered_orders[
        filtered_orders['order_date'].dt.year.isin(
            selected_year
        )
    ]
if selected_risk:
    filtered_risk = filtered_risk[
        filtered_risk['risk_category'].isin(selected_risk)
    ]
    filtered_orders = filtered_orders[
        filtered_orders['order_id'].isin(
            filtered_risk['order_id']
        )
    ]

# ── Header ──
st.markdown("""
<div class="header-bar">
    <h1 style="margin:0; color:#E6EDF3; font-size:32px;">
        🔗 ChainSight
    </h1>
    <p style="margin:4px 0 0 0; color:#8B949E; 
              font-size:15px;">
        Supply Chain Intelligence Platform — 
        Risk Analytics & Performance Dashboard
    </p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──
total = len(filtered_orders)
delayed = filtered_orders['is_delayed'].sum()
on_time_rate = round(
    100 - (delayed / total * 100), 2
) if total > 0 else 0
total_revenue = round(
    filtered_orders['sales'].sum(), 2
)
avg_days = round(
    filtered_orders['actual_shipping_days'].mean(), 1
)
total_profit = round(
    filtered_orders['profit'].sum(), 2
)

merged_kpi = filtered_orders.merge(
    filtered_risk[['order_id', 'risk_category']],
    on='order_id', how='left'
)
revenue_at_risk = round(
    merged_kpi[
        merged_kpi['risk_category'] == 'High Risk'
    ]['sales'].sum(), 2
)
high_risk_count = len(
    merged_kpi[
        merged_kpi['risk_category'] == 'High Risk'
    ]
)
risk_pct = round(
    high_risk_count / total * 100, 1
) if total > 0 else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📦 Total Orders", f"{total:,}")
k2.metric(
    "✅ On-Time Rate",
    f"{on_time_rate}%",
    delta=f"{on_time_rate - 50:.1f}% vs target"
)
k3.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
k4.metric("📈 Total Profit", f"${total_profit:,.0f}")
k5.metric(
    "⚠️ Revenue at Risk",
    f"${revenue_at_risk:,.0f}"
)
k6.metric("🚚 Avg Ship Days", f"{avg_days} days")

st.divider()

# ── Smart Alerts ──
st.markdown("### 🚨 Smart Alerts")

col_a, col_b, col_c = st.columns(3)

with col_a:
    if on_time_rate < 50:
        st.markdown(f"""
        <div class="alert-box">
            🔴 <b>Critical:</b> On-Time Rate 
            {on_time_rate}% is below 50% target.<br>
            <small>Immediate action required</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-box alert-success">
            🟢 <b>Good:</b> On-Time Rate is above target.
        </div>
        """, unsafe_allow_html=True)

with col_b:
    risk_pct = round(
        high_risk_count / total * 100, 1
    ) if total > 0 else 0
    if risk_pct > 70:
        st.markdown(f"""
        <div class="alert-box">
            🔴 <b>High Risk:</b> {risk_pct}% orders 
            flagged as High Risk.<br>
            <small>Review supply chain immediately</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-box alert-warning">
            🟡 <b>Monitor:</b> {risk_pct}% orders 
            in High Risk zone.
        </div>
        """, unsafe_allow_html=True)

with col_c:
    rev_risk_pct = round(
        revenue_at_risk / total_revenue * 100, 1
    ) if total_revenue > 0 else 0
    st.markdown(f"""
    <div class="alert-box alert-warning">
        🟡 <b>Revenue Alert:</b> 
        {rev_risk_pct}% of revenue 
        (${revenue_at_risk:,.0f}) at risk.<br>
        <small>High risk orders detected</small>
    </div>
    """, unsafe_allow_html=True)

st.divider()

#  Charts Row 1 
col1, col2 = st.columns(2)

CHART_LAYOUT = dict(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#8B949E'),
    height=380,
    margin=dict(t=30, b=30, l=10, r=10)
)

with col1:
    st.markdown("### 🌍 Delay Rate by Region")
    region_data = run_query(QUERIES['delay_by_region'])
    fig1 = px.bar(
        region_data,
        x='delay_rate',
        y='region',
        orientation='h',
        color='delay_rate',
        color_continuous_scale=[
            '#00D4AA', '#FFB347', '#FF6B6B'
        ],
        text=region_data['delay_rate'].apply(
            lambda x: f"{x}%"
        )
    )
    fig1.update_traces(textposition='outside')
    fig1.update_layout(
        **CHART_LAYOUT,
        xaxis_title="Delay Rate %",
        yaxis_title="",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("### 🚢 Shipping Mode Performance")
    ship_data = run_query(QUERIES['shipping_performance'])
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name='Total Orders',
        x=ship_data['shipping_mode'],
        y=ship_data['total_orders'],
        marker_color='#00D4AA',
        text=ship_data['total_orders'],
        textposition='outside'
    ))
    fig2.add_trace(go.Bar(
        name='Delayed Orders',
        x=ship_data['shipping_mode'],
        y=ship_data['delayed_orders'],
        marker_color='#FF6B6B',
        text=ship_data['delayed_orders'],
        textposition='outside'
    ))
    fig2.update_layout(
        **CHART_LAYOUT,
        barmode='group',
        xaxis_title="Shipping Mode",
        yaxis_title="Orders",
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8B949E')
        )
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Charts Row 2 ──
col3, col4 = st.columns(2)

with col3:
    st.markdown("### ⚠️ Risk Category Distribution")
    risk_counts = filtered_risk[
        'risk_category'
    ].value_counts().reset_index()
    risk_counts.columns = ['risk_category', 'count']

    fig3 = go.Figure(go.Pie(
        labels=risk_counts['risk_category'],
        values=risk_counts['count'],
        hole=0.5,
        marker=dict(colors=[
            '#FF6B6B', '#FFB347', '#00D4AA'
        ]),
        textinfo='label+percent',
        textfont=dict(color='#E6EDF3', size=13)
    ))
    fig3.update_layout(
        **CHART_LAYOUT,
        showlegend=True,
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8B949E')
        ),
        annotations=[dict(
            text=f'{total:,}<br>Orders',
            x=0.5, y=0.5,
            font=dict(
                size=14,
                color='#E6EDF3'
            ),
            showarrow=False
        )]
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("### 💰 Revenue by Category (Top 10)")
    rev_data = run_query(QUERIES['revenue_by_category'])
    fig4 = px.bar(
        rev_data,
        x='total_revenue',
        y='category',
        orientation='h',
        color='avg_profit_pct',
        color_continuous_scale=[
            '#0066FF', '#00D4AA'
        ],
        text=rev_data['total_revenue'].apply(
            lambda x: f"${x/1e6:.1f}M"
        )
    )
    fig4.update_traces(textposition='outside')
    fig4.update_layout(
        **CHART_LAYOUT,
        xaxis_title="Revenue ($)",
        yaxis_title="",
        coloraxis_colorbar=dict(
            title="Profit %",
            tickfont=dict(color='#8B949E')
        )
    )
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ── Monthly Trend ───
st.markdown("### 📈 Monthly Performance Trend")
monthly = run_query(QUERIES['monthly_trend'])

fig5 = go.Figure()
fig5.add_trace(go.Scatter(
    x=monthly['month'],
    y=monthly['total_orders'],
    name='Total Orders',
    line=dict(color='#00D4AA', width=2.5),
    fill='tozeroy',
    fillcolor='rgba(0,212,170,0.1)'
))
fig5.add_trace(go.Scatter(
    x=monthly['month'],
    y=monthly['delayed_orders'],
    name='Delayed Orders',
    line=dict(
        color='#FF6B6B', width=2.5,
        dash='dash'
    ),
    fill='tozeroy',
    fillcolor='rgba(255,107,107,0.1)'
))
fig5.add_trace(go.Bar(
    x=monthly['month'],
    y=monthly['monthly_revenue'],
    name='Revenue ($)',
    marker_color='rgba(0,102,255,0.3)',
    yaxis='y2'
))
fig5.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#8B949E'),
    margin=dict(t=30, b=30, l=10, r=10),
    height=400,
    yaxis=dict(
        title='Orders',
        color='#8B949E'
    ),
    yaxis2=dict(
        title='Revenue ($)',
        overlaying='y',
        side='right',
        color='#8B949E'
    ),
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font=dict(color='#8B949E')
    ),
    hovermode='x unified'
)
st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ── Department Performance ──
st.markdown("### 🏢 Department Performance")
dept_data = run_query(QUERIES['department_revenue'])

fig6 = go.Figure()
fig6.add_trace(go.Bar(
    name='Revenue',
    x=dept_data['department'],
    y=dept_data['total_revenue'],
    marker_color='#0066FF',
    text=dept_data['total_revenue'].apply(
        lambda x: f"${x/1e6:.1f}M"
    ),
    textposition='outside'
))
fig6.add_trace(go.Bar(
    name='Profit',
    x=dept_data['department'],
    y=dept_data['total_profit'],
    marker_color='#00D4AA',
    text=dept_data['total_profit'].apply(
        lambda x: f"${x/1e6:.1f}M"
    ),
    textposition='outside'
))
fig6.update_layout(
    **CHART_LAYOUT,
    barmode='group',
    xaxis_title="Department",
    yaxis_title="Amount ($)",
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        font=dict(color='#8B949E')
    )
)
st.plotly_chart(fig6, use_container_width=True)

st.divider()

# ── High Risk Table ──
st.markdown("### 🚨 High Risk Orders — Top 10")
high_risk_data = run_query(QUERIES['high_risk_orders'])

st.dataframe(
    high_risk_data,
    use_container_width=True,
    height=350      
)

st.divider()

# ── Export ───
col_e1, col_e2 = st.columns(2)

with col_e1:
    csv = filtered_orders.to_csv(index=False)
    st.download_button(
        "⬇️ Export Orders Data",
        csv,
        "chainsight_orders.csv",
        "text/csv"
    )

with col_e2:
    risk_csv = filtered_risk.to_csv(index=False)
    st.download_button(
        "⬇️ Export Risk Data",
        risk_csv,
        "chainsight_risk.csv",
        "text/csv"
    )

# ── Footer ──
st.markdown("""
<div style="text-align:center; 
            color:#8B949E; 
            font-size:13px; 
            padding:20px 0;">
    🔗 ChainSight — Supply Chain Intelligence Platform<br>
    Built with Python • SQL • Streamlit • Plotly
</div>
""", unsafe_allow_html=True)