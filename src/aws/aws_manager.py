from typing import List
import boto3
from pydantic import BaseModel
import logging
import yaml
from botocore.exceptions import ClientError
import pathlib
from src.config.config import config


class SubnetInfo(BaseModel):
    SubnetId: str
    CidrBlock: str
    AvailableIpAddressCount: int


class AWSManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ec2_client = boto3.client("ec2")

    def list_subnets(self, vpc_id) -> List[SubnetInfo]:
        response = self.ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        subnets_info = []
        for subnet in response["Subnets"]:
            subnet_info = SubnetInfo(
                SubnetId=subnet["SubnetId"],
                CidrBlock=subnet["CidrBlock"],
                AvailableIpAddressCount=subnet["AvailableIpAddressCount"],
            )
            subnets_info.append(subnet_info)
        return subnets_info

    def upload_deployment_yaml(self, yaml_path: str):
        path = pathlib.Path(yaml_path)

        with open(path, "r") as file:
            deployment_yaml = yaml.safe_load(file)

        model_name = deployment_yaml.get("metadata", {}).get("name")
        if not model_name:
            self.logger.error("Model name not found in YAML metadata.")
            return False

        try:
            s3_client = boto3.client("s3")
            s3_client.upload_file(
                Filename=str(path),
                Bucket=config.BUCKET_NAME,
                Key=f"{model_name}.yaml",
            )
        except ClientError as e:
            self.logger.error(e)
            return False

        return True
