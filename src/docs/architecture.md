
# Architecture Notes
- Use Delta tables for all zones to enable ACID, time travel, and efficient merges.
- Prefer append-only writes in Bronze; overwrite in Silver/Gold when building full refresh.
- Track lineage using Fabric workspace items and naming conventions (e.g., `lh_bronze_*`).
- Separate dev/test/prod workspaces when operationalizing.


## Standard Schemas

We use **source-scoped schemas** in the Lakehouse/Warehouse to keep replicated and curated data clearly separated:

- `<source>_replication`: raw/replicated data exactly as landed from the source (append-only; schema-on-read).
- `<source>_reporting`: cleansed & conformed tables for analytics and downstream mart consumption.

**Zone routing**
- **Bronze** writes in `<source>_replication`.
- **Silver** overwrites in `<source>_reporting`.
- **Gold** marts live in `<source>_reporting` (or a dedicated `marts` schema per governance).

**Examples**
- `erp_replication.customers_raw`
- `erp_reporting.customers_curated`
- `crm_replication.accounts_raw`
- `crm_reporting.accounts_curated`
