from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用首次启动时初始化数据库
    :param app: FastAPI应用
    :return:
    """

    await init_db()
    yield


app = FastAPI(title="至道 API", lifespan=lifespan)
app.include_router(router=router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
