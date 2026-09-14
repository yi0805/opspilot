# Task

Task 002 — Business Data Layer

## Goal

Create compact, deterministic synthetic business data and Python query services that a future LLM tool layer can wrap.

## Git context

- **Branch:** `task/002-business-data-layer`
- **Base commit:** `f124f00622dab4f582f417c95316e06c82fe6a15`
- **Final commit:** reported after the completion commit is created
- **Pull request:** none; not opened or pushed

## Data model

- **Product:** unique SKU, name, category, unit price/cost, reorder point, and active status.
- **Sale:** aggregated daily units sold and sale price for one product.
- **Inventory:** one current row per product, with on-hand, reserved, incoming, and update time.
- **Campaign:** product-specific marketing spend, attributed revenue, dates, channel, and status.

All models use the existing SQLAlchemy base and portable SQLAlchemy types compatible with PostgreSQL and SQLite tests.

## Demo dataset

The deterministic dataset contains nine products in Toys, Creative, Educational, Home, and Lifestyle; 27 aggregated sales records; nine inventory positions; and six campaigns. It is wholly synthetic.

Intentional business scenarios:

- `FW-100` Forest Builder Blocks has 310 units of recent sales but only 22 available units against a reorder point of 30.
- `HB-500` Home Base Organizer has only 12 units of sales, with 185 available units against a reorder point of 40.
- Creator Spotlight for `AR-300` returns 3.5000 ROI; Turbo Video Launch and Home Re-engagement have negative ROI.
- Peak Ambassador has zero spend and therefore reports ROI as `None`, avoiding a divide-by-zero result.

## Business query services

`app.services.business_queries` provides ordinary deterministic functions:

- `get_product_details(session, sku)` returns product and gross-margin details.
- `query_sales(session, sku=None, start_date=None, end_date=None)` aggregates units, revenue, and gross profit by product.
- `query_inventory(session, sku=None)` calculates available stock and reorder status.
- `query_campaigns(session, sku=None, status=None)` returns campaign performance with safe ROI handling.

`app.db.seed` provides a rerunnable seed command. It creates the registered business tables for the configured database and inserts the synthetic set only when no products exist.

## Verification

```text
backend> .\.venv\Scripts\python.exe -m pytest
Result: 7 passed, including the existing health endpoint test.

backend> $env:DATABASE_URL = "sqlite:///...temporary database..."; .\.venv\Scripts\python.exe -m app.db.seed
Result: first run seeded synthetic data; second run reported that data already exists.

backend> .\.venv\Scripts\python.exe -c "...business query smoke check..."
Result: retrieved Forest Builder Blocks, 310 units sold, low-stock SKU FW-100, and Turbo Video Launch as the weakest non-zero-spend campaign by ROI.
```

## Known limitations

The following are intentionally not implemented:

- LLM integration
- AI agent
- tool calling
- business recommendation generation
- frontend business UI
- deployment

There are no migrations, API endpoints for the business data, or live external data sources. The seed routine intentionally leaves a database unchanged if any product already exists; it is designed for a fresh local/demo database rather than synchronizing partial datasets.

## Relevant decisions

- Sales remain daily aggregates rather than orders, customers, or payments to keep the demo focused.
- Query calculations are performed in explicit Python functions, so the future tool layer can call them without database-specific SQL aggregates.
- Tests use an isolated in-memory SQLite database and never contact the configured PostgreSQL database.
- `Decimal` monetary values preserve deterministic money and margin calculations.

## Recommended next task

Task 003 — LLM Tool Calling
