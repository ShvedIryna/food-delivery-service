from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401 — реєструє таблиці в Base.metadata
from app.api import routes_auth, routes_catalog, routes_orders, routes_profile
from app.core.config import get_settings
from app.db.session import Base, SessionLocal, engine, wait_for_db
from app.seed import seed_if_empty

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    Base.metadata.create_all(engine)
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_if_empty(db)
    yield


app = FastAPI(
    title="Смак Експрес — API сервісу доставки їжі",
    version="1.0.0",
    description="REST API курсової роботи з дисципліни «Документування ПЗ та шаблони проєктування».",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (routes_auth, routes_catalog, routes_orders, routes_profile):
    app.include_router(module.router)


@app.get("/api/health", tags=["Службові"])
def health():
    return {"status": "ok"}
