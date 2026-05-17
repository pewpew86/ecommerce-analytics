import pandas as pd
from sqlalchemy import create_engine
import psycopg2

# Cleaned password handling configuration
PASSWORD = 'admin123' 

# Step 1: Initialize Database Connection
try:
    conn = psycopg2.connect(
        host='127.0.0.1', port='5432',
        user='postgres', password=PASSWORD,
        database='postgres'
    )
    conn.autocommit = True
    conn.cursor().execute("CREATE DATABASE ecommerce_analytics;")
    conn.close()
    print("✅ Database created")
except Exception as e:
    print(f"✅ Database ready ({e})")

# Step 2: Establish Engine Mapping via IPv4 Loopback
engine = create_engine(
    f'postgresql://postgres:{PASSWORD}@127.0.0.1:5432/ecommerce_analytics'
)

# Step 3: Populate Target Source CSV Files
data_path = 'data/raw/'

files = {
    'customers'             : 'olist_customers_dataset.csv',
    'orders'                : 'olist_orders_dataset.csv',
    'order_items'           : 'olist_order_items_dataset.csv',
    'payments'              : 'olist_order_payments_dataset.csv',
    'reviews'               : 'olist_order_reviews_dataset.csv',
    'products'              : 'olist_products_dataset.csv',
    'sellers'               : 'olist_sellers_dataset.csv',
    'category_map'          : 'product_category_name_translation.csv',
}

for table, filename in files.items():
    df = pd.read_csv(data_path + filename)
    df.to_sql(table, engine, if_exists='replace', index=False)
    print(f"  ✅ {table}: {len(df):,} rows")

# Load Analytical Master Aggregations
mat = pd.read_csv('data/master_analytical_table.csv', low_memory=False)
mat.to_sql('master_analytical_table', engine, if_exists='replace', index=False)
print(f"  ✅ master_analytical_table: {len(mat):,} rows")

print("\n✅ ALL DONE")