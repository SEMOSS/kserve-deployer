from dotenv import load_dotenv
from pydantic import BaseModel


class Config(BaseModel):
    """Configuration settings for the application"""

    NAMESPACE: str
    API_VERSION: str = "0.16"
    BUCKET_NAME: str = "kserve-deployments"


load_dotenv()

config = Config(
    NAMESPACE="kserve",
    API_VERSION="0.16",
    BUCKET_NAME="kserve-deployments",
)
