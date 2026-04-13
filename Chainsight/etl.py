import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Load Functions ────────────────────────────────────────

def load_orders():
    path = os.path.join(
        BASE_DIR, 'Data',
        'DataCoSupplyChainDataset.csv'
    )
    orders_df = pd.read_csv(path, encoding='latin-1')
    print(f"Orders loaded: {orders_df.shape}")
    return orders_df

def load_suppliers():
    path = os.path.join(
        BASE_DIR, 'Data',
        'Procurement KPI Analysis Dataset.csv'
    )
    suppliers_df = pd.read_csv(path, encoding='latin-1')
    print(f"Suppliers loaded: {suppliers_df.shape}")
    return suppliers_df

def load_shipments():
    path = os.path.join(
        BASE_DIR, 'Data', 'Train.csv'
    )
    shipments_df = pd.read_csv(path, encoding='latin-1')
    print(f"Shipments loaded: {shipments_df.shape}")
    return shipments_df

# ── Clean Functions ───────────────────────────────────────

def clean_orders(orders_df):
    cols = [
        'Order Id', 'order date (DateOrders)',
        'shipping date (DateOrders)',
        'Days for shipping (real)',
        'Days for shipment (scheduled)',
        'Delivery Status', 'Late_delivery_risk',
        'Category Name', 'Department Name',
        'Market', 'Order Region', 'Order Country',
        'Order Status', 'Shipping Mode',
        'Sales', 'Order Item Profit Ratio',
        'Order Item Quantity', 'Order Profit Per Order'
    ]
    orders_clean = orders_df[cols].copy()

    orders_clean.columns = [
        'order_id', 'order_date', 'ship_date',
        'actual_shipping_days',
        'scheduled_shipping_days',
        'delivery_status', 'late_delivery_risk',
        'category', 'department',
        'market', 'region', 'country',
        'order_status', 'shipping_mode',
        'sales', 'profit_ratio',
        'quantity', 'profit'
    ]

    # Date conversion
    orders_clean['order_date'] = pd.to_datetime(
        orders_clean['order_date'], errors='coerce'
    )
    orders_clean['ship_date'] = pd.to_datetime(
        orders_clean['ship_date'], errors='coerce'
    )

    # Delay flag
    orders_clean['is_delayed'] = (
        orders_clean['actual_shipping_days'] >
        orders_clean['scheduled_shipping_days']
    ).astype(int)

    # Drop nulls
    orders_clean = orders_clean.dropna(subset=[
        'order_date', 'sales', 'shipping_mode'
    ])

    print(f"✅ Orders cleaned: {orders_clean.shape}")
    return orders_clean


def clean_suppliers(suppliers_df):
    suppliers_clean = suppliers_df.copy()
    suppliers_clean.columns = (
        suppliers_clean.columns
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
    )

    suppliers_clean['order_date'] = pd.to_datetime(
        suppliers_clean['order_date'], errors='coerce'
    )
    suppliers_clean['delivery_date'] = pd.to_datetime(
        suppliers_clean['delivery_date'], errors='coerce'
    )

    # Lead time
    suppliers_clean['lead_time_days'] = (
        suppliers_clean['delivery_date'] -
        suppliers_clean['order_date']
    ).dt.days

    # Defect rate
    suppliers_clean['defect_rate'] = (
        suppliers_clean['defective_units'] /
        suppliers_clean['quantity'].replace(0, 1) * 100
    ).round(2)

    # On time flag
    suppliers_clean['on_time'] = (
        suppliers_clean['order_status'] ==
        'Delivered on time'
    ).astype(int)

    suppliers_clean = suppliers_clean.dropna(
        subset=['supplier', 'lead_time_days']
    )

    print(f"✅ Suppliers cleaned: {suppliers_clean.shape}")
    return suppliers_clean


def clean_shipments(shipments_df):
    shipments_clean = shipments_df.copy()
    shipments_clean.columns = (
        shipments_clean.columns
        .str.strip()
        .str.lower()
        .str.replace('.', '_')
        .str.replace(' ', '_')
    )

    shipments_clean = shipments_clean.rename(columns={
        'reached_on_time_y_n': 'reached_on_time',
        'weight_in_gms': 'weight_gms',
        'mode_of_shipment': 'shipping_mode'
    })

    shipments_clean['weight_kg'] = (
        shipments_clean['weight_gms'] / 1000
    ).round(2)

    shipments_clean = shipments_clean.dropna(
        subset=['shipping_mode', 'weight_gms']
    )

    print(f"✅ Shipments cleaned: {shipments_clean.shape}")
    return shipments_clean


# ── Merge Function ────────────────────────────────────────

def merge_datasets(orders_clean, 
                   shipments_clean, 
                   suppliers_clean):

    # Step 1 — Shipment stats by shipping mode
    shipment_stats = shipments_clean.groupby(
        'shipping_mode'
    ).agg(
        avg_weight_kg=('weight_kg', 'mean'),
        avg_customer_rating=('customer_rating', 'mean'),
        on_time_rate=('reached_on_time', 'mean'),
        avg_discount=('discount_offered', 'mean')
    ).reset_index()

    # Standardize keys
    orders_clean['shipping_mode_key'] = (
        orders_clean['shipping_mode']
        .str.strip().str.title()
    )
    shipment_stats['shipping_mode_key'] = (
        shipment_stats['shipping_mode']
        .str.strip().str.title()
    )

    # Merge 1
    merged_df = orders_clean.merge(
        shipment_stats,
        on='shipping_mode_key',
        how='left'
    )
    print(f"After merge 1: {merged_df.shape}")

    # Step 2 — Supplier stats by category
    supplier_stats = suppliers_clean.groupby(
        'item_category'
    ).agg(
        avg_lead_time=('lead_time_days', 'mean'),
        avg_defect_rate=('defect_rate', 'mean'),
        supplier_on_time_rate=('on_time', 'mean')
    ).reset_index()

    supplier_stats = supplier_stats.rename(
        columns={'item_category': 'category'}
    )

    # Merge 2
    merged_df = merged_df.merge(
        supplier_stats,
        on='category',
        how='left'
    )
    print(f"After merge 2: {merged_df.shape}")

    # Fill nulls with median
    fill_cols = [
        'avg_weight_kg', 'avg_customer_rating',
        'on_time_rate', 'avg_lead_time',
        'avg_defect_rate', 'supplier_on_time_rate'
    ]
    for col in fill_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna(
                merged_df[col].median()
            )

    print(f"✅ Final merged: {merged_df.shape}")
    return merged_df


# ── Save ──────────────────────────────────────────────────

def save_clean_data(merged_df):
    output_path = os.path.join(
        BASE_DIR, 'Data', 'chainsight_clean.csv'
    )
    merged_df.to_csv(output_path, index=False)
    print(f"✅ Saved: {output_path}")


# ── Main ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔄 Loading...")
    orders_df = load_orders()
    suppliers_df = load_suppliers()
    shipments_df = load_shipments()

    print("\n🧹 Cleaning...")
    orders_clean = clean_orders(orders_df)
    suppliers_clean = clean_suppliers(suppliers_df)
    shipments_clean = clean_shipments(shipments_df)

    print("\n🔗 Merging...")
    merged_df = merge_datasets(
        orders_clean,
        shipments_clean,
        suppliers_clean
    )

    print("\n💾 Saving...")
    save_clean_data(merged_df)

    print("\n🎯 Final Info:")
    print(merged_df.shape)
    print(merged_df.columns.tolist())