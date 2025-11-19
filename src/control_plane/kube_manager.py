import logging
import boto3
import yaml
from botocore.exceptions import ClientError
import pathlib
from kubernetes import client
from kserve import KServeClient
from kserve import constants
from kserve import utils
from kserve import V1beta1InferenceService
from kserve import V1beta1InferenceServiceSpec
from kserve import V1beta1PredictorSpec
from kserve import V1beta1TFServingSpec
from src.config.config import config


class KubeManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_version = config.API_VERSION
        self.kind = constants.KSERVE_KIND
        self.kserve_client = KServeClient()
