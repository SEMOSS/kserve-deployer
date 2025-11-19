from fastapi import APIRouter, Depends, HTTPException
from src.aws.aws_manager import AWSManager

router = APIRouter()


@router.post("/list-deployment-yamls")
def list_deployment_yamls(aws_manager: AWSManager = Depends()) -> dict:
    try:
        files = aws_manager.list_deployment_yamls()
        return {"deployments": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
