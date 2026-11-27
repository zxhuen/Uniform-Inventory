from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import engine, Base


from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.modules.people.router import router as PeopleRouter

app = FastAPI(title="Uniform Inventory API")

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(SlowAPIMiddleware)

app.include_router(PeopleRouter)
