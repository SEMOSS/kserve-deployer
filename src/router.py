from fastapi import APIRouter
from src.routes.list_subnets import router as list_subnets_router
from src.routes.upload_deployment_yaml import router as upload_deployment_yaml_router
from src.routes.upload_deployment_yaml_content import (
    router as upload_deployment_yaml_content_router,
)
from src.routes.list_deployment_yamls import router as list_deployment_yamls_router
from src.routes.read_deployment_yaml import router as read_deployment_yaml_router
from src.routes.read_all_deployment_yamls import (
    router as read_all_deployment_yamls_router,
)

router = APIRouter()

router.include_router(list_subnets_router, prefix="/api")
router.include_router(upload_deployment_yaml_router, prefix="/api")
router.include_router(upload_deployment_yaml_content_router, prefix="/api")
router.include_router(list_deployment_yamls_router, prefix="/api")
router.include_router(read_deployment_yaml_router, prefix="/api")
router.include_router(read_all_deployment_yamls_router, prefix="/api")


@router.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}
