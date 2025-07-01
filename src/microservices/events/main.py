import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, APIRouter, status

from events import broker, producer, send_event
from schemas import EventResponse, MovieEvent, UserEvent, PaymentEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await broker.start()
        await producer.start()
        logger.info("Connected to Kafka successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        raise
    finally:
        await broker.close()
        await producer.stop()
        logger.info("Disconnected from Kafka")


app = FastAPI(lifespan=lifespan)
router = APIRouter(prefix="/api/events")


@router.get("/health")
async def health():
    return {"status": True}


@router.post("/movie", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_movie_event(movie: MovieEvent):
    try:
        return await send_event("movie", movie.dict(), "movie-events")
    except Exception as e:
        logging.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.post("/user", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_user_event(user: UserEvent):
    try:
        return await send_event("user", user.dict(), "user-events")
    except Exception as e:
        logging.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.post("/payment", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_event(payment: PaymentEvent):
    try:
        return await send_event("payment", payment.dict(), "payment-events")
    except Exception as e:
        logging.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8082)))
