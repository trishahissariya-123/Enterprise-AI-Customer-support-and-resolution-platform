import  json
from aiokafka import AIOKafkaProducer


class KafkaEventProducer:
    def __init__(self,
                 bootstrap_servers:str ="localhost:9092",):
        self.bootstrap_servers = bootstrap_servers
        self.producer : AIOKafkaProducer | None = None

    async def start(self):
        self.producer= AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers,
                                        value_serializer=lambda m: json.dumps(m).encode('utf-8'))


        await self.producer.start()


    async def stop(self):
        if self.producer is not None:
            await self.producer.stop()
            self.producer = None

    async def publish(self, topic:str, event:dict):
        if self.producer is None:
            raise RuntimeError('Kafka producer not started')
        await self.producer.send_and_wait(topic, event)