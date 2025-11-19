from fastapi import APIRouter, Depends, HTTPException
from src.aws.aws_manager import AWSManager

router = APIRouter()


@router.post("/read-all-deployment-yamls")
def read_all_deployment_yamls(aws_manager: AWSManager = Depends()) -> dict:
    yamls = aws_manager.read_all_deployment_yamls()
    if not yamls:
        raise HTTPException(status_code=404, detail="No deployment YAMLs found")
    return {"yamls": yamls}
