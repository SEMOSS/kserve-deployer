from fastapi import APIRouter, Depends, HTTPException
from src.aws.aws_manager import AWSManager

router = APIRouter()


@router.delete("/delete-model-yaml")
def delete_model_yaml(key: str, aws_manager: AWSManager = Depends()) -> dict:
    try:
        success = aws_manager.delete_deployment_yaml(key)
        if not success:
            raise HTTPException(
                status_code=404, detail="Model YAML not found or could not be deleted."
            )
        return {"message": "Model YAML deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
