from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.aws.aws_manager import AWSManager
import yaml
import tempfile
import os

router = APIRouter()


class YamlContentUpload(BaseModel):
    content: str


@router.post("/upload-yaml-content")
def upload_deployment_yaml_content(
    payload: YamlContentUpload, aws_manager: AWSManager = Depends()
) -> dict:
    """
    Upload deployment YAML content directly without requiring a file path.
    Creates a temporary file, uploads to S3, then cleans up.
    The S3 key is automatically extracted from the metadata.name field in the YAML.
    """
    try:
        try:
            deployment_yaml = yaml.safe_load(payload.content)
        except yaml.YAMLError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid YAML format: {str(e)}"
            )

        model_name = deployment_yaml.get("metadata", {}).get("name")
        if not model_name:
            raise HTTPException(
                status_code=400,
                detail="YAML must contain metadata.name field for the deployment name",
            )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            temp_file.write(payload.content)
            temp_file_path = temp_file.name

        try:
            success = aws_manager.upload_deployment_yaml(temp_file_path)
            if not success:
                raise HTTPException(
                    status_code=400, detail="Failed to upload deployment YAML to S3."
                )
            return {
                "message": "Deployment YAML uploaded successfully.",
                "key": f"{model_name}.yaml",
            }
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
