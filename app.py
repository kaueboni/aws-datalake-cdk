import os
from aws_cdk import core

from aws_datalake_cdk.common_stack import CommonStack
from aws_datalake_cdk.data_lake.stack import DataLakeStack
from aws_datalake_cdk.databricks.stack import DatabricksStack
from aws_datalake_cdk.glue_catalog.stack import GlueCatalogStack
from aws_datalake_cdk.kinesis.stack import KinesisStack
from aws_datalake_cdk.redshift.stack import RedshiftStack

os.environ["ENVIRONMENT"] = 'aws-lab'

app = core.App()
data_lake_stack = DataLakeStack(app)
common_stack = CommonStack(app)
kinesis_stack = KinesisStack(
    app, data_lake_raw_bucket=data_lake_stack.data_lake_raw_bucket
)
glue_catalog_stack = GlueCatalogStack(
    app,
    raw_data_lake_bucket=data_lake_stack.data_lake_raw_bucket,
    trusted_data_lake_bucket=data_lake_stack.data_lake_raw_trusted,
)
databricks_stack = DatabricksStack(app)
redshift_stack = RedshiftStack(
    app,
    common_stack=common_stack,
    data_lake_raw=data_lake_stack.data_lake_raw_bucket,
    data_lake_trusted=data_lake_stack.data_lake_raw_trusted,
)

app.synth()
