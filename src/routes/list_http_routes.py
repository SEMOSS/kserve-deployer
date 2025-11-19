from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from src.control_plane.kube_manager import KubeManager, HTTPRouteInfo

router = APIRouter()


@router.get("/http-routes")
async def list_http_routes(
    namespace: Optional[str] = None, kube_manager: KubeManager = Depends()
) -> List[HTTPRouteInfo]:
    try:
        http_routes = kube_manager.list_http_routes(namespace=namespace)
        return http_routes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
