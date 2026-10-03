import asyncio

from backend.app.infrastructure.kafka.producer import KafkaEventProducer


async def main():

    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092"
    )

    try:
        await producer.start()

        event = {
            "event_type": "TEST_EVENT",
            "customer_id": "CUST1001",
            "message": "Kafka integration test",
        }

        await producer.publish(
            topic="support-events",
            event=event,
        )

        print("Kafka event published successfully")

    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())