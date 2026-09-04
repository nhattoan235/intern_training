"""
http_receiver.py - HTTP version of the consumer
Run a small web server that listens for requests at /message and prints
their contents.

"""

from flask import Flask, request

app = Flask(__name__)


@app.route('/message', methods=['POST'])
def receive_message():
    data = request.get_json()
    message = data.get('message')
    print(f" [x] Received '{message}'")
    return {"status": "ok"}, 200


if __name__ == '__main__':
    print(" [*] HTTP server listening on http://localhost:5000/message")
    app.run(port=5000)
