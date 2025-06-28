import logging
import os
import json
from faststream import FastStream
from faststream.kafka import KafkaBroker
from aiokafka import AIOKafkaProducer
from schemas import Event,EventResponse
from datetime import datetime
from uuid import uuid4
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kafka_url = os.getenv("KAFKA_BROKERS", "kafka:9092")

producer = AIOKafkaProducer(bootstrap_servers=kafka_url)
broker = KafkaBroker(kafka_url)
stream = FastStream(broker)

logging.basicConfig(level=logging.INFO)


async def send_event(event_type: str, payload: dict, topic: str):
    event = Event(
        id=str(uuid4()),
        type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        payload=payload
    ).dict()
    message = json.dumps(event, default=str).encode('utf-8')
    metadata = await producer.send_and_wait(topic, message)
    return EventResponse(
        status="success",
        partition=metadata.partition,
        offset=metadata.offset,
        event=event
    ).dict()


@broker.subscriber("movie-events")
async def handle_movie_event(event: Event):
    logger.info(f"Received movie event in handler: {event.dict()}")


@broker.subscriber("user-events")
async def handle_user_event(msg: dict):
    logger.info(f"Received user event: {msg}")


@broker.subscriber("payment-events")
async def handle_payment_event(msg: dict):
    logger.info(f"Received payment event: {msg}")

