# grpc_microservice


proto gen local

python -m grpc_tools.protoc -Iproto --python_out=src/infra/adapters/inbound/grpc/py_proto --grpc_python_out=src/infra/adapters/inbound/grpc/py_proto proto/service.proto

from src.infra.adapters.inbound.grpc.py_proto import service_pb2 as service__pb2
