import grpc
import user_pb2
import user_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
        print("Mengirim request ke Go Server menggunakan Python...")
        response = stub.GetUserProfile(user_pb2.UserRequest(user_id=1))
        print(f"Respon dari Server -> Nama: {response.name}, Email: {response.email}")

if __name__ == '__main__':
    run()
