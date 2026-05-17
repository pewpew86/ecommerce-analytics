# ============================================================
# NOTEBOOK 3: EDA + BUSINESS STORY
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
import os  # <--- ADD THIS LINE
warnings.filterwarnings('ignore')


pd.set_option('display.float_format', '{:.2f}'.format)

# ============================================================
# LOAD MAT + DEDUPLICATION FIX
# ============================================================

mat = pd.read_csv('data/master_analytical_table.csv', low_memory=False)
mat['order_purchase_timestamp'] = pd.to_datetime(mat['order_purchase_timestamp'])
mat['order_delivered_customer_date'] = pd.to_datetime(mat['order_delivered_customer_date'])

print(f"MAT loaded: {mat.shape}")

# Fix the 667 duplicate review rows
# Keep one row per order_id + order_item_id combination
mat = mat.drop_duplicates(subset=['order_id', 'order_item_id']).copy()
print(f"After dedup: {mat.shape}")

# Working subset — only delivered orders for most analyses
delivered = mat[mat['is_delivered'] == True].copy()
print(f"Delivered orders subset: {len(delivered):,} rows")

# ============================================================
# PLOT SETTINGS
# ============================================================

plt.rcParams.update({
    'figure.dpi'      : 130,
    'axes.spines.top' : False,
    'axes.spines.right': False,
    'axes.titlesize'  : 13,
    'axes.titleweight': 'bold',
    'axes.labelsize'  : 11,
    'xtick.labelsize' : 9,
    'ytick.labelsize' : 9,
    'font.family'     : 'sans-serif'
})
BLUE   = '#2563EB'
RED    = '#DC2626'
GREEN  = '#16A34A'
ORANGE = '#EA580C'
GRAY   = '#6B7280'

os.makedirs('outputs/charts', exist_ok=True)

# ============================================================
# ANALYSIS 1: REVENUE vs ORDER VOLUME DIVERGENCE
# The core business question
# ============================================================

print("\n=== ANALYSIS 1: Revenue vs Order Volume ===")

monthly = (
    delivered.groupby('year_month')
    .agg(
        orders        = ('order_id', 'nunique'),
        revenue       = ('total_payment_value', 'sum'),
        avg_order_val = ('total_payment_value', 'mean'),
        unique_customers = ('customer_unique_id', 'nunique')
    )
    .reset_index()
    .sort_values('year_month')
)

# Remove first and last months (incomplete data)
#monthly = monthly.iloc[1:-1].copy()

#print(monthly[['year_month', 'orders', 'revenue', 'avg_order_val']].to_string(index=False))


# Trim launch noise (first 4 months) and incomplete last month
monthly = monthly.iloc[4:-1].copy()
print(f"Date range after trim: {monthly['year_month'].iloc[0]} → {monthly['year_month'].iloc[-1]}")
print(monthly[['year_month', 'orders', 'revenue', 'avg_order_val']].to_string(index=False))

# Normalize to index 100 for comparison
monthly['orders_idx']  = 100 * monthly['orders']  / monthly['orders'].iloc[0]
monthly['revenue_idx'] = 100 * monthly['revenue'] / monthly['revenue'].iloc[0]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Chart 1a: Indexed growth
ax = axes[0]
ax.plot(monthly['year_month'], monthly['orders_idx'],
        color=BLUE, linewidth=2.5, marker='o', markersize=4, label='Orders')
ax.plot(monthly['year_month'], monthly['revenue_idx'],
        color=RED, linewidth=2.5, marker='o', markersize=4, label='Revenue')
ax.axhline(100, color=GRAY, linestyle='--', linewidth=1)
ax.set_title('Orders vs Revenue Growth (Indexed to 100)')
ax.set_xlabel('Month')
ax.set_ylabel('Index (Base = 100)')
ax.legend()
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Chart 1b: AOV trend
ax = axes[1]
ax.plot(monthly['year_month'], monthly['avg_order_val'],
        color=ORANGE, linewidth=2.5, marker='o', markersize=4)
ax.set_title('Average Order Value Over Time')
ax.set_xlabel('Month')
ax.set_ylabel('AOV (BRL)')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('outputs/charts/01_revenue_vs_orders.png', bbox_inches='tight')
plt.show()
print("✅ Chart 1 saved")

# ============================================================
# ANALYSIS 2: CUSTOMER RETENTION COHORT
# The most powerful single finding in this dataset
# ============================================================

print("\n=== ANALYSIS 2: Customer Retention Cohort ===")

# Get each customer's first purchase month (cohort assignment)
delivered['year_month_dt'] = pd.to_datetime(delivered['year_month'])

first_purchase = (
    delivered.groupby('customer_unique_id')['year_month_dt']
    .min()
    .reset_index()
    .rename(columns={'year_month_dt': 'cohort_month'})
)

delivered_cohort = delivered.merge(first_purchase, on='customer_unique_id')

# Count unique customers per cohort × order month
cohort_data = (
    delivered_cohort.groupby(['cohort_month', 'year_month_dt'])
    ['customer_unique_id'].nunique()
    .reset_index()
    .rename(columns={'customer_unique_id': 'customers'})
)

cohort_data['period_number'] = (
    (cohort_data['year_month_dt'].dt.year  - cohort_data['cohort_month'].dt.year) * 12 +
    (cohort_data['year_month_dt'].dt.month - cohort_data['cohort_month'].dt.month)
)

cohort_pivot = cohort_data.pivot_table(
    index='cohort_month', columns='period_number', values='customers'
)

# Retention rate relative to cohort size (period 0)
cohort_sizes  = cohort_pivot[0]
retention_pct = cohort_pivot.divide(cohort_sizes, axis=0) * 100

# Print retention rates for period 0–6
print("\nRetention % by cohort (Period 0 = acquisition month):")
print(retention_pct[[0,1,2,3,4,5,6]].round(1).to_string())

# Visualize as heatmap
fig, ax = plt.subplots(figsize=(14, 8))
sns.heatmap(
    retention_pct.iloc[:, :12],
    annot=True, fmt='.0f',
    cmap='YlOrRd_r',
    linewidths=0.5,
    ax=ax,
    cbar_kws={'label': 'Retention %'}
)
ax.set_title('Customer Retention Cohort — % Returning Each Month', pad=15)
ax.set_xlabel('Month Since First Purchase')
ax.set_ylabel('Cohort Month')
ax.set_yticklabels([str(d)[:7] for d in retention_pct.index], rotation=0)
plt.tight_layout()
plt.savefig('outputs/charts/02_cohort_retention.png', bbox_inches='tight')
plt.show()

# Key stat — what % of customers are single-purchase?
purchase_counts = (
    delivered.groupby('customer_unique_id')['order_id']
    .nunique()
    .reset_index()
    .rename(columns={'order_id': 'purchase_count'})
)
one_time = (purchase_counts['purchase_count'] == 1).mean() * 100
print(f"\n⚠️  One-time buyers: {one_time:.1f}% of all customers")
print("✅ Chart 2 saved")

# ============================================================
# ANALYSIS 3: PRODUCT CATEGORY PROFITABILITY MATRIX
# ============================================================

print("\n=== ANALYSIS 3: Category Profitability Matrix ===")

category_stats = (
    delivered.groupby('product_category_name_english')
    .agg(
        total_revenue  = ('price', 'sum'),
        avg_price      = ('price', 'mean'),
        avg_freight    = ('freight_value', 'mean'),
        avg_freight_ratio = ('freight_ratio', 'mean'),
        order_count    = ('order_id', 'nunique'),
        avg_review     = ('review_score', 'mean')
    )
    .reset_index()
)

# Filter to categories with meaningful volume
category_stats = category_stats[category_stats['order_count'] >= 50].copy()
category_stats['margin_flag'] = np.where(
    category_stats['avg_freight_ratio'] > 0.30, 'High Freight Risk', 'Healthy Margin'
)

print("\nTop 15 categories by revenue:")
top15 = category_stats.nlargest(15, 'total_revenue')[
    ['product_category_name_english', 'total_revenue',
     'avg_price', 'avg_freight_ratio', 'avg_review', 'margin_flag']
]
print(top15.to_string(index=False))

# Scatter: Revenue vs Freight Ratio — bubble = order volume
fig, ax = plt.subplots(figsize=(13, 8))

colors = [RED if f == 'High Freight Risk' else BLUE
          for f in category_stats['margin_flag']]
sizes  = (category_stats['order_count'] / category_stats['order_count'].max()) * 800

scatter = ax.scatter(
    category_stats['avg_freight_ratio'],
    category_stats['total_revenue'],
    c=colors, s=sizes, alpha=0.7, edgecolors='white', linewidth=0.5
)

# Label top 10 revenue categories
top10 = category_stats.nlargest(10, 'total_revenue')
for _, row in top10.iterrows():
    ax.annotate(
        row['product_category_name_english'],
        (row['avg_freight_ratio'], row['total_revenue']),
        fontsize=7.5, ha='left', va='bottom',
        xytext=(5, 4), textcoords='offset points'
    )

ax.axvline(0.30, color=RED, linestyle='--', linewidth=1.2, alpha=0.7)
ax.text(0.305, ax.get_ylim()[1]*0.95, '30% freight threshold',
        color=RED, fontsize=9)

ax.set_title('Category Profitability Matrix\n(Bubble size = order volume)',
             pad=12)
ax.set_xlabel('Average Freight Ratio (freight / order value)')
ax.set_ylabel('Total Revenue (BRL)')
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f'R${x/1e6:.1f}M')
)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f'{x:.0%}')
)

from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0],[0], marker='o', color='w', markerfacecolor=BLUE,
           markersize=10, label='Healthy Margin'),
    Line2D([0],[0], marker='o', color='w', markerfacecolor=RED,
           markersize=10, label='High Freight Risk (>30%)')
]
ax.legend(handles=legend_elements, loc='upper right')
plt.tight_layout()
plt.savefig('outputs/charts/03_category_profitability.png', bbox_inches='tight')
plt.show()
print("✅ Chart 3 saved")

# ============================================================
# ANALYSIS 4: DELIVERY IMPACT ON REVIEWS
# ============================================================

print("\n=== ANALYSIS 4: Delivery Impact on Review Score ===")

delivery_review = (
    delivered.groupby('delivery_status')
    .agg(
        avg_review    = ('review_score', 'mean'),
        pct_bad       = ('bad_review', 'mean'),
        pct_good      = ('good_review', 'mean'),
        order_count   = ('order_id', 'nunique'),
        avg_delay     = ('delivery_delay_days', 'mean')
    )
    .reset_index()
)
print(delivery_review.round(3).to_string(index=False))

# Delay bins
delivered['delay_bin'] = pd.cut(
    delivered['delivery_delay_days'],
    bins=[-999, -10, -5, 0, 5, 10, 20, 999],
    labels=['Early 10+', 'Early 5-10', 'On Time',
            'Late 1-5d', 'Late 5-10d', 'Late 10-20d', 'Late 20d+']
)

delay_review = (
    delivered.groupby('delay_bin', observed=True)
    .agg(
        avg_review  = ('review_score', 'mean'),
        order_count = ('order_id', 'nunique')
    )
    .reset_index()
)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Chart 4a: Avg review by delay bin
ax = axes[0]
bar_colors = [GREEN if 'Early' in str(b) or b == 'On Time'
              else ORANGE if '1-5' in str(b) or '5-10' in str(b)
              else RED
              for b in delay_review['delay_bin']]
bars = ax.bar(delay_review['delay_bin'], delay_review['avg_review'],
              color=bar_colors, edgecolor='white', linewidth=0.8)
ax.set_title('Avg Review Score by Delivery Timing')
ax.set_xlabel('Delivery Status')
ax.set_ylabel('Avg Review Score')
ax.set_ylim(1, 5.3)
for bar, val in zip(bars, delay_review['avg_review']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
            f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')

# Chart 4b: Order count by delay bin
ax = axes[1]
ax.bar(delay_review['delay_bin'], delay_review['order_count'],
       color=BLUE, alpha=0.8, edgecolor='white')
ax.set_title('Order Volume by Delivery Timing')
ax.set_xlabel('Delivery Status')
ax.set_ylabel('Number of Orders')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')

plt.tight_layout()
plt.savefig('outputs/charts/04_delivery_review_impact.png', bbox_inches='tight')
plt.show()
print("✅ Chart 4 saved")

# ============================================================
# ANALYSIS 5: GEOGRAPHIC REVENUE + LATE DELIVERY HEATMAP
# ============================================================

print("\n=== ANALYSIS 5: Geographic Analysis ===")

state_stats = (
    delivered.groupby('customer_state')
    .agg(
        total_revenue   = ('total_payment_value', 'sum'),
        order_count     = ('order_id', 'nunique'),
        late_rate       = ('is_late', 'mean'),
        avg_review      = ('review_score', 'mean'),
        avg_freight     = ('freight_value', 'mean')
    )
    .reset_index()
    .sort_values('total_revenue', ascending=False)
)

state_stats['revenue_per_order'] = (
    state_stats['total_revenue'] / state_stats['order_count']
)
state_stats['late_rate_pct'] = state_stats['late_rate'] * 100

print("\nAll states — Revenue, Late Rate, Avg Review:")
print(state_stats[[
    'customer_state', 'total_revenue', 'order_count',
    'late_rate_pct', 'avg_review', 'avg_freight'
]].round(2).to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Chart 5a: Revenue by state
ax = axes[0]
top_states = state_stats.head(15)
bars = ax.barh(top_states['customer_state'], top_states['total_revenue'],
               color=BLUE, edgecolor='white')
ax.set_title('Total Revenue by State (Top 15)')
ax.set_xlabel('Revenue (BRL)')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1e6:.1f}M'))
ax.invert_yaxis()

# Chart 5b: Late delivery rate by state — highlight problem states
ax = axes[1]
state_sorted = state_stats.sort_values('late_rate_pct', ascending=False).head(15)
bar_colors_late = [RED if r > 15 else ORANGE if r > 10 else BLUE
                   for r in state_sorted['late_rate_pct']]
ax.barh(state_sorted['customer_state'], state_sorted['late_rate_pct'],
        color=bar_colors_late, edgecolor='white')
ax.axvline(state_stats['late_rate_pct'].mean(), color=GRAY,
           linestyle='--', linewidth=1.5, label=f"Avg: {state_stats['late_rate_pct'].mean():.1f}%")
ax.set_title('Late Delivery Rate by State (Top 15 Worst)')
ax.set_xlabel('Late Delivery Rate (%)')
ax.legend()
ax.invert_yaxis()

plt.tight_layout()
plt.savefig('outputs/charts/05_geographic_analysis.png', bbox_inches='tight')
plt.show()
print("✅ Chart 5 saved")

# ============================================================
# ANALYSIS 6: ORDER TIMING HEATMAP (Marketing Insight)
# ============================================================

print("\n=== ANALYSIS 6: Order Timing Heatmap ===")

timing = (
    delivered.groupby(['order_dayofweek', 'order_hour'])
    ['order_id'].count()
    .reset_index()
    .rename(columns={'order_id': 'order_count'})
)

day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
timing_pivot = timing.pivot(
    index='order_dayofweek', columns='order_hour', values='order_count'
).reindex(day_order)

fig, ax = plt.subplots(figsize=(16, 6))
sns.heatmap(
    timing_pivot,
    cmap='Blues',
    annot=False,
    linewidths=0.3,
    ax=ax,
    cbar_kws={'label': 'Orders'}
)
ax.set_title('Order Volume Heatmap — Day of Week × Hour of Day', pad=12)
ax.set_xlabel('Hour of Day')
ax.set_ylabel('')
plt.tight_layout()
plt.savefig('outputs/charts/06_order_timing_heatmap.png', bbox_inches='tight')
plt.show()
print("✅ Chart 6 saved")

# ============================================================
# ANALYSIS 7: PAYMENT TYPE BEHAVIOR
# ============================================================

print("\n=== ANALYSIS 7: Payment Type Analysis ===")

payment_stats = (
    delivered.groupby('payment_type')
    .agg(
        order_count     = ('order_id', 'nunique'),
        avg_order_value = ('total_payment_value', 'mean'),
        avg_installments = ('payment_installments', 'mean'),
        avg_review      = ('review_score', 'mean'),
        total_revenue   = ('total_payment_value', 'sum')
    )
    .reset_index()
    .sort_values('total_revenue', ascending=False)
)
print(payment_stats.round(2).to_string(index=False))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

ax = axes[0]
ax.bar(payment_stats['payment_type'], payment_stats['avg_order_value'],
       color=[BLUE, ORANGE, GREEN, RED][:len(payment_stats)], edgecolor='white')
ax.set_title('Avg Order Value by Payment Type')
ax.set_ylabel('Avg Order Value (BRL)')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))

ax = axes[1]
ax.bar(payment_stats['payment_type'], payment_stats['total_revenue'],
       color=[BLUE, ORANGE, GREEN, RED][:len(payment_stats)], edgecolor='white')
ax.set_title('Total Revenue by Payment Type')
ax.set_ylabel('Revenue (BRL)')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x/1e6:.1f}M'))

plt.tight_layout()
plt.savefig('outputs/charts/07_payment_analysis.png', bbox_inches='tight')
plt.show()
print("✅ Chart 7 saved")

# ============================================================
# FINAL SUMMARY PRINT — your FINDINGS.md raw material
# ============================================================

print("\n" + "="*55)
print("📊 BUSINESS FINDINGS SUMMARY")
print("="*55)

total_rev    = delivered['total_payment_value'].sum()
total_orders = delivered['order_id'].nunique()
aov          = total_rev / total_orders
late_pct     = delivered['is_late'].mean() * 100
high_fr_pct  = delivered['high_freight_flag'].mean() * 100

print(f"\n  Total Revenue     : R${total_rev:>12,.0f}")
print(f"  Total Orders      : {total_orders:>12,}")
print(f"  Avg Order Value   : R${aov:>12,.2f}")
print(f"  Late Delivery %   : {late_pct:>11.1f}%")
print(f"  High Freight %    : {high_fr_pct:>11.1f}%")
print(f"  Avg Review Score  : {delivered['review_score'].mean():>12.2f}")
print(f"  One-time Buyers   : {one_time:>11.1f}%")
print(f"\n  Worst late states : {state_stats.nlargest(3,'late_rate_pct')['customer_state'].tolist()}")
print(f"  Best revenue state: {state_stats.iloc[0]['customer_state']}")
print(f"\n  Charts saved to: ../outputs/charts/")
print("="*55)