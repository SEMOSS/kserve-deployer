from fastapi import APIRouter, Depends, HTTPException
from src.aws.aws_manager import AWSManager

router = APIRouter()


@router.post("/read-deployment-yaml")
async def read_deployment_yaml(key: str, aws_manager: AWSManager = Depends()) -> dict:
    yaml_content = aws_manager.read_deployment_yaml(key)
    if not yaml_content:
        raise HTTPException(status_code=404, detail="Deployment YAML not found")
    return {"yaml": yaml_content}
