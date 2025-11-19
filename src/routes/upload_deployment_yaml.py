from fastapi import APIRouter, Depends, HTTPException
from src.aws.aws_manager import AWSManager

router = APIRouter()


@router.post("/upload")
async def upload_deployment_yaml(
    yaml_path: str, aws_manager: AWSManager = Depends()
) -> dict:
    try:
        success = aws_manager.upload_deployment_yaml(yaml_path)
        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to upload deployment YAML."
            )
        return {"message": "Deployment YAML uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
