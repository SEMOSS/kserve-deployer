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
    AvailabilityZone: str


class AWSManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ec2_client = boto3.client("ec2")
        self.s3_client = boto3.client("s3")

    def list_subnets(self, vpc_id) -> List[SubnetInfo]:
        """
        Lists all subnets in a given VPC including their CIDR blocks and available IP counts.
        """
        response = self.ec2_client.describe_subnets(
            Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
        )
        subnets_info = []
        for subnet in response["Subnets"]:
            subnet_info = SubnetInfo(
                SubnetId=subnet["SubnetId"],
                CidrBlock=subnet["CidrBlock"],
                AvailableIpAddressCount=subnet["AvailableIpAddressCount"],
                AvailabilityZone=subnet["AvailabilityZone"],
            )
            subnets_info.append(subnet_info)
        return subnets_info

    def upload_deployment_yaml(self, yaml_path: str):
        """
        Uploads a deployment YAML file to an S3 bucket.
        """
        path = pathlib.Path(yaml_path)

        with open(path, "r") as file:
            deployment_yaml = yaml.safe_load(file)

        model_name = deployment_yaml.get("metadata", {}).get("name")
        if not model_name:
            self.logger.error("Model name not found in YAML metadata.")
            return False

        try:
            self.s3_client.upload_file(
                Filename=str(path),
                Bucket=config.BUCKET_NAME,
                Key=f"{model_name}.yaml",
            )
        except ClientError as e:
            self.logger.error(e)
            return False

        return True

    def list_deployment_yamls(self) -> List[str]:
        """
        List only the files that are directly in the root of the bucket
        (keys without a '/' in them).
        """
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=config.BUCKET_NAME, Delimiter="/")

            files: List[str] = []
            for page in pages:
                for obj in page.get("Contents", []):
                    files.append(obj["Key"])
            return files
        except ClientError as e:
            self.logger.error(e)
            return []

    def read_deployment_yaml(self, key: str) -> dict:
        """
        Reads a deployment YAML file from an S3 bucket and returns its contents as a dictionary.
        """
        try:
            response = self.s3_client.get_object(Bucket=config.BUCKET_NAME, Key=key)
            yaml_content = response["Body"].read().decode("utf-8")
            return yaml.safe_load(yaml_content)
        except ClientError as e:
            self.logger.error(f"Failed to read {key} from S3: {e}")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML format in {key}: {e}")
            return {}

    def read_all_deployment_yamls(self) -> dict:
        """
        Reads all deployment YAML files from the S3 bucket and returns their contents as a dictionary.
        """
        yamls = {}
        files = self.list_deployment_yamls()
        for key in files:
            yaml_content = self.read_deployment_yaml(key)
            if yaml_content:
                yamls[key] = yaml_content
        return yamls

    def delete_deployment_yaml(self, model_name: str) -> bool:
        """
        Deletes a deployment YAML file from the S3 bucket.
        """
        try:
            self.s3_client.delete_object(
                Bucket=config.BUCKET_NAME, Key=f"{model_name}.yaml"
            )
            return True
        except ClientError as e:
            self.logger.error(f"Failed to delete {model_name}.yaml from S3: {e}")
            return False
