import os

from aws_cdk import core
from aws_cdk import aws_redshift as redshift, aws_ec2 as ec2, aws_iam as iam
from aws_datalake_cdk.data_lake.base import BaseDataLakeBucket

from aws_datalake_cdk.common_stack import CommonStack

"""
CREATE EXTERNAL SCHEMA data_lake_raw
FROM DATA CATALOG
DATABASE 'glue_kaue-bonilha_develop_data_lake_raw'
REGION 'us-east-1'
IAM_ROLE 'arn:aws:iam::820187792016:role/develop-redshift-stack-iamdevelopredshiftspectrumr-SMTW4PNGK8YI'
"""

class SpectrumRole(iam.Role):
    def __init__(
        self,
        scope: core.Construct,
        data_lake_raw: BaseDataLakeBucket,
        data_lake_trusted: BaseDataLakeBucket,
        **kwargs,
    ) -> None:
        self.deploy_env = os.environ["ENVIRONMENT"]
        self.data_lake_raw = data_lake_raw
        self.data_lake_trusted = data_lake_trusted

        super().__init__(
            scope,
            id=f"iam-{self.deploy_env}-redshift-spectrum-role",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            description="Role to allow Redshift to access data lake using spectrum",
        )

        policy = iam.Policy(
            scope,
            id=f"iam-{self.deploy_env}-redshift-spectrum-policy",
            policy_name=f"iam-{self.deploy_env}-redshift-spectrum-policy",
            statements=[
                iam.PolicyStatement(actions=["glue:*", "athena:*"], resources=["*"]),
                iam.PolicyStatement(
                    actions=["s3:Get*", "s3:List*", "s3:Put*"],
                    resources=[
                        self.data_lake_raw.bucket_arn,
                        f"{self.data_lake_raw.bucket_arn}/*",
                        self.data_lake_trusted.bucket_arn,
                        f"{self.data_lake_trusted.bucket_arn}/*",
                    ],
                ),
            ],
        )
        self.attach_inline_policy(policy)


class RedshiftStack(core.Stack):
    def __init__(
        self,
        scope: core.Construct,
        data_lake_raw: BaseDataLakeBucket,
        data_lake_trusted: BaseDataLakeBucket,
        common_stack: CommonStack,
        **kwargs,
    ) -> None:
        self.common_stack = common_stack
        self.data_lake_raw = data_lake_raw
        self.deploy_env = os.environ["ENVIRONMENT"]
        self.data_lake_trusted = data_lake_trusted
        super().__init__(scope, id=f"{self.deploy_env}-redshift-stack", **kwargs)

        self.redshift_sg = ec2.SecurityGroup(
            self,
            f"redshift-{self.deploy_env}-sg",
            vpc=self.common_stack.custom_vpc,
            allow_all_outbound=True,
            security_group_name=f"redshift-{self.deploy_env}-sg",
        )

        self.redshift_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("0.0.0.0/0"), connection=ec2.Port.tcp(5439)
        )

        for subnet in self.common_stack.custom_vpc.private_subnets:
            self.redshift_sg.add_ingress_rule(
                peer=ec2.Peer.ipv4(subnet.ipv4_cidr_block), connection=ec2.Port.tcp(5439)
            )

        self.redshift_cluster = redshift.Cluster(
            self,
            f"kaue-bonilha-{self.deploy_env}-redshift",
            cluster_name=f"kaue-bonilha-{self.deploy_env}-redshift",
            vpc=self.common_stack.custom_vpc,
            cluster_type=redshift.ClusterType.MULTI_NODE,
            node_type=redshift.NodeType.DC2_LARGE,
            default_database_name="dw",
            number_of_nodes=2,
            removal_policy=core.RemovalPolicy.DESTROY,
            master_user=redshift.Login(master_username="admin"),
            publicly_accessible=True,
            roles=[SpectrumRole(self, self.data_lake_raw, self.data_lake_trusted)],
            security_groups=[self.redshift_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )
