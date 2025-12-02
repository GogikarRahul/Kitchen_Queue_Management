from fastapi import FastAPI, Request
from app.api.v1.router import router as api_v1_router
from app.core.logging import get_logger

app = FastAPI()
logger = get_logger("main")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"REQUEST: {request.method} {request.url}")

    response = await call_next(request)

    logger.info(f"RESPONSE: {response.status_code} for {request.method} {request.url}")
    return response


app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Kitchen Queue Backend Running 👨‍🍳🔥"}
