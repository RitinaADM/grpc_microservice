# grpc_microservice


proto gen local

python -m grpc_tools.protoc -Iproto --python_out=src/domain/py_proto --grpc_python_out=src/domain/py_proto proto/service.proto

