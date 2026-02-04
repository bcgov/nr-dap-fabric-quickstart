# Gold (Business Marts) - PySpark
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
gold_table = f"{reporting_schema}.customer_country_ageband_mart"

silver_df = spark.table(silver_table)

# Example business metric: customers by country and age band
banded = (
    silver_df
    .withColumn(
        "age_band",
        F.when(F.col("age") < 25, "<25")
         .when((F.col("age") >= 25) & (F.col("age") < 35), "25-34")
         .when((F.col("age") >= 35) & (F.col("age") < 50), "35-49")
         .otherwise("50+")
    )
    .groupBy("country", "age_band")
    .agg(F.countDistinct("id").alias("customers"))
)

banded.write.format("delta").mode("overwrite").saveAsTable(gold_table)
print(f"Gold table written: {gold_table}")
