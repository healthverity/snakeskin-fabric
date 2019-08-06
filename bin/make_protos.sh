#!/bin/bash
# Creates python protobufs from .proto files

python3 -m grpc.tools.protoc \
    -I./\
    --python_out=./ \
    --mypy_out=./ \
    --grpc_python_out=./ \
    $(find snakeskin/protos | egrep '.proto$')
