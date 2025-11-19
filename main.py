from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router import router

app = FastAPI(
    title="GovConnect KServe Deployer API",
    description="API for deploying and managing KServe models",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint providing basic API information"""
    return {
        "message": "GovConnect KServe Deployer API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
