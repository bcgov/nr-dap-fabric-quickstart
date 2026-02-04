# Naming Conventions

## Workspaces & Items
- Workspaces: `<ministry acronym>_<group/project name>_<environment>` (e.g., `ECS_CTHUB_Prod`, `AF_BRM_NonProd`, `FOR_ADMO_Test`, `FOR_BCTS_Dev`)
- Lakehouse: `lh_<domain>_<purpose>` (e.g., `quickstart_lh`, `lh_finance_reporting`)
- Warehouse: `wh_<domain>_<purpose>` (e.g., `wh_sales_gold`)

## Schemas
- Replication schema: `<source>_replication` (e.g., `erp_replication`)
- Reporting schema: `<source>_reporting` (e.g., `erp_reporting`)

## Tables
- Raw landing (Bronze): `<subject>_raw` (e.g., `customers_raw`)
- Curated (Silver): `<subject>_curated` (e.g., `customers_curated`)
- Marts (Gold): `<subject>_<grain>_mart` (e.g., `customer_country_ageband_mart`)

## Pipelines
- `pl_<source>_to_<target>_<zone>` (e.g., `pl_oracle_to_lakehouse_bronze`)
- Parameterized copies: `pl_<source>_replication_copy`

## Notebooks
- `nb_bronze_<source>_<subject>.py`, `nb_silver_<subject>.py`, `nb_gold_<mart>.py`

## Columns
- Timestamps: `created_ts`, `updated_ts`, `_ingest_ts` (service columns prefixed with `_`)
