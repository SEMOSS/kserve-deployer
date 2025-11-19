from fastapi import APIRouter, HTTPException
from src.control_plane.kube_manager import KubeManager

router = APIRouter()
km = KubeManager(in_cluster=False)


@router.post("/delete/{model_name}")
async def delete(
    model_name: str,
    namespace: str = None,
    wait: bool = True,
    timeout_sec: int = 300,
    poll_sec: int = 3,
):
    ok = await km.delete_inference_service(
        name=model_name,
        namespace=namespace,
        wait=wait,
        timeout_sec=timeout_sec,
        poll_sec=poll_sec,
    )
    if not ok:
        raise HTTPException(
            status_code=500, detail="Failed to delete or wait for deletion."
        )
    return {"status": "ok", "model": model_name, "namespace": namespace, "waited": wait}
