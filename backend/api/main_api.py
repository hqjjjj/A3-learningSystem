from fastapi import FastAPI

from api.api_chat import router as chat_router
from api.api_path import router as path_router
from api.api_resource import router as resource_router

app=FastAPI()

# 挂载子路由并未它们分配虚拟路径（网址区域）
app.include_router(
    chat_router,
    prefix="/api/chat",
    tags=["chat"]
)

app.include_router(
    path_router,
    prefix="/api/path",
    tags=["path"]
)

app.include_router(
    resource_router,
    prefix="/api/resource",
    tags=["resource"]
)