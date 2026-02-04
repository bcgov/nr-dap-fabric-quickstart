# Data Quality Checks (PySpark) aligned to named schemas
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

reporting_schema = f"{source}_reporting"
silver_table = f"{reporting_schema}.customers_curated"

df = spark.table(silver_table)

# 1) Non-null IDs
null_ids = df.filter(F.col("id").isNull()).count()
assert null_ids == 0, f"Null IDs found: {null_ids}"

# 2) Age reasonable range
bad_age = df.filter((F.col("age") < 0) | (F.col("age") > 120)).count()
assert bad_age == 0, f"Out-of-range ages: {bad_age}"

# 3) Duplicate business keys
dup_ids = (
    df.groupBy("id")
      .count()
      .filter(F.col("count") > 1)
      .count()
)
assert dup_ids == 0, f"Duplicate IDs found: {dup_ids}"

# 4) Basic email sanity check (simple contains check)
bad_email = df.filter(~F.col("email").contains("@")).count()
assert bad_email == 0, f"Malformed emails found: {bad_email}"

print("Data quality checks passed.")
