from fastapi import APIRouter, HTTPException
from src.control_plane.kube_manager import KubeManager

router = APIRouter()
km = KubeManager(in_cluster=False)


@router.post("/download-model")
def download_model(model_name: str, hf_repo_id: str):
    ok = km.download_model_to_pvc(model_name=model_name, hf_repo_id=hf_repo_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to download model to PVC.")
    return {"status": "ok", "model": model_name, "hf_repo_id": hf_repo_id}
