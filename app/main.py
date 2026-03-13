from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_database
from app.dns_server import start_dns_server
from app.routes import custom_hostnames, dns_records, mockflare, zones
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    seed_database()

    dns_server = start_dns_server()

    yield

    dns_server.stop()


app = FastAPI(
    title="Mockflare",
    description="Mock Cloudflare API for DNS Records and Custom Hostnames",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(zones.router)
app.include_router(dns_records.router)
app.include_router(custom_hostnames.router)
app.include_router(mockflare.router)


@app.get("/")
def root():
    return {"message": "Mockflare API", "docs": "/docs"}
