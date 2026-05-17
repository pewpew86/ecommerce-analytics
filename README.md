# ecommerce-analytics
End-to-end e-commerce analytics project using Python, PostgreSQL, and Power BI


# 🛒 E-Commerce Analytics Intelligence System
> **"Why Are We Losing Revenue Despite Growing Orders?"**

A complete end-to-end data analytics project analyzing 100,000+ orders 
from a Brazilian e-commerce platform to diagnose revenue leakage, 
customer retention failure, and operational inefficiencies.

---

## 📌 Project Overview

| Item | Detail |
|------|--------|
| **Dataset** | Olist Brazilian E-Commerce (Kaggle) |
| **Records** | 99,441 orders · 9 relational tables |
| **Period** | September 2016 – October 2018 |
| **Tools** | Python · PostgreSQL · Power BI |
| **Skills** | Data Cleaning · EDA · SQL · RFM Analysis · Dashboard Design |

---

## 🎯 Business Problem

The Head of Growth presents this mandate:

> *"Our order volume grew significantly last quarter, but revenue didn't 
> keep pace. Marketing spend is up. Something is broken — we don't know 
> if it's pricing, customers, logistics, or product mix. Find out."*

---

## 🏗️ Project Architecture

Raw CSVs (9 tables)
↓
Python — Data Audit + Cleaning + Feature Engineering
↓
Master Analytical Table (114,092 rows · 50 columns)
↓
PostgreSQL — 4 Business Views (RFM, KPIs, Delivery, Categories)
↓
Power BI — 4-Page Executive Dashboard
↓
Business Findings Report

---

## 📁 Repository Structure

ecommerce-analytics/
│
├── data/
│   └── raw/                    ← 9 original CSVs (not tracked)
│
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_cleaning_feature_engineering.ipynb
│   └── 03_eda_business_story.ipynb
│
├── sql/
│   └── views_and_queries.sql
│
├── outputs/
│   ├── charts/                 ← 7 EDA charts
│   └── sql_results/            ← 8 query result CSVs
│
├── dashboard/
│   └── ecommerce_dashboard.pbix
│
├── FINDINGS.md
└── README.md

---

## 🔍 Key Findings

### 1. 🚨 Customer Retention Crisis
**96%+ of customers never make a second purchase.**
Cohort retention drops to effectively 0% by Month 2 across all cohorts.
The business is running entirely on new customer acquisition.

### 2. 📦 Delivery Delay Destroys Reviews
| Delivery Timing | Avg Review |
|----------------|-----------|
| Early 10+ days | 4.23 ★ |
| On Time | 4.08 ★ |
| Late 1–5 days | 3.26 ★ |
| Late 5–10 days | 1.83 ★ |
| Late 20+ days | 1.75 ★ |

A 5-day delay cuts review scores by 55%.

### 3. 🗺️ Northeast Brazil Logistics Failure
States AL and MA have late delivery rates exceeding 20% 
vs 9.9% national average. Both are Northeast states with 
weak logistics infrastructure.

### 4. 📊 Freight Margin Risk
21.6% of all items have freight costs exceeding 30% of 
order value — directly compressing margins.

### 5. 💳 Credit Card Dominates Revenue
73.9% of orders use credit card, generating R$14M+ in revenue.
Credit card buyers have highest AOV at R$178 vs voucher at R$130.

---

## 📊 Dashboard Preview

> Power BI dashboard — 4 pages:
> - **Page 1:** Executive Overview (Revenue KPIs, AOV trend, 
>   Category breakdown, Payment mix)
> - **Page 2:** Customer Intelligence (RFM segments, 
>   Retention crisis, Geographic distribution)
> - **Page 3:** Product & Margin (Category profitability, 
>   Freight risk matrix, Review scores)
> - **Page 4:** Operations & Delivery (Late rate by state, 
>   Delivery days, Review correlation)

---

## 🛠️ Tools & Technologies

| Layer | Tool | Purpose |
|-------|------|---------|
| Data Audit | Python (pandas) | Schema analysis, null checks, join integrity |
| Cleaning | Python (pandas, numpy) | Type fixing, deduplication, null handling |
| Feature Engineering | Python | Delivery metrics, RFM features, time features |
| Database | PostgreSQL | Data warehouse, business views |
| EDA | matplotlib, seaborn | 7 analytical charts |
| Dashboard | Power BI | 4-page executive dashboard |

---

## 💡 Business Recommendations

1. **Launch post-purchase loyalty program** targeting At Risk 
   RFM segment — estimated 10-15% win-back potential
2. **Renegotiate logistics SLAs** for AL, MA, SE, CE states — 
   these 4 states disproportionately damage platform reputation
3. **Introduce minimum order values** for high freight ratio 
   categories to protect margins
4. **Shift marketing budget** from pure acquisition to retention — 
   current CAC is unsustainable with 96% one-time buyer rate
5. **Run promotions Monday–Wednesday 10am–3pm** — peak ordering 
   window identified from timing heatmap

---

## 📂 Dataset

Source: [Olist Brazilian E-Commerce — Kaggle]
(https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

> Raw data files are not tracked in this repository.
> Download from Kaggle and place in `/data/raw/`

---

📥 Download Power BI File (.pbix): https://drive.google.com/drive/folders/1pOfNZFZzs1TfTuHsm0_4UJFslBtE2c-P?usp=drive_link 

## 👤 Author: Golam Rabbi 

