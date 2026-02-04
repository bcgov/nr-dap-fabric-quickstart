# Silver (Cleanse & Conform) - PySpark
from pyspark.sql import functions as F
import os

# ----- Parameters (from pipeline/job) -----
try:
    from notebookutils import mssparkutils
except Exception:
    mssparkutils = None

source = None
if mssparkutils:
    try:
        source = mssparkutils.env.getJobParam("source")
    except Exception:
        source = None
if not source:
    source = os.environ.get('SOURCE', 'erp')

replication_schema = f"{source}_replication"
reporting_schema = f"{source}_reporting"

bronze_table = f"{replication_schema}.customers_raw"
silver_table = f"{reporting_schema}.customers_curated"

bronze_df = spark.table(bronze_table)

# Minimal transformations: types, trim, dedupe
silver_df = (
    bronze_df
    .withColumn("age", F.col("age").cast("int"))
    .withColumn("country", F.upper(F.col("country")))
    .withColumn("name", F.trim(F.col("name")))
    .dropDuplicates(["id"])  # business key
)

silver_df.write.format("delta").mode("overwrite").saveAsTable(silver_table)
print(f"Silver table written: {silver_table}")
