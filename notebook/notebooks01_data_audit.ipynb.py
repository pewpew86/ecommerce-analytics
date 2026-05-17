
# ============================================================
# NOTEBOOK 1: DATA AUDIT
# Ecommerce Analytics Project
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.float_format', '{:.2f}'.format)

# ============================================================
# STEP 1: LOAD ALL 9 TABLES
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

all_tables = {
    'customers'   : customers,
    'geolocation' : geolocation,
    'order_items' : order_items,
    'payments'    : payments,
    'reviews'     : reviews,
    'orders'      : orders,
    'products'    : products,
    'sellers'     : sellers,
    'category_map': category_map
}

print("✅ All 9 tables loaded successfully\n")

# ============================================================
# STEP 2: AUDIT FUNCTION — run on every table
# ============================================================

def audit_table(df, name):
    print("=" * 55)
    print(f"TABLE: {name.upper()}")
    print("=" * 55)
    print(f"  Rows       : {df.shape[0]:,}")
    print(f"  Columns    : {df.shape[1]}")
    print(f"  Duplicates : {df.duplicated().sum():,}")
    
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls) > 0:
        print(f"\n  ⚠️  NULL columns:")
        for col, count in nulls.items():
            pct = 100 * count / len(df)
            print(f"     {col}: {count:,} ({pct:.1f}%)")
    else:
        print("  ✅ No nulls found")
    
    print(f"\n  Column types:")
    for col, dtype in df.dtypes.items():
        print(f"     {col}: {dtype}")
    print()

for name, df in all_tables.items():
    audit_table(df, name)

# ============================================================
# STEP 3: RELATIONSHIP CHECK — are the joins valid?
# ============================================================

print("\n" + "=" * 55)
print("RELATIONSHIP / JOIN INTEGRITY CHECKS")
print("=" * 55)

# orders ↔ customers
matched = orders['customer_id'].isin(customers['customer_id']).sum()
print(f"\norders → customers match  : {matched:,} / {len(orders):,}")

# order_items ↔ orders
matched = order_items['order_id'].isin(orders['order_id']).sum()
print(f"order_items → orders match: {matched:,} / {len(order_items):,}")

# payments ↔ orders
matched = payments['order_id'].isin(orders['order_id']).sum()
print(f"payments → orders match   : {matched:,} / {len(payments):,}")

# reviews ↔ orders
matched = reviews['order_id'].isin(orders['order_id']).sum()
print(f"reviews → orders match    : {matched:,} / {len(reviews):,}")

# order_items ↔ products
matched = order_items['product_id'].isin(products['product_id']).sum()
print(f"order_items → products    : {matched:,} / {len(order_items):,}")

# order_items ↔ sellers
matched = order_items['seller_id'].isin(sellers['seller_id']).sum()
print(f"order_items → sellers     : {matched:,} / {len(order_items):,}")

# products ↔ category_map
matched = products['product_category_name'].isin(
    category_map['product_category_name']
).sum()
unmatched = products['product_category_name'].notna().sum() - matched
print(f"products → category_map   : {matched:,} matched, {unmatched:,} unmatched")

# ============================================================
# STEP 4: ORDER STATUS BREAKDOWN
# ============================================================

print("\n" + "=" * 55)
print("ORDER STATUS BREAKDOWN")
print("=" * 55)
status = orders['order_status'].value_counts()
for s, count in status.items():
    pct = 100 * count / len(orders)
    print(f"  {s:<30} {count:>7,}  ({pct:.1f}%)")

# ============================================================
# STEP 5: DATE COLUMN CHECK
# ============================================================

print("\n" + "=" * 55)
print("DATE RANGE CHECK")
print("=" * 55)

date_cols = [
    'order_purchase_timestamp',
    'order_approved_at',
    'order_delivered_carrier_date',
    'order_delivered_customer_date',
    'order_estimated_delivery_date'
]

for col in date_cols:
    temp = pd.to_datetime(orders[col], errors='coerce')
    print(f"\n  {col}")
    print(f"    Min  : {temp.min()}")
    print(f"    Max  : {temp.max()}")
    print(f"    NULLs: {temp.isna().sum():,}")

# ============================================================
# STEP 6: PAYMENT TYPE BREAKDOWN
# ============================================================

print("\n" + "=" * 55)
print("PAYMENT TYPE BREAKDOWN")
print("=" * 55)
pay = payments['payment_type'].value_counts()
for p, count in pay.items():
    pct = 100 * count / len(payments)
    print(f"  {p:<25} {count:>7,}  ({pct:.1f}%)")

# ============================================================
# STEP 7: PRICE & FREIGHT QUICK STATS
# ============================================================

print("\n" + "=" * 55)
print("PRICE & FREIGHT STATS")
print("=" * 55)
print(order_items[['price', 'freight_value']].describe().round(2))

# ============================================================
# STEP 8: REVIEW SCORE DISTRIBUTION
# ============================================================

print("\n" + "=" * 55)
print("REVIEW SCORE DISTRIBUTION")
print("=" * 55)
rev = reviews['review_score'].value_counts().sort_index()
for score, count in rev.items():
    pct = 100 * count / len(reviews)
    bar = '█' * int(pct)
    print(f"  {score} ⭐  {count:>7,}  ({pct:.1f}%)  {bar}")

# ============================================================
# STEP 9: TOP 10 PRODUCT CATEGORIES (before translation)
# ============================================================

print("\n" + "=" * 55)
print("TOP 10 PRODUCT CATEGORIES")
print("=" * 55)
cat = products['product_category_name'].value_counts().head(10)
for c, count in cat.items():
    print(f"  {str(c):<40} {count:>5,}")

# ============================================================
# STEP 10: SAVE AUDIT SUMMARY TO FILE
# ============================================================

summary = []
for name, df in all_tables.items():
    summary.append({
        'table'         : name,
        'rows'          : df.shape[0],
        'columns'       : df.shape[1],
        'duplicates'    : df.duplicated().sum(),
        'null_columns'  : df.isnull().any().sum(),
        'total_nulls'   : df.isnull().sum().sum()
    })

summary_df = pd.DataFrame(summary)
summary_df.to_csv('data/audit_summary.csv', index=False)
print("\n" + "=" * 55)
print("✅ AUDIT COMPLETE")
print("   audit_summary.csv saved to /data/")
print("=" * 55)
print("\nSummary:")
print(summary_df.to_string(index=False))                                                                                             