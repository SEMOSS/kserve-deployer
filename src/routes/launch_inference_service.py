from fastapi import APIRouter, HTTPException
from src.control_plane.kube_manager import KubeManager

router = APIRouter()
km = KubeManager(in_cluster=False)


@router.post("/deploy/{model_name}")
async def deploy(model_name: str, semoss_id: str, wait: bool = True):
    ok = await km.deploy_inference_service(
        model_name=model_name, semoss_id=semoss_id, wait=wait
    )
    if not ok:
        raise HTTPException(
            status_code=500, detail="Failed to deploy or wait for readiness."
        )
    return {"status": "ok", "model": model_name, "semoss_id": semoss_id, "waited": wait}
