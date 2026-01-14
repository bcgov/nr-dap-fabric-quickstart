# Fabric Lakehouse Medallion QuickStart - Setup Guide

This guide will walk you through setting up and testing the medallion lakehouse architecture in Microsoft Fabric.

## Prerequisites

- Access to a Microsoft Fabric workspace with contributor or admin rights
- Permissions to create Lakehouse and Pipeline items
- Basic familiarity with Fabric interface

## Architecture Overview

This QuickStart implements a medallion lakehouse architecture with three zones:
- **Bronze (Replication)**: Raw data landing zone (`<source>_replication` schema)
- **Silver (Reporting)**: Cleansed and conformed data (`<source>_reporting` schema)
- **Gold (Marts)**: Business-ready aggregations (`<source>_reporting` schema)

## Step-by-Step Setup

### Step 1: Git QuickStart - Import Files to Workspace

Use this workflow to connect your Fabric workspace to GitHub and import the QuickStart files.

1. **Create a new empty Fabric workspace** (or use an existing one)

2. **Connect the workspace to GitHub**:
   - Create personal access token on GitHub: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic
   - Navigate to **Workspace settings → Git integration**
   - Provider: **GitHub**
   - Repository: `bcgov/nr-dap-azure`
   - Branch: `fabric-lakehouse-medallion-quickstart`

3. **Initial sync**:
   - Choose **Git → Workspace** (your workspace is empty)
   - This imports the bootstrap notebook

4. **Disconnect Git** (recommended):
   - Go to **Workspace settings → Git integration → Disconnect**
   - This prevents accidental commits back to the repo
   - Your workspace items remain intact and ready to use

5. **Run the bootstrap notebook**:
   - Open `bootstrap/01_import_files_root`
   - Click **Run all**
   - The notebook will:
     - Create and attach Lakehouse `lh_sales_core`
     - Copy all QuickStart files from the branch root to **Lakehouse → Files → `quickstart`**
     - This includes notebooks, sample data, templates, and documentation


**Verify**: 
- Lakehouse `lh_sales_core` exists in your workspace
- Files are visible under **Lakehouse → Files → quickstart** folder

**Note**: If your organization restricts outbound traffic, allow `api.github.com` and `raw.githubusercontent.com` for the one-time import.

### Step 2: Create Database Schemas in Lakehouse

Schemas must be created in your Lakehouse before running notebooks. Create them manually using the Lakehouse UI:

1. Open your Lakehouse (`lh_sales_core`)
2. In the Lakehouse Explorer (left panel), find the **Schemas** section
3. Right-click on **Schemas** → **New schema**
4. Create schema: `erp_replication`
5. Right-click on **Schemas** → **New schema** again
6. Create schema: `erp_reporting`

**Verify**: You should see both `erp_replication` and `erp_reporting` schemas listed under the Schemas section in your Lakehouse.

**Important Notes:**
- Lakehouse SQL analytics endpoint does **NOT** support `CREATE SCHEMA` SQL statements
- Schemas are **NOT** automatically created by `.saveAsTable()` - they must exist before notebooks run
- All schemas must be created manually through the Lakehouse UI before running any notebooks

### Step 3: Upload Notebooks

1. **Navigate to your workspace** (not inside the Lakehouse)
2. Click **+ New** → **Notebook**
3. For each Python file in the `notebooks/` folder:
   - Create a new notebook
   - Name it appropriately:
     - `nb_bronze_erp_customers` for bronze.py
     - `nb_silver_erp_customers` for silver.py
     - `nb_gold_customer_marts` for gold.py
   - Delete the default empty cell
   - Copy the entire contents of the .py file
   - Paste into a new code cell
   - Make sure to **attach the notebook to your Lakehouse** (`lh_sales_core`):
     - Click **Add** under Lakehouses in the left panel
     - Select **Existing lakehouse**
     - Choose `lh_sales_core`

4. **Create Data Quality Notebook**
   - Create another notebook
   - Name it: `nb_dq_checks`
   - Copy contents from `dq/dq_checks.py`
   - Attach to `lh_sales_core`

**Note**: The notebooks are parameterized with a `source` parameter (default: 'erp'). When running from the pipeline, this parameter will be passed automatically.

### Step 4: Manual Testing (Run Notebooks Individually)

Before setting up the pipeline, test each notebook manually:

1. **Run Bronze Notebook** (`nb_bronze_erp_customers`)
   - Click **Run all**
   - Expected output: "Bronze table written: erp_replication.customers_raw"
   - Verify: Query the table:
     ```python
     display(spark.table("erp_replication.customers_raw"))
     ```

2. **Run Silver Notebook** (`nb_silver_erp_customers`)
   - Click **Run all**
   - Expected output: "Silver table written: erp_reporting.customers_curated"
   - Verify: Query the table:
     ```python
     display(spark.table("erp_reporting.customers_curated"))
     ```

3. **Run Gold Notebook** (`nb_gold_customer_marts`)
   - Click **Run all**
   - Expected output: "Gold table written: erp_reporting.customer_country_ageband_mart"
   - Verify: Query the table:
     ```python
     display(spark.table("erp_reporting.customer_country_ageband_mart"))
     ```

4. **Run DQ Checks** (`nb_dq_checks`)
   - Click **Run all**
   - Expected output: "Data quality checks passed."

**Note**: The changes from Bronze to Silver are almost invisible. Pay attention to `age` column. Notice `ABC` in Bronze `age` column and `123` in Silver `age` column.

**Important - Bronze Append Behavior**: Bronze uses append mode, so running the Bronze notebook multiple times will duplicate data (e.g., running manually then via pipeline will result in 12 rows instead of 6). This is expected behavior for an append-only audit trail. Silver handles deduplication, so you'll still see only 6 unique records in the curated table.

### Step 5: Create the Pipeline (Optional - for Orchestration)

1. **Navigate to your workspace**
2. Click **+ New** → **Data pipeline**
3. Name it: `pl_bronze_silver_gold`
4. **Add Notebook Activities**:
   
   **Activity 1 - Bronze**:
   - Drag **Notebook** activity onto canvas
   - Name: `Bronze`
   - Settings tab:
     - Notebook: Select `nb_bronze_erp_customers`
     - Parameters: Add parameter `source` with value `erp`
   
   **Activity 2 - Silver**:
   - Drag another **Notebook** activity
   - Name: `Silver`
   - Settings tab:
     - Notebook: Select `nb_silver_erp_customers`
     - Parameters: Add parameter `source` with value `erp`
   - General tab:
     - Add dependency: Select `Bronze` (click the green box on Bronze activity and drag to Silver)
   
   **Activity 3 - Gold**:
   - Drag another **Notebook** activity
   - Name: `Gold`
   - Settings tab:
     - Notebook: Select `nb_gold_customer_marts`
     - Parameters: Add parameter `source` with value `erp`
   - General tab:
     - Add dependency: Select `Silver`
   
   **Activity 4 - DQ Checks**:
   - Drag another **Notebook** activity
   - Name: `DQ_Checks`
   - Settings tab:
     - Notebook: Select `nb_dq_checks`
     - Parameters: Add parameter `source` with value `erp`
   - General tab:
     - Add dependency: Select `Gold`

5. **Save the pipeline**
6. Click **Run** to test the full orchestration

### Step 6: Verify Results

After the pipeline completes (or after manual runs):

1. **Check Bronze Table**:
   ```sql
   SELECT * FROM erp_replication.customers_raw;
   ```
   Should show 6 rows (12 rown if pipeline and manual process were run) with raw customer data plus `_ingest_ts` column

2. **Check Silver Table**:
   ```sql
   SELECT * FROM erp_reporting.customers_curated;
   ```
   Should show 6 rows with cleaned data (uppercase countries, trimmed names, typed age)

3. **Check Gold Mart**:
   ```sql
   SELECT * FROM erp_reporting.customer_country_ageband_mart
   ORDER BY country, age_band;
   ```
   Should show aggregated customer counts by country and age band

## Testing Different Sources

The QuickStart is parameterized to support multiple data sources using the `source` parameter. This parameter automatically routes data to the correct schemas.

### Understanding the Source Parameter

The `source` parameter (default: `'erp'`) controls schema naming throughout the entire pipeline:
- **Bronze writes to**: `{source}_replication` schema
- **Silver/Gold write to**: `{source}_reporting` schema

**ERP** in this context stands for **Enterprise Resource Planning** systems (like SAP, Oracle ERP, Microsoft Dynamics) - used as the default example source.

### Source Parameter Examples

Here are common source system patterns you can use:

| Source Value | Use Case | Example Systems | Replication Schema | Reporting Schema |
|--------------|----------|-----------------|-------------------|------------------|
| `erp` | Enterprise Resource Planning | SAP, Oracle ERP, Dynamics 365 F&O | `erp_replication` | `erp_reporting` |
| `crm` | Customer Relationship Management | Salesforce, Dynamics 365 CRM, HubSpot | `crm_replication` | `crm_reporting` |
| `mkt` | Marketing Platforms | Marketo, HubSpot, Adobe Campaign | `mkt_replication` | `mkt_reporting` |
| `hr` | Human Resources Systems | Workday, ADP, BambooHR | `hr_replication` | `hr_reporting` |
| `iot` | IoT/Sensor Data | Azure IoT Hub, AWS IoT | `iot_replication` | `iot_reporting` |
| `pos` | Point of Sale Systems | Square, Toast, Shopify POS | `pos_replication` | `pos_reporting` |
| `fin` | Financial Systems | NetSuite, QuickBooks, Xero | `fin_replication` | `fin_reporting` |
| `wms` | Warehouse Management | Manhattan, SAP EWM | `wms_replication` | `wms_reporting` |

### How to Test with a Different Source

To add additional data sources beyond the sample ERP data:

1. **Create source-specific schemas** in Lakehouse UI:
   - Open your Lakehouse
   - Right-click on **Schemas** → **New schema** → Create `{source}_replication`
   - Right-click on **Schemas** → **New schema** → Create `{source}_reporting`
   - Replace `{source}` with your source name (e.g., `crm`, `mkt`, `hr`)

2. **Prepare your source data**:
   - Upload your data file to Lakehouse Files (similar to Step 2)
   - Or configure a copy template from `templates/` folder to connect directly to your source system

3. **Update notebooks**:
   - Modify Bronze notebook to point to your new data source
   - Update the `source` parameter to match your schema naming (e.g., `source = 'crm'`)

4. **Run the pipeline** with the new source parameter, and the medallion pattern will process your data through Bronze → Silver → Gold using the appropriate schemas.

### Running Multiple Sources Simultaneously

You can process data from multiple sources in the same Fabric workspace:

```
Schemas in your Lakehouse:
├── erp_replication     (ERP raw data)
├── erp_reporting       (ERP curated data)
├── crm_replication     (CRM raw data)
├── crm_reporting       (CRM curated data)
├── mkt_replication     (Marketing raw data)
└── mkt_reporting       (Marketing curated data)
```

Each source maintains complete isolation and clear lineage.

## Troubleshooting

### Issue: "Table or schema not found"
**Solution**: 
- Create schemas manually in the Lakehouse UI (right-click Schemas → New schema)
- Verify schemas exist in Lakehouse Explorer under the Schemas section
- Confirm you created both `erp_replication` and `erp_reporting` schemas

### Issue: "CREATE SCHEMA not supported" error in Lakehouse
**Solution**: This is expected behavior. Lakehouse SQL endpoint does not support `CREATE SCHEMA` SQL statements. Create schemas manually in the Lakehouse UI: right-click on **Schemas** → **New schema**

### Issue: "File not found" error in Bronze notebook
**Solution**: Verify the CSV file is uploaded to `Files/raw/customers.csv` in your Lakehouse

### Issue: Notebooks can't find tables
**Solution**: Make sure notebooks are attached to the correct Lakehouse (`lh_sales_core`)

### Issue: Data quality checks fail
**Solution**: Check the Silver table data quality. Common issues:
- Null IDs
- Invalid age values
- Duplicate records
- Malformed emails

### Issue: Pipeline parameter not passing correctly
**Solution**: 
- Ensure parameter name is exactly `source` (case-sensitive)
- In pipeline, use syntax: `@pipeline().parameters.source`
- In notebooks, verify the parameter retrieval code is present

## Next Steps - Productionization

Once your QuickStart is working:

1. **Add More Sources**: Use templates in `templates/` folder to connect Oracle, PostgreSQL, APIs, etc.
2. **Implement Incremental Loading**: Modify Bronze notebooks to use watermark columns
3. **Add Monitoring**: Implement logging and alerting for pipeline failures
4. **Separate Environments**: Create dev/test/prod workspaces following naming conventions
5. **Schema Evolution**: Plan for handling schema changes using Delta Lake features
6. **Data Governance**: Implement lineage tracking, sensitivity labels, and access controls
7. **CI/CD**: Set up Git integration and deployment pipelines

## Reference Documentation

- `docs/architecture.md` - Architecture decisions and patterns
- `docs/naming-conventions.md` - Naming standards for all Fabric items
- `README.md` - Project overview
- `templates/*.json` - Copy activity templates for various data sources

## Support

For issues or questions:
1. Review the troubleshooting section above
2. Check Microsoft Fabric documentation: https://learn.microsoft.com/fabric/
3. Verify all prerequisites and steps were completed in order

---

**Happy Building! 🚀**
