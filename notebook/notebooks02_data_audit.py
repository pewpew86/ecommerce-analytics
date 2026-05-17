
# ============================================================
# NOTEBOOK 2: CLEANING + FEATURE ENGINEERING
# ============================================================

import pandas as pd
import numpy as np
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:.2f}'.format)

# ============================================================
# STEP 1: RELOAD ALL TABLES
# ============================================================

data_path = 'data/raw/'

customers    = pd.read_csv(data_path + 'olist_customers_dataset.csv')
geolocation  = pd.read_csv(data_path + 'olist_geolocation_dataset.csv')
order_items  = pd.read_csv(data_path + 'olist_order_items_dataset.csv')
payments     = pd.read_csv(data_path + 'olist_order_payments_dataset.csv')
reviews      = pd.read_csv(data_path + 'olist_order_reviews_dataset.csv')
orders       = pd.read_csv(data_path + 'olist_orders_dataset.csv')
products     = pd.read_csv(data_path + 'olist_products_dataset.csv')
sellers      = pd.read_csv(data_path + 'olist_sellers_dataset.csv')
category_map = pd.read_csv(data_path + 'product_category_name_translation.csv')

print("✅ All tables reloaded")

# ============================================================
# STEP 2: CLEAN EACH TABLE INDIVIDUALLY
# ============================================================

print("\n--- Cleaning: ORDERS ---")

# Convert all datetime columns
datetime_cols = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date'
]
for col in datetime_cols:
    orders[col] = pd.to_datetime(orders[col], errors='coerce')

# Flag undelivered — DO NOT DROP
orders['is_delivered'] = orders['order_status'] == 'delivered'
orders['is_cancelled'] = orders['order_status'] == 'canceled'

# Drop the 3 not_defined payment rows
payments = payments[payments['payment_type'] != 'not_defined'].copy()
print(f"  Payments after dropping not_defined: {len(payments):,}")

# Clean geolocation — drop duplicates, keep first lat/lng per zip
geo_clean = (
    geolocation
    .drop_duplicates(subset='geolocation_zip_code_prefix', keep='first')
    .rename(columns={
        'geolocation_zip_code_prefix': 'zip_code_prefix',
        'geolocation_lat': 'lat',
        'geolocation_lng': 'lng'
    })
)
print(f"  Geolocation after dedup: {len(geo_clean):,} unique zip codes")

# Clean products — fill nulls
products['product_category_name'] = (
    products['product_category_name'].fillna('unknown')
)
for col in ['product_name_lenght', 'product_description_lenght',
            'product_photos_qty', 'product_weight_g',
            'product_length_cm', 'product_height_cm', 'product_width_cm']:
    products[col] = products[col].fillna(products[col].median())

print(f"  Products nulls remaining: {products.isnull().sum().sum()}")

# Fix 13 unmatched categories — add manual translations
manual_translations = {
    'unknown'                          : 'unknown',
    'pc_gamer'                         : 'pc_gamer',
    'portateis_cozinha_e_preparadores' : 'portable_kitchen_food_preparers',
}
# Merge translation, fill missing with manual map then fallback to raw name
products = products.merge(category_map, on='product_category_name', how='left')
products['product_category_name_english'] = (
    products['product_category_name_english']
    .fillna(products['product_category_name'].map(manual_translations))
    .fillna(products['product_category_name'])  # fallback: use Portuguese name
)
print(f"  Untranslated categories remaining: "
      f"{products['product_category_name_english'].isna().sum()}")

# Reviews — keep only score and order_id, drop comment columns
reviews_clean = reviews[['review_id', 'order_id', 'review_score']].copy()
print(f"  Reviews cleaned: {len(reviews_clean):,} rows")

print("\n✅ Individual table cleaning done")

# ============================================================
# STEP 3: BUILD MASTER ANALYTICAL TABLE (MAT)
# ============================================================
# This is the single table all your SQL and Power BI will use
# Join order: orders → customers → order_items → products → payments → reviews

print("\n--- Building Master Analytical Table ---")

# 3a. orders + customers
mat = orders.merge(customers, on='customer_id', how='left')
print(f"  After orders + customers     : {mat.shape}")

# 3b. + order_items (one row per item, so orders with multiple items expand)
mat = mat.merge(order_items, on='order_id', how='left')
print(f"  After + order_items          : {mat.shape}")

# 3c. + products (for category info)
mat = mat.merge(
    products[['product_id', 'product_category_name_english',
              'product_weight_g', 'product_photos_qty']],
    on='product_id', how='left'
)
print(f"  After + products             : {mat.shape}")

# 3d. + sellers (for seller state — useful for geo analysis)
mat = mat.merge(
    sellers[['seller_id', 'seller_state', 'seller_city']],
    on='seller_id', how='left'
)
print(f"  After + sellers              : {mat.shape}")

# 3e. + payments (aggregate per order first — one row per order)
# Some orders have multiple payment rows (split payments)
payments_agg = payments.groupby('order_id').agg(
    total_payment_value = ('payment_value', 'sum'),
    payment_installments = ('payment_installments', 'max'),
    payment_type         = ('payment_type', 'first')
).reset_index()

mat = mat.merge(payments_agg, on='order_id', how='left')
print(f"  After + payments             : {mat.shape}")

# 3f. + reviews (one review per order)
mat = mat.merge(reviews_clean, on='order_id', how='left')
print(f"  After + reviews              : {mat.shape}")

# ============================================================
# STEP 4: FEATURE ENGINEERING
# ============================================================

print("\n--- Feature Engineering ---")

# -- TIME FEATURES --
mat['order_year']       = mat['order_purchase_timestamp'].dt.year
mat['order_month']      = mat['order_purchase_timestamp'].dt.month
mat['order_month_name'] = mat['order_purchase_timestamp'].dt.strftime('%b')
mat['order_quarter']    = mat['order_purchase_timestamp'].dt.quarter
mat['order_dayofweek']  = mat['order_purchase_timestamp'].dt.day_name()
mat['order_hour']       = mat['order_purchase_timestamp'].dt.hour
mat['year_month']       = mat['order_purchase_timestamp'].dt.to_period('M').astype(str)

# -- DELIVERY FEATURES --
mat['delivery_days'] = (
    mat['order_delivered_customer_date'] - mat['order_purchase_timestamp']
).dt.days

mat['estimated_days'] = (
    mat['order_estimated_delivery_date'] - mat['order_purchase_timestamp']
).dt.days

mat['delivery_delay_days'] = mat['delivery_days'] - mat['estimated_days']

mat['is_late'] = mat['delivery_delay_days'] > 0

mat['delivery_status'] = np.where(
    mat['order_delivered_customer_date'].isna(), 'not_delivered',
    np.where(mat['delivery_delay_days'] <= 0, 'on_time', 'late')
)

# -- REVENUE FEATURES --
mat['item_revenue']   = mat['price'] + mat['freight_value']
mat['freight_ratio']  = mat['freight_value'] / mat['item_revenue'].replace(0, np.nan)
mat['high_freight_flag'] = mat['freight_ratio'] > 0.30

# -- CUSTOMER FEATURES --
# Days since last order (relative to dataset end date)
DATASET_END = pd.Timestamp('2018-10-17')

customer_last_order = (
    mat[mat['is_delivered']]
    .groupby('customer_unique_id')['order_purchase_timestamp']
    .max()
    .reset_index()
    .rename(columns={'order_purchase_timestamp': 'last_order_date'})
)
customer_last_order['recency_days'] = (
    DATASET_END - customer_last_order['last_order_date']
).dt.days

mat = mat.merge(customer_last_order, on='customer_unique_id', how='left')

# -- REVIEW QUALITY FLAG --
mat['bad_review']  = mat['review_score'] <= 2
mat['good_review'] = mat['review_score'] >= 4

# -- ORDER VALUE TIER --
mat['order_value_tier'] = pd.cut(
    mat['total_payment_value'],
    bins=[0, 50, 150, 300, 500, 99999],
    labels=['<50', '50-150', '150-300', '300-500', '500+']
)

print("  ✅ All features engineered")

# ============================================================
# STEP 5: SANITY CHECK ON ENGINEERED FEATURES
# ============================================================

print("\n--- Sanity Checks ---")

print(f"\n  Delivery status breakdown:")
print(mat[mat['is_delivered']]['delivery_status'].value_counts())

print(f"\n  Late delivery rate: "
      f"{mat[mat['is_delivered']]['is_late'].mean()*100:.1f}%")

print(f"\n  Avg delivery days (on-time): "
      f"{mat[mat['delivery_status']=='on_time']['delivery_days'].mean():.1f}")

print(f"\n  Avg delivery days (late): "
      f"{mat[mat['delivery_status']=='late']['delivery_days'].mean():.1f}")

print(f"\n  High freight orders: "
      f"{mat['high_freight_flag'].sum():,} "
      f"({mat['high_freight_flag'].mean()*100:.1f}%)")

print(f"\n  Avg review score: {mat['review_score'].mean():.2f}")

print(f"\n  Order value tier distribution:")
print(mat['order_value_tier'].value_counts().sort_index())

# ============================================================
# STEP 6: SAVE MAT
# ============================================================

output_path = 'data/'
os.makedirs(output_path, exist_ok=True)

mat.to_csv(output_path + 'master_analytical_table.csv', index=False)

print(f"\n{'='*55}")
print(f"✅ MASTER ANALYTICAL TABLE SAVED")
print(f"   Rows    : {mat.shape[0]:,}")
print(f"   Columns : {mat.shape[1]}")
print(f"   Location: /data/master_analytical_table.csv")
print(f"{'='*55}")

# Final column list
print("\nFinal columns in MAT:")
for i, col in enumerate(mat.columns, 1):
    print(f"  {i:>2}. {col}")