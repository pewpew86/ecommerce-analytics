-- VIEW 1: Monthly KPIs
CREATE OR REPLACE VIEW vw_monthly_kpis AS
SELECT
    year_month,
    COUNT(DISTINCT order_id)                    AS total_orders,
    COUNT(DISTINCT customer_unique_id)          AS unique_customers,
    ROUND(SUM(total_payment_value)::numeric, 2) AS gross_revenue,
    ROUND(AVG(total_payment_value)::numeric, 2) AS avg_order_value,
    ROUND(SUM(freight_value)::numeric, 2)       AS total_freight_cost,
    ROUND((AVG(freight_value / NULLIF(price + freight_value,0))*100)::numeric,1)
                                                AS avg_freight_ratio_pct,
    ROUND(AVG(review_score)::numeric, 2)        AS avg_review
FROM master_analytical_table
WHERE is_delivered = TRUE
GROUP BY year_month
ORDER BY year_month;

-- VIEW 2: Category Profitability
CREATE OR REPLACE VIEW vw_category_profitability AS
SELECT
    product_category_name_english AS category,
    COUNT(DISTINCT order_id)      AS total_orders,
    ROUND(SUM(price)::numeric, 2) AS total_revenue,
    ROUND((AVG(freight_value / NULLIF(price + freight_value,0))*100)::numeric,1)
                                  AS avg_freight_ratio_pct,
    ROUND(AVG(review_score)::numeric, 2) AS avg_review,
    CASE
        WHEN AVG(freight_value / NULLIF(price+freight_value,0)) > 0.30
        THEN 'HIGH FREIGHT RISK' ELSE 'Healthy'
    END AS margin_flag
FROM master_analytical_table
WHERE is_delivered = TRUE
GROUP BY product_category_name_english
HAVING COUNT(DISTINCT order_id) >= 50
ORDER BY total_revenue DESC;

-- VIEW 3: State Delivery Performance
CREATE OR REPLACE VIEW vw_state_delivery AS
SELECT
    customer_state                              AS state,
    COUNT(DISTINCT order_id)                    AS total_orders,
    ROUND(AVG(delivery_days)::numeric, 1)       AS avg_delivery_days,
    ROUND(AVG(delivery_delay_days)::numeric, 1) AS avg_delay_days,
    ROUND((100.0 * SUM(CASE WHEN is_late THEN 1 ELSE 0 END)
          / COUNT(*))::numeric, 1)              AS late_rate_pct,
    ROUND(AVG(review_score)::numeric, 2)        AS avg_review
FROM master_analytical_table
WHERE is_delivered = TRUE
  AND delivery_days IS NOT NULL
GROUP BY customer_state
ORDER BY late_rate_pct DESC;

-- VIEW 4: RFM Customer Segmentation
CREATE OR REPLACE VIEW vw_rfm_segments AS
WITH rfm_base AS (
    SELECT
        customer_unique_id,
        MAX(order_purchase_timestamp) AS last_order_date,
        COUNT(DISTINCT order_id)      AS frequency,
        SUM(total_payment_value)      AS monetary
    FROM master_analytical_table
    WHERE is_delivered = TRUE
    GROUP BY customer_unique_id
),
rfm_scored AS (
    SELECT *,
        NTILE(4) OVER (ORDER BY last_order_date DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC)        AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC)         AS m_score
    FROM rfm_base
)
SELECT *,
    CASE
        WHEN r_score = 4 AND f_score >= 3  THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal Customers'
        WHEN r_score = 4 AND f_score = 1   THEN 'New Customers'
        WHEN r_score = 2 AND f_score >= 2  THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Potential Loyalists'
    END AS segment_label
FROM rfm_scored;