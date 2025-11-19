from typing import List
from fastapi import APIRouter, Depends, HTTPException
from src.aws.aws_manager import AWSManager, SubnetInfo

router = APIRouter()


@router.get("/subnets/{vpc_id}")
async def list_subnets(
    vpc_id: str, aws_manager: AWSManager = Depends()
) -> List[SubnetInfo]:
    try:
        subnets = aws_manager.list_subnets(vpc_id)
        return subnets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
