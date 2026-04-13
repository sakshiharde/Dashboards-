import pandas as pd
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Database Connection ───────────────────────────────────

def get_connection():
    db_path = os.path.join(BASE_DIR, 'chainsight.db')
    conn = sqlite3.connect(db_path)
    return conn

# ── Load Data into SQLite ─────────────────────────────────

def create_database():
    path = os.path.join(
        BASE_DIR, 'Data', 'chainsight_final.csv'
    )
    final_df = pd.read_csv(path)

    conn = get_connection()

    # Teen tables banao
    # Table 1 — Orders (main table)
    orders_cols = [
        'order_id', 'order_date', 'ship_date',
        'actual_shipping_days',
        'scheduled_shipping_days',
        'delivery_status', 'late_delivery_risk',
        'category', 'department', 'market',
        'region', 'country', 'order_status',
        'shipping_mode', 'sales', 'profit_ratio',
        'quantity', 'profit', 'is_delayed'
    ]
    orders_table = final_df[
        [c for c in orders_cols
         if c in final_df.columns]
    ]
    orders_table.to_sql(
        'orders', conn,
        if_exists='replace', index=False
    )
    print(f"✅ Orders table: {orders_table.shape}")

    # Table 2 — Risk Scores
    risk_cols = [
        'order_id', 'risk_score', 'risk_category',
        'delay_score', 'defect_score',
        'status_score', 'lead_score'
    ]
    risk_table = final_df[
        [c for c in risk_cols
         if c in final_df.columns]
    ]
    risk_table.to_sql(
        'risk_scores', conn,
        if_exists='replace', index=False
    )
    print(f"✅ Risk table: {risk_table.shape}")

    # Table 3 — Supplier Performance
    supplier_cols = [
        'order_id', 'category',
        'avg_lead_time', 'avg_defect_rate',
        'supplier_on_time_rate',
        'avg_customer_rating'
    ]
    supplier_table = final_df[
        [c for c in supplier_cols
         if c in final_df.columns]
    ]
    supplier_table.to_sql(
        'supplier_performance', conn,
        if_exists='replace', index=False
    )
    print(f"✅ Supplier table: {supplier_table.shape}")

    conn.close()
    print("\n✅ Database created: chainsight.db")

# ── SQL Queries ───────────────────────────────────────────

def run_query(query):
    conn = get_connection()
    result_df = pd.read_sql_query(query, conn)
    conn.close()
    return result_df

# Business Insight Queries
QUERIES = {

    # KPI 1 — On Time Delivery Rate
    "on_time_rate": """
        SELECT
            ROUND(
                100.0 * SUM(CASE WHEN is_delayed = 0
                            THEN 1 ELSE 0 END)
                / COUNT(*), 2
            ) AS on_time_rate
        FROM orders
    """,

    # KPI 2 — Delay by Region
    "delay_by_region": """
        SELECT
            region,
            COUNT(*) AS total_orders,
            SUM(is_delayed) AS delayed_orders,
            ROUND(
                100.0 * SUM(is_delayed) / COUNT(*), 1
            ) AS delay_rate,
            ROUND(AVG(actual_shipping_days), 1)
                AS avg_shipping_days
        FROM orders
        GROUP BY region
        ORDER BY delay_rate DESC
    """,

    # KPI 3 — Revenue by Category
    "revenue_by_category": """
        SELECT
            category,
            COUNT(*) AS total_orders,
            ROUND(SUM(sales), 2) AS total_revenue,
            ROUND(AVG(profit_ratio) * 100, 1)
                AS avg_profit_pct
        FROM orders
        GROUP BY category
        ORDER BY total_revenue DESC
        LIMIT 10
    """,

    # KPI 4 — High Risk Orders
    "high_risk_orders": """
        SELECT
            o.region,
            o.category,
            COUNT(*) AS high_risk_count,
            ROUND(SUM(o.sales), 2) AS revenue_at_risk
        FROM orders o
        JOIN risk_scores r ON o.order_id = r.order_id
        WHERE r.risk_category = 'High Risk'
        GROUP BY o.region, o.category
        ORDER BY revenue_at_risk DESC
        LIMIT 10
    """,

    # KPI 5 — Monthly Order Trend
    "monthly_trend": """
        SELECT
            SUBSTR(order_date, 1, 7) AS month,
            COUNT(*) AS total_orders,
            SUM(is_delayed) AS delayed_orders,
            ROUND(SUM(sales), 2) AS monthly_revenue
        FROM orders
        GROUP BY month
        ORDER BY month
    """,

    # KPI 6 — Shipping Mode Performance
    "shipping_performance": """
        SELECT
            shipping_mode,
            COUNT(*) AS total_orders,
            SUM(is_delayed) AS delayed_orders,
            ROUND(
                100.0 * SUM(is_delayed) / COUNT(*), 1
            ) AS delay_rate,
            ROUND(AVG(actual_shipping_days), 1)
                AS avg_days
        FROM orders
        GROUP BY shipping_mode
        ORDER BY delay_rate DESC
    """,

    # KPI 7 — Department Revenue
    "department_revenue": """
        SELECT
            department,
            COUNT(*) AS total_orders,
            ROUND(SUM(sales), 2) AS total_revenue,
            ROUND(SUM(profit), 2) AS total_profit
        FROM orders
        GROUP BY department
        ORDER BY total_revenue DESC
    """
}

# ── Test All Queries ──────────────────────────────────────

def test_all_queries():
    print("\n📊 Running SQL Queries...\n")

    for name, query in QUERIES.items():
        result = run_query(query)
        print(f"✅ {name}:")
        print(result.head(3))
        print()

if __name__ == "__main__":
    print("🔄 Creating database...")
    create_database()

    print("\n🔍 Testing queries...")
    test_all_queries()

    print("\n🎉 database.py complete!")