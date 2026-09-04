"""
sender.py - Producer
Send the "Hello World!" message to the 'hello' queue on RabbitMQ.


"""

import pika

# --- Connect to RabbitMQ (running on localhost) ---
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# ---  queue ---
# durable=False means the queue is lost if RabbitMQ restarts 
channel.queue_declare(queue='hello')

# --- send message ---
# exchange='' uses the default exchange (direct, routing_key = queue name)
message = "Hello World 2!"
channel.basic_publish(
    exchange='',
    routing_key='hello',
    body=message
)

print(f" [x] Sent '{message}'")

connection.close()
