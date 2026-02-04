# Copy Activity Templates

These JSON templates are **reference guides** showing the correct structure and configuration patterns for Microsoft Fabric Copy activities. They demonstrate how to configure Copy activities for ingesting data from various sources into your Lakehouse.

**Important**: These templates cannot be directly imported or pasted into Fabric. Use them as a guide to manually configure Copy activities through the Fabric UI.

## Copy Data vs Copy Job

Microsoft Fabric provides two ways to create copy operations for data ingestion:

### Option 1: Copy Data
**Use this when you want to create a new pipeline activity that moves data from a source system into the Bronze Lakehouse.**

**Example:**
- Source: SQL Database or Blob Storage
- Destination: Lakehouse (Bronze layer)

**You configure:**
- Source connection
- Destination table or folder
- Mapping (optional)

**Ideal for:** Initial ingestion or adding a new data source.

### Option 2: Copy Job
**Use this when you already have a similar ingestion pipeline and want to duplicate its configuration for another source or dataset.**

**Example:**
- You have a pipeline that ingests Customer data into Bronze
- You want to ingest Orders data with the same settings (e.g., same Lakehouse, same transformations)

**Copy job saves time because:**
- It clones the activity, including triggers, retry policies, and settings
- You only change the source/destination specifics

### Best Practice for Bronze Zone
- **First time for a new source**: Use **Copy data** to create the ingestion activity
- **Scaling ingestion for multiple similar sources**: Use **Copy job** to replicate the pipeline logic quickly

**These templates show the configuration structure that both methods create**, helping you understand what settings to configure regardless of which method you use.

## How to Use These Templates

These templates show you the **correct configuration structure** that MS Fabric uses internally. Use them as a reference when configuring Copy activities through the Fabric interface.

### Step 1: Understand the Template Structure

Each template shows:
- **Source configuration**: Connection type, settings, and parameters
- **Sink configuration**: Lakehouse table destination
- **Field mappings**: How source fields map to destination columns
- **Data types**: Proper type conversions

### Step 2: Create Copy Activity in Fabric UI

1. In your Fabric workspace, create a new **Data Pipeline**
2. Add a **Copy Data** activity to the canvas
3. Configure using the template as your guide:

   **For Source**:
   - Set the connection type (e.g., PostgreSQL, REST API, S3)
   - Configure connection settings shown in the template
   - Match the source settings (table names, endpoints, etc.)

   **For Sink**:
   - Select your Lakehouse
   - Set schema and table name
   - Choose "Append" mode for Bronze layer

   **For Mappings** (if needed):
   - Use the field mappings shown in the template
   - Match data types to ensure proper conversion

### Step 3: Replace Placeholders with Your Values

Templates use placeholders like:
- `<YOUR_POSTGRESQL_CONNECTION_ID>` - Replace with your actual connection (created in Fabric)
- `<YOUR_WORKSPACE_ID>` - Your Fabric workspace GUID
- `<YOUR_LAKEHOUSE_ARTIFACT_ID>` - Your Lakehouse GUID
- Schema/table names - Adjust to match your naming conventions

**Note**: You don't manually replace these - the Fabric UI handles connections and IDs when you configure through the interface. These placeholders are for reference only—do not edit or upload JSON.

## Template Descriptions

### copy_postgresql.json
- **Purpose**: Reference for configuring PostgreSQL to Lakehouse copy
- **Source Type**: PostgreSqlSource

### copy_oracle.json  
- **Purpose**: Reference for configuring Oracle to Lakehouse copy
- **Source Type**: OracleSource

### copy_s3.json
- **Purpose**: Reference for configuring S3 CSV files to Lakehouse
- **Source Type**: AmazonS3 + DelimitedText
- **Format**: CSV with headers

### copy_api.json
- **Purpose**: Reference for configuring REST API to Lakehouse copy
- **Source Type**: RestSource

## Understanding the JSON Structure

MS Fabric Copy activities use this structure:

```json
{
  "name": "activity-name",
  "type": "Copy",
  "typeProperties": {
    "source": {
      "type": "SourceType",
      "datasetSettings": { ... }
    },
    "sink": {
      "type": "LakehouseTableSink",
      "datasetSettings": { ... }
    },
    "translator": {
      "type": "TabularTranslator",
      "mappings": [ ... ]
    }
  }
}
```

**Key differences from simplified examples**:
- Nested `typeProperties` and `datasetSettings`
- Specific type names (e.g., `PostgreSqlSource` not just `PostgreSQL`)
- Detailed connection references with GUIDs
- Explicit field mappings with JSON paths for APIs

## Best Practices

### Schema Naming
- Bronze layer: `{source}_replication` (e.g., `erp_replication`)
- Always create schemas in Lakehouse UI before running Copy jobs

### Table Naming  
- Raw tables: `{entity}_raw` (e.g., `customers_raw`)
- Use append mode for Bronze to preserve history

### Field Mappings
- For APIs: Use JSON path expressions (e.g., `$['data'][*]['fieldName']`)
- For databases: Usually auto-mapped, but verify data types
- Convert timestamps to DateTime type in mappings

### Connection Management
- Create reusable connections in Fabric workspace
- Use descriptive names (e.g., `conn_postgresql_erp`, `conn_bcparks_api`)
- Store credentials securely (never in templates)

## Important Notes

- **Templates are for reference only** - They show structure and patterns, not importable code
- **Create schemas first** in your Lakehouse UI before running Copy activities
- **Connection IDs are unique** to your Fabric workspace - templates use placeholders
- **Test with small datasets** before running full loads
- **Field mappings may need adjustment** based on your actual source data structure

## Common Configuration Scenarios

### Scenario 1: Database Table Replication
1. View `copy_postgresql.json` or `copy_oracle.json`
2. Create database connection in Fabric
3. Configure Copy activity with source table
4. Set sink to `{source}_replication.{table}_raw`
5. Use Append mode

### Scenario 2: REST API Data Ingestion  
1. View `copy_api.json`
2. Create REST API connection (or use anonymous for public APIs)
3. Configure source with API endpoint
4. Set up JSON path mappings for nested responses
5. Use `collectionReference` to specify array location

### Scenario 3: File-based Ingestion (S3)
1. View `copy_s3.json`
2. Create cloud storage connection
3. Configure file location and format (CSV, JSON, etc.)
4. Set header row options
5. Map to Lakehouse table

---

**Remember**: These templates show you **what Fabric creates** when you configure Copy activities correctly. Use them to understand the structure, not to copy/paste directly.

## Important Notes

- All templates use **Append** mode for Bronze layer (raw data preservation)
- Schema and table names follow the `{source}_replication.{entity}_raw` convention
- Connection IDs are unique to your Fabric workspace - do not share publicly
- Test with a small dataset first before running full loads
- These templates are tested with MS Fabric as of December 2025 (features may change)

## Need Help?

See the main [SETUP.md](../SETUP.md) for complete setup instructions and [README.md](../README.md) for architecture guidance.