import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_clean_data():
    path = os.path.join(
        BASE_DIR, 'Data', 'chainsight_clean.csv'
    )
    clean_df = pd.read_csv(path)
    clean_df['order_date'] = pd.to_datetime(
        clean_df['order_date']
    )
    print(f"✅ Clean data loaded: {clean_df.shape}")
    return clean_df

def fix_columns(clean_df):
    # shipping_mode_x fix karo
    if 'shipping_mode_x' in clean_df.columns:
        clean_df = clean_df.rename(
            columns={'shipping_mode_x': 'shipping_mode'}
        )
    if 'shipping_mode_y' in clean_df.columns:
        clean_df = clean_df.drop(
            columns=['shipping_mode_y']
        )
    if 'shipping_mode_key' in clean_df.columns:
        clean_df = clean_df.drop(
            columns=['shipping_mode_key']
        )
    print(f"✅ Columns fixed: {clean_df.shape}")
    return clean_df

def calculate_risk_score(clean_df):
    """
    Risk Score = weighted combination of:
    Delay Risk         40%
    Supplier Defect    30%
    Delivery Status    20%
    Lead Time          10%
    """
    risk_df = clean_df.copy()

    # ── Factor 1: Delay Score (40%) ───────────────────────
    max_days = risk_df['actual_shipping_days'].max()
    risk_df['delay_score'] = (
        risk_df['actual_shipping_days'] /
        max_days * 100
    ).fillna(50)

    # ── Factor 2: Defect Score (30%) ─────────────────────
    max_defect = risk_df['avg_defect_rate'].max()
    risk_df['defect_score'] = (
        risk_df['avg_defect_rate'] /
        max_defect * 100
    ).fillna(50)

    # ── Factor 3: Delivery Status Score (20%) ────────────
    status_map = {
        'Shipping on time': 10,
        'Advance shipping': 5,
        'Late delivery': 80,
        'Shipping canceled': 100
    }
    risk_df['status_score'] = risk_df[
        'delivery_status'
    ].map(status_map).fillna(50)

    # ── Factor 4: Lead Time Score (10%) ──────────────────
    max_lead = risk_df['avg_lead_time'].max()
    risk_df['lead_score'] = (
        risk_df['avg_lead_time'] /
        max_lead * 100
    ).fillna(50)

    # ── Final Weighted Risk Score ─────────────────────────
    risk_df['risk_score'] = (
        risk_df['delay_score']  * 0.40 +
        risk_df['defect_score'] * 0.30 +
        risk_df['status_score'] * 0.20 +
        risk_df['lead_score']   * 0.10
    ).round(2)

    # ── Risk Category ─────────────────────────────────────
    risk_df['risk_category'] = pd.cut(
        risk_df['risk_score'],
        bins=[0, 30, 60, 100],
        labels=['Low Risk', 'Medium Risk', 'High Risk']
    )

    print("✅ Risk scores calculated!")
    print(risk_df['risk_category'].value_counts())
    return risk_df

def calculate_kpis(risk_df):
    """Business KPIs calculate karo"""

    total_orders = len(risk_df)

    on_time_rate = round(
        100 - (risk_df['is_delayed'].sum() /
        total_orders * 100), 2
    )

    avg_shipping_days = round(
        risk_df['actual_shipping_days'].mean(), 1
    )

    revenue_at_risk = round(
        risk_df[
            risk_df['risk_category'] == 'High Risk'
        ]['sales'].sum(), 2
    )

    total_revenue = round(risk_df['sales'].sum(), 2)

    high_risk_orders = len(
        risk_df[risk_df['risk_category'] == 'High Risk']
    )

    kpis = {
        'total_orders': total_orders,
        'on_time_rate': on_time_rate,
        'avg_shipping_days': avg_shipping_days,
        'revenue_at_risk': revenue_at_risk,
        'total_revenue': total_revenue,
        'high_risk_orders': high_risk_orders
    }

    print("\n🎯 KPIs:")
    for key, value in kpis.items():
        print(f"   {key}: {value}")

    return kpis

def save_final_data(risk_df):
    path = os.path.join(
        BASE_DIR, 'Data', 'chainsight_final.csv'
    )
    risk_df.to_csv(path, index=False)
    print(f"\n✅ Final data saved: {path}")

if __name__ == "__main__":
    print("🔄 Loading clean data...")
    clean_df = load_clean_data()

    print("\n🔧 Fixing columns...")
    clean_df = fix_columns(clean_df)

    print("\n⚡ Calculating risk scores...")
    risk_df = calculate_risk_score(clean_df)

    print("\n📊 Calculating KPIs...")
    kpis = calculate_kpis(risk_df)

    print("\n💾 Saving final data...")
    save_final_data(risk_df)

    print("\n🎉 features.py complete!")