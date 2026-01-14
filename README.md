# Fabric Lakehouse Medallion QuickStart

This QuickStart provides a ready-to-use implementation of the Medallion (Bronze–Silver–Gold) Lakehouse architecture in Microsoft Fabric, designed to help clients rapidly deploy a scalable data lakehouse solution.

## Quick Start

**New to this project?** → Start with **[SETUP.md](SETUP.md)** for detailed step-by-step instructions to get up and running in Fabric.

### Fabric Git Quickstart (connect → sync → run → disconnect)

Use this 5‑minute path to pull the notebook into a new, empty workspace and import the training files.

1. **Create** a new empty Fabric workspace.
2. **Connect the workspace to GitHub**  
   - **Workspace settings → Git integration**  
   - Provider: GitHub  
   - Repo: `bcgov/nr-dap-azure`  
   - Branch: `fabric-lakehouse-medallion-quickstart`  
   - Folder: `bootstrap`
3. **Initial sync**: choose **Git → Workspace** (your workspace is empty).
4. **Run the notebook** `bootstrap/01_import_files_root` → **Run all**  
   - Creates/attaches Lakehouse **`lh_sales_core`**  
   - Copies **text assets** from the branch root into **Lakehouse → Files → `quickstart`**  
   - (Binary files are skipped by default; see SETUP for how to enable them.)
5. **Disconnect Git**  
   - **Workspace settings → Git integration → Disconnect**  
   - Prevents accidental commits back to the repo; your items remain in the workspace.

> **Tip:** If your organization restricts outbound traffic, allow `api.github.com` and `raw.githubusercontent.com` for the one‑time import.  
> **Note:** Lakehouse data (Tables and Files) isn’t tracked in Git; the notebook places assets locally for each learner.

## Project Structure

```
fabric-medallion-quickstart/
├── SETUP.md                          # 👈 START HERE - Detailed setup guide
├── README.md                         # This file - project overview
├── .github                           # CODEOWNERS CODEOWNERS and any workflows
├── bootstrap                         # Fabric‑committed notebook(s) + a lightweight README
│   ├── 01_import_files_root.Notebook # Fabric representation of the notebook item
│   │   ├── .platform                 # Fabric generated platform file
│   │   └── notebook-contents.py      # source (cells + metadata)
│   └── README.md                     # instructions (connect → sync → run → disconnect)
├── docs/                             # Architecture and design documentation
│   ├── architecture.md               # Architecture decisions and patterns
│   └── naming-conventions.md         # Naming standards for Fabric items
├── notebooks/                        # PySpark notebooks for data processing
│   ├── bronze.py                     # Bronze layer: raw data ingestion
│   ├── silver.py                     # Silver layer: data cleansing & conformance
│   └── gold.py                       # Gold layer: business marts & aggregations
├── dq/                               # Data quality validation
│   └── dq_checks.py                  # Quality checks for curated data
├── schemas/                          # SQL schema definitions (for future Warehouse use)
│   ├── create_replication_schema.sql # Create <source>_replication schemas
│   ├── create_reporting_schema.sql   # Create <source>_reporting schemas
│   └── seed_security_examples.sql    # Column-level and row-level security examples
├── samples/                          # Sample data for testing
│   └── customers.csv                 # Sample customer data (6 rows)
├── templates/                        # Copy activity templates for data ingestion
│   ├── copy_oracle.json              # Oracle → Lakehouse Bronze
│   ├── copy_postgresql.json          # PostgreSQL → Lakehouse Bronze
│   ├── copy_s3.json                  # S3 → Lakehouse Bronze
│   ├── copy_api.json                 # REST API → Lakehouse Bronze
│   └── copy_dataverse.json           # Dataverse → Lakehouse Bronze
└── pipeline/                         # Pipeline orchestration
    └── pipeline.json                 # Sample orchestration (reference only)
```

## Architecture Overview

### Medallion Zones

This QuickStart implements a three-tier medallion architecture:

- **Bronze (Replication)** → `<source>_replication` schema
  - Raw data landing zone
  - Append-only writes
  - Schema-on-read
  - Example: `erp_replication.customers_raw`

- **Silver (Reporting)** → `<source>_reporting` schema
  - Cleansed and conformed data
  - Overwrite mode (full refresh)
  - Type conversions, deduplication, standardization
  - Example: `erp_reporting.customers_curated`

- **Gold (Marts)** → `<source>_reporting` schema
  - Business-ready aggregations and metrics
  - Optimized for analytics and reporting
  - Example: `erp_reporting.customer_country_ageband_mart`

### Key Features

- **Delta Lake**: All tables use Delta format for ACID transactions, time travel, and efficient merges
- **Parameterized**: Single `source` parameter controls schema routing
- **Source-Scoped Schemas**: Keep data from different sources logically separated
- **Data Quality**: Built-in validation checks between layers
- **Extensible**: Template-based approach for adding new data sources

## Standard Schemas & Zone Routing

All processing uses **source-scoped schemas** to maintain clear data lineage:

| Zone | Schema Pattern | Purpose | Write Mode |
|------|---------------|---------|------------|
| Bronze | `<source>_replication` | Raw replicated data | Append |
| Silver | `<source>_reporting` | Cleansed conformed data | Overwrite |
| Gold | `<source>_reporting` | Business marts | Overwrite |

**Examples:**
- `erp_replication.customers_raw` (Bronze)
- `erp_reporting.customers_curated` (Silver)
- `crm_replication.accounts_raw` (Bronze)
- `crm_reporting.accounts_curated` (Silver)

### About the SQL Schema Scripts

The `schemas/` folder contains SQL scripts for schema creation. **These scripts are not used in this Lakehouse QuickStart** but are provided for future Warehouse-based implementations where:
- Schemas can be created via T-SQL `CREATE SCHEMA` statements
- Column-level security (CLS) and row-level security (RLS) can be implemented
- SQL-based schema management is preferred

For this Lakehouse QuickStart, schemas are created manually in the Lakehouse UI (see [SETUP.md](SETUP.md) Step 3).

## Getting Started

### Prerequisites
- Microsoft Fabric workspace access (Contributor or Admin)
- Permissions to create Lakehouses and Pipelines
- Basic understanding of PySpark and SQL

**👉 See [SETUP.md](SETUP.md) for complete step-by-step setup instructions**

The setup process uses Git integration to quickly deploy all QuickStart files to your Fabric workspace, then guides you through creating schemas, importing notebooks, and running the medallion pipeline.

## Extending the QuickStart

The QuickStart is designed to be easily extended with additional data sources using the parameterized `source` variable.

### Common Source System Patterns

| Source | Use Case | Example Systems |
|--------|----------|-----------------|
| `erp` | Enterprise Resource Planning | SAP, Oracle ERP, Dynamics 365 |
| `crm` | Customer Relationship Mgmt | Salesforce, Dynamics CRM, HubSpot |
| `mkt` | Marketing Platforms | Marketo, HubSpot, Adobe Campaign |
| `hr` | Human Resources | Workday, ADP, BambooHR |
| `iot` | IoT/Sensor Data | Azure IoT Hub, AWS IoT |
| `pos` | Point of Sale | Square, Toast, Shopify |
| `fin` | Financial Systems | NetSuite, QuickBooks, Xero |

Each source maintains isolated schemas (`{source}_replication` and `{source}_reporting`) for clear data lineage.

**For detailed instructions on adding new sources**, see [SETUP.md - Testing Different Sources](SETUP.md#testing-different-sources)

## Best Practices

### Data Quality
- Run DQ checks after each layer transformation
- Implement both structural and business rule validations
- Log failures for investigation and remediation

### Performance
- Partition large tables by date/region
- Use Z-ordering on frequently filtered columns
- Compact Delta tables regularly (`OPTIMIZE`)

### Security
- Apply column-level security in Warehouse (see `schemas/seed_security_examples.sql`)
- Use row-level security for multi-tenant scenarios
- Implement sensitivity labels for PII/PHI data

### Monitoring
- Track pipeline run durations and row counts
- Set up alerts for failures and data quality issues
- Create operational dashboards for data ops teams

## Documentation

- **[SETUP.md](SETUP.md)** - Step-by-step setup and testing guide
- **[architecture.md](docs/architecture.md)** - Architecture decisions and patterns
- **[naming-conventions.md](docs/naming-conventions.md)** - Naming standards for Fabric items

## Common Use Cases

The QuickStart templates support various data integration scenarios:

- **ERP Integration**: Oracle, SAP, Microsoft Dynamics
- **CRM Replication**: Salesforce, Dynamics 365, Dataverse
- **Cloud Storage**: S3, Azure Data Lake Storage
- **API Integration**: REST APIs, public data sources
- **IoT/Streaming**: Event Hub, Kafka integration patterns

See `templates/` folder for Copy activity reference configurations.

## Support & Resources

- **[SETUP.md](SETUP.md)** - Complete setup guide with troubleshooting
- **Microsoft Fabric Documentation**: https://learn.microsoft.com/fabric/
- **Delta Lake Guide**: https://delta.io/
- **Fabric Community**: https://community.fabric.microsoft.com/

## Contributing

This is a template/quickstart project. Feel free to:
- Adapt naming conventions for your organization
- Add source-specific transformations
- Extend with additional data quality rules
- Implement custom security policies

## License

This template is provided as-is for use with Microsoft Fabric. Adapt as needed for your organization's requirements.

---

**Ready to get started?** → Open **[SETUP.md](SETUP.md)** and follow the step-by-step guide! 🚀
