"""
AION Kafka Event Streaming Client
Real-time organizational event bus
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Kafka Topics
class KafkaTopics:
    KNOWLEDGE_INGESTED = "aion.knowledge.ingested"
    KNOWLEDGE_DECAYED = "aion.knowledge.decayed"
    KNOWLEDGE_CONFLICT = "aion.knowledge.conflict"
    EMPLOYEE_DEPARTED = "aion.employee.departed"
    DISEASE_DETECTED = "aion.disease.detected"
    SIMULATION_COMPLETED = "aion.simulation.completed"
    HEALING_RECOMMENDED = "aion.healing.recommended"
    OII_COMPUTED = "aion.intelligence.computed"
    SENSING_EVENT = "aion.sensing.event"
    GRAPH_UPDATED = "aion.graph.updated"
    BOARD_REPORT_READY = "aion.board.report_ready"

    ALL_TOPICS = [
        KNOWLEDGE_INGESTED, KNOWLEDGE_DECAYED, KNOWLEDGE_CONFLICT,
        EMPLOYEE_DEPARTED, DISEASE_DETECTED, SIMULATION_COMPLETED,
        HEALING_RECOMMENDED, OII_COMPUTED, SENSING_EVENT, GRAPH_UPDATED,
        BOARD_REPORT_READY,
    ]


_producer: Optional[AIOKafkaProducer] = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            enable_idempotence=True,
            max_batch_size=16384,
            linger_ms=5,
        )
        await _producer.start()
        logger.info("Kafka producer started")
    return _producer


async def close_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")


async def publish_event(
    topic: str,
    event: Dict[str, Any],
    key: Optional[str] = None,
    partition: Optional[int] = None,
) -> None:
    """Publish an event to a Kafka topic."""
    try:
        producer = await get_producer()
        await producer.send_and_wait(topic, value=event, key=key, partition=partition)
        logger.debug(f"Event published to {topic}", extra={"topic": topic, "key": key})
    except Exception as e:
        logger.error(f"Failed to publish event to {topic}: {e}")
        raise


async def create_consumer(
    topics: List[str],
    group_id: Optional[str] = None,
) -> AIOKafkaConsumer:
    """Create and start a Kafka consumer."""
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=settings.kafka_servers,
        group_id=group_id or settings.KAFKA_CONSUMER_GROUP_ID,
        auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=True,
        auto_commit_interval_ms=5000,
    )
    await consumer.start()
    return consumer


@dataclass
class EventEnvelope:
    topic: str
    key: Optional[str]
    value: Dict[str, Any]
    offset: int
    partition: int
    timestamp: int
