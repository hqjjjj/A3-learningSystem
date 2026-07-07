import sys
sys.path.insert(0, '..')

from fastapi import FastAPI

from api_chat import router as chat_router
from api_path import router as path_router
from api_resource import router as resource_router
from api_user import router as user_router

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# 挂载子路由并未它们分配虚拟路径
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

app.include_router(
    user_router, 
    prefix="/api/user", 
    tags=["user"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)