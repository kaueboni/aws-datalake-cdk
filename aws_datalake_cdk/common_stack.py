import os

from aws_cdk import core
from aws_cdk import aws_rds as rds, aws_ec2 as ec2


class CommonStack(core.Stack):
    def __init__(self, scope: core.Construct, **kwargs) -> None:
        self.deploy_env = os.environ["ENVIRONMENT"]
        super().__init__(scope, id=f"{self.deploy_env}-common-stack", **kwargs)

        self.custom_vpc = ec2.Vpc(self, f"vpc-{self.deploy_env}")

        
