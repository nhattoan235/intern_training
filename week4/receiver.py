"""
receiver.py - Consumer
Listen to the 'hello' queue and print each received message.

"""

import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# Declare the same queue as the sender (idempotent: no error if it already exists)
channel.queue_declare(queue='hello')


def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")


# auto_ack=True: automatically acknowledge a message as soon as it is received
channel.basic_consume(
    queue='hello',
    on_message_callback=callback,
    auto_ack=True
)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
