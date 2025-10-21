from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager

from event_service.database import engine, Base
import event_service.models  # ensure models are imported and registered with Base
from event_service.api.event import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Create tables automatically for sqlite testing environment
        try:
            url_str = str(engine.url)
        except Exception:
            url_str = ""
        if url_str.startswith("sqlite"):
            Base.metadata.create_all(bind=engine)
    except Exception as e:
        logging.error(e, exc_info=True)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(events_router)


@app.get("/")
async def health_check():
    return {"status": "ok"}
