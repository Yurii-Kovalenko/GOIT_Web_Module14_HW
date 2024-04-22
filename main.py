"""
REST API Contacts
"""

import redis.asyncio as redis_asyncio

from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from fastapi.middleware.cors import CORSMiddleware

from src.routes import contacts, auth, users
from src.conf.config import settings

import uvicorn

app = FastAPI()

app.include_router(auth.router, prefix='/api')
app.include_router(contacts.router, prefix='/api')
app.include_router(users.router, prefix='/api')


@app.on_event("startup")
async def startup():
    """
    Initialization of the limit on the number of requests to contact routes
    """
    r = await redis_asyncio.Redis(host=settings.redis_host, port=settings.redis_port, db=0, encoding="utf-8",
                                  decode_responses=True)
    await FastAPILimiter.init(r)


@app.get("/")
def read_root():
    """
    The root to main page
    """
    return {"message": "REST API Contacts"}


@app.get("/api/healthchecker")
def root():
    """
    The root to healthchecker
    """
    return {"message": "Is working."}


origins = ["http://localhost:3000"]
"""
CORS for REST API
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
