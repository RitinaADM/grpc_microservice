При обновлении proto файлов:

``` bash
python -m grpc_tools.protoc -Iproto --python_out=src/infra/adapters/inbound/grpc/py_proto --grpc_python_out=src/infra/adapters/inbound/grpc/py_proto proto/service.proto
```
В файле service_pb2_grpc.py исправить импорт

Заменить

    import service_pb2 as service__pb2

На

    from src.infra.adapters.inbound.grpc.py_proto import service_pb2 as service__pb2
