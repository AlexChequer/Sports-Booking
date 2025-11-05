from fastapi import FastAPI
from app.api.routes import health, bookings_user, quotes, callbacks
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="Sports-Booking")


app.include_router(health.router, tags=["health"])
app.include_router(bookings_user.router, tags=["bookings"])
app.include_router(quotes.router, tags=["quotes"])
app.include_router(callbacks.router, tags=["callbacks"])

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import traceback, logging

logger = logging.getLogger("uvicorn.error")

@app.exception_handler(Exception)
async def unhandled_exc(request: Request, exc: Exception):
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("500 on %s %s | %s", request.method, request.url.path, tb)
    # devolve o erro para facilitar o debug (temporário):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def validation_exc(request: Request, exc: RequestValidationError):
    body = (await request.body()).decode() if await request.body() else "<empty>"
    logger.error("422 on %s %s | body=%s | errors=%s", request.method, request.url.path, body, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
