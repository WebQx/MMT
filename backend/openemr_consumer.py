import pika
import json
import httpx
import os
from dotenv import load_dotenv
import asyncio
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenEMRConsumer:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        self.openemr_base_url = os.getenv("OPENEMR_BASE_URL", "https://demo.openemr.io/apis/default")
        self.openemr_api_key = os.getenv("OPENEMR_API_KEY", "test-api-key")
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish RabbitMQ connection"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='transcriptions', durable=True)
            logger.info("Connected to RabbitMQ")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    async def send_to_openemr(self, transcription_data):
        """Send transcription to OpenEMR"""
        try:
            # Prepare data for OpenEMR
            openemr_data = {
                "date": transcription_data.get("timestamp"),
                "body": transcription_data.get("text"),
                "title": f"Medical Transcription - {transcription_data.get('language', 'unknown')}",
                "user": transcription_data.get("user_id", "unknown"),
                "category": "Medical Transcription",
                "activity": 1  # Active
            }

            headers = {
                "Authorization": f"Bearer {self.openemr_api_key}",
                "Content-Type": "application/json"
            }

            # Send to OpenEMR API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.openemr_base_url}/encounters",
                    json=openemr_data,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    logger.info(f"Successfully sent transcription {transcription_data.get('transcription_id')} to OpenEMR")
                    return True
                else:
                    logger.error(f"OpenEMR API error: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send to OpenEMR: {e}")
            return False

    def process_message(self, ch, method, properties, body):
        """Process transcription message"""
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            logger.info(f"Processing transcription: {message.get('transcription_id')}")

            # Send to OpenEMR asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self.send_to_openemr(message))
            loop.close()

            if success:
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Message processed and acknowledged: {message.get('transcription_id')}")
            else:
                # Reject message and requeue for retry
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.warning(f"Message rejected and requeued: {message.get('transcription_id')}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject message and requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        if not self.connect():
            logger.error("Failed to connect to RabbitMQ")
            return

        try:
            # Set up consumer
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue='transcriptions',
                on_message_callback=self.process_message
            )

            logger.info("OpenEMR Consumer started. Waiting for messages...")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")

    def stop_consuming(self):
        """Stop consuming messages"""
        if self.channel:
            self.channel.stop_consuming()

def main():
    """Main function to run the consumer"""
    consumer = OpenEMRConsumer()
    
    try:
        consumer.start_consuming()
    except Exception as e:
        logger.error(f"Consumer failed: {e}")

if __name__ == "__main__":
    main()