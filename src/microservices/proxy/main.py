import os
import random
from contextlib import asynccontextmanager
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient()
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)

MONOLITH_URL = os.getenv("MONOLITH_URL", "http://monolith:8088")
MOVIES_SERVICE_URL = os.getenv("MOVIES_SERVICE_URL", "http://movies-service:8081")
EVENTS_SERVICE_URL = os.getenv("EVENTS_SERVICE_URL", "http://events-service:8082")
GRADUAL_MIGRATION = os.getenv("GRADUAL_MIGRATION", "true")
MOVIES_MIGRATION_PERCENT = int(os.getenv("MOVIES_MIGRATION_PERCENT", "50"))


async def forward_request(request: Request, target_url: str):
    client = request.app.state.client
    url = urljoin(target_url, request.url.path)
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in ["host", "content-length"]
    }

    body = await request.body()

    try:
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.query_params,
            content=body,
            timeout=5.0
        )
        if response.status_code == 200:
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code,
            )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Нет такой страницы")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    full_path = f"/{path}"
    target_url = MONOLITH_URL
    if GRADUAL_MIGRATION:
        if random.randint(1, 100) <= MOVIES_MIGRATION_PERCENT:
            if full_path.startswith("/api/movies"):
                target_url = MOVIES_SERVICE_URL
            elif full_path.startswith("/api/events"):
                target_url = EVENTS_SERVICE_URL
    return await forward_request(request, target_url)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8006)))
