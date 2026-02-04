# Bronze (Staging) - PySpark
# Attach to Lakehouse and run with Spark in Microsoft Fabric.
from pyspark.sql import functions as F
import os

# ----- Parameters (from pipeline/job) -----
try:
    from notebookutils import mssparkutils  # Fabric/Synapse utility
except Exception:
    mssparkutils = None

source = None
if mssparkutils:
    try:
        source = mssparkutils.env.getJobParam("source")
    except Exception:
        source = None
if not source:
    source = os.environ.get('SOURCE', 'erp')  # fallback default

replication_schema = f"{source}_replication"

# Paths (adjust as needed)
raw_path = "Files/quickstart/samples/customers.csv"

# Table naming
bronze_table = f"{replication_schema}.customers_raw"

# Load raw CSV from OneLake Files into Delta (append-only)
df_raw = spark.read.option("header", True).csv(raw_path)
(
    df_raw
    .withColumn("_ingest_ts", F.current_timestamp())
    .write
    .format("delta")
    .mode("append")
    .saveAsTable(bronze_table)
)
print(f"Bronze table written: {bronze_table}")
