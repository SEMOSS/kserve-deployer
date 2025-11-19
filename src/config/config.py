import os
from dotenv import load_dotenv
from pydantic import BaseModel


class Config(BaseModel):
    """Configuration settings for the application"""

    MODEL_NAMESPACE: str
    API_VERSION: str
    BUCKET_NAME: str
    KSERVE_GROUP: str
    KSERVE_VERSION: str
    KSERVE_PLURAL: str
    HOSTNAME: str


load_dotenv()
config = Config(
    MODEL_NAMESPACE=os.getenv("MODEL_NAMESPACE", "huggingface"),
    API_VERSION=os.getenv("API_VERSION", "0.16"),
    BUCKET_NAME=os.getenv("BUCKET_NAME", "kserve-deployments"),
    KSERVE_GROUP=os.getenv("KSERVE_GROUP", "serving.kserve.io"),
    KSERVE_VERSION=os.getenv("KSERVE_VERSION", "v1beta1"),
    KSERVE_PLURAL=os.getenv("KSERVE_PLURAL", "inferenceservices"),
    HOSTNAME=os.getenv("HOSTNAME", "demo.semoss.org"),
)
