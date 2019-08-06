# @generated by generate_proto_mypy_stubs.py.  Do not edit!
import sys
from google.protobuf.descriptor import (
    Descriptor as google___protobuf___descriptor___Descriptor,
)

from google.protobuf.message import (
    Message as google___protobuf___message___Message,
)

from snakeskin.protos.common.common_pb2 import (
    Envelope as snakeskin___protos___common___common_pb2___Envelope,
    Status as snakeskin___protos___common___common_pb2___Status,
)

from typing import (
    Optional as typing___Optional,
    Text as typing___Text,
)

from typing_extensions import (
    Literal as typing_extensions___Literal,
)


class StepRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    channel = ... # type: typing___Text
    payload = ... # type: bytes

    def __init__(self,
        *,
        channel : typing___Optional[typing___Text] = None,
        payload : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> StepRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"channel",u"payload"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"channel",b"channel",u"payload",b"payload"]) -> None: ...

class StepResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    payload = ... # type: bytes

    def __init__(self,
        *,
        payload : typing___Optional[bytes] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> StepResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"payload"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"payload",b"payload"]) -> None: ...

class SubmitRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    channel = ... # type: typing___Text
    last_validation_seq = ... # type: int

    @property
    def content(self) -> snakeskin___protos___common___common_pb2___Envelope: ...

    def __init__(self,
        *,
        channel : typing___Optional[typing___Text] = None,
        last_validation_seq : typing___Optional[int] = None,
        content : typing___Optional[snakeskin___protos___common___common_pb2___Envelope] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> SubmitRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"content"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"channel",u"content",u"last_validation_seq"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"content",b"content"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"channel",b"channel",u"content",b"content",u"last_validation_seq",b"last_validation_seq"]) -> None: ...

class SubmitResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    status = ... # type: snakeskin___protos___common___common_pb2___Status
    info = ... # type: typing___Text

    def __init__(self,
        *,
        status : typing___Optional[snakeskin___protos___common___common_pb2___Status] = None,
        info : typing___Optional[typing___Text] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> SubmitResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"info",u"status"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"info",b"info",u"status",b"status"]) -> None: ...