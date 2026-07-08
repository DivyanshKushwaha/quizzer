import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from init_tables import init_tables
from core.handler.exception import AuthError, ServiceError
from features.routers import auth_routes, quiz_routes, play_routes, ws_routes
from features.data_tools import quiz_data_tool as quiz_db
from features.data_tools import play_data_tool as play_db
from features.data_tools import redis_data_tool as redis_db

app = FastAPI(title="OneShop Quiz API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCHEDULER_TICK_SEC = 3


async def _scheduler_loop():
    """Tick server-side: auto-start scheduled quizzes and finish expired ones, then push over WS."""
    while True:
        try:
            changed = await quiz_db.run_transitions()
            if changed["activated"] or changed["finished"]:
                await redis_db.publish_global({"type": "feed"})
                for quiz_id in changed["activated"]:
                    await redis_db.publish(quiz_id, {"type": "started"})
                for quiz_id in changed["finished"]:
                    await play_db.finish_stale_attempts(quiz_id)
                    await redis_db.publish(quiz_id, {"type": "finished"})
        except Exception:
            pass
        await asyncio.sleep(SCHEDULER_TICK_SEC)


@app.on_event("startup")
def on_startup():
    init_tables()


@app.on_event("startup")
async def start_scheduler():
    asyncio.create_task(_scheduler_loop())


@app.exception_handler(AuthError)
def auth_error_handler(_: Request, exc: AuthError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(ServiceError)
def service_error_handler(_: Request, exc: ServiceError):
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


app.include_router(auth_routes.router, prefix="/auth")
app.include_router(quiz_routes.router)
app.include_router(play_routes.router)
app.include_router(ws_routes.router)
