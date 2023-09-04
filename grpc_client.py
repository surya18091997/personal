import grpc

import proto_example_pb2
import proto_example_pb2_grpc


def main():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = proto_example_pb2_grpc.GreetingServiceStub(channel)
        request = proto_example_pb2.Request(message="Alice")
        response = stub.SayHello(request)
        print("Client received:", response.message)


if __name__ == "__main__":
    main()
