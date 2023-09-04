from concurrent import futures

import grpc
from flask import Flask

import proto_example_pb2
import proto_example_pb2_grpc

app = Flask(__name__)


class GreetingServicer(proto_example_pb2_grpc.GreetingServiceServicer):
    def SayHello(self, request, context):
        response = proto_example_pb2.Response()
        response.message = f"Hello, {request.message}!"
        return response


server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
proto_example_pb2_grpc.add_GreetingServiceServicer_to_server(GreetingServicer(), server)
server.add_insecure_port("[::]:50051")


@app.route("/")
def index():
    return "gRPC Server is running!"


if __name__ == "__main__":
    server.start()
    app.run(host="0.0.0.0", port=5001)
