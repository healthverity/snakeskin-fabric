# @generated by generate_proto_mypy_stubs.py.  Do not edit!
import sys
from google.protobuf.descriptor import (
    Descriptor as google___protobuf___descriptor___Descriptor,
    EnumDescriptor as google___protobuf___descriptor___EnumDescriptor,
)

from google.protobuf.message import (
    Message as google___protobuf___message___Message,
)

from typing import (
    List as typing___List,
    Optional as typing___Optional,
    Text as typing___Text,
    Tuple as typing___Tuple,
    cast as typing___cast,
)

from typing_extensions import (
    Literal as typing_extensions___Literal,
)


class ServerStatus(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    class StatusCode(int):
        DESCRIPTOR: google___protobuf___descriptor___EnumDescriptor = ...
        @classmethod
        def Name(cls, number: int) -> str: ...
        @classmethod
        def Value(cls, name: str) -> ServerStatus.StatusCode: ...
        @classmethod
        def keys(cls) -> typing___List[str]: ...
        @classmethod
        def values(cls) -> typing___List[ServerStatus.StatusCode]: ...
        @classmethod
        def items(cls) -> typing___List[typing___Tuple[str, ServerStatus.StatusCode]]: ...
        UNDEFINED = typing___cast(ServerStatus.StatusCode, 0)
        STARTED = typing___cast(ServerStatus.StatusCode, 1)
        STOPPED = typing___cast(ServerStatus.StatusCode, 2)
        PAUSED = typing___cast(ServerStatus.StatusCode, 3)
        ERROR = typing___cast(ServerStatus.StatusCode, 4)
        UNKNOWN = typing___cast(ServerStatus.StatusCode, 5)
    UNDEFINED = typing___cast(ServerStatus.StatusCode, 0)
    STARTED = typing___cast(ServerStatus.StatusCode, 1)
    STOPPED = typing___cast(ServerStatus.StatusCode, 2)
    PAUSED = typing___cast(ServerStatus.StatusCode, 3)
    ERROR = typing___cast(ServerStatus.StatusCode, 4)
    UNKNOWN = typing___cast(ServerStatus.StatusCode, 5)

    status = ... # type: ServerStatus.StatusCode

    def __init__(self,
        *,
        status : typing___Optional[ServerStatus.StatusCode] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> ServerStatus: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"status"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"status",b"status"]) -> None: ...

class LogLevelRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    log_module = ... # type: typing___Text
    log_level = ... # type: typing___Text

    def __init__(self,
        *,
        log_module : typing___Optional[typing___Text] = None,
        log_level : typing___Optional[typing___Text] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> LogLevelRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"log_level",u"log_module"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"log_level",b"log_level",u"log_module",b"log_module"]) -> None: ...

class LogLevelResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    log_module = ... # type: typing___Text
    log_level = ... # type: typing___Text

    def __init__(self,
        *,
        log_module : typing___Optional[typing___Text] = None,
        log_level : typing___Optional[typing___Text] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> LogLevelResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"log_level",u"log_module"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"log_level",b"log_level",u"log_module",b"log_module"]) -> None: ...

class LogSpecRequest(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    log_spec = ... # type: typing___Text

    def __init__(self,
        *,
        log_spec : typing___Optional[typing___Text] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> LogSpecRequest: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"log_spec"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"log_spec",b"log_spec"]) -> None: ...

class LogSpecResponse(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...
    log_spec = ... # type: typing___Text
    error = ... # type: typing___Text

    def __init__(self,
        *,
        log_spec : typing___Optional[typing___Text] = None,
        error : typing___Optional[typing___Text] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> LogSpecResponse: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def ClearField(self, field_name: typing_extensions___Literal[u"error",u"log_spec"]) -> None: ...
    else:
        def ClearField(self, field_name: typing_extensions___Literal[u"error",b"error",u"log_spec",b"log_spec"]) -> None: ...

class AdminOperation(google___protobuf___message___Message):
    DESCRIPTOR: google___protobuf___descriptor___Descriptor = ...

    @property
    def logReq(self) -> LogLevelRequest: ...

    @property
    def logSpecReq(self) -> LogSpecRequest: ...

    def __init__(self,
        *,
        logReq : typing___Optional[LogLevelRequest] = None,
        logSpecReq : typing___Optional[LogSpecRequest] = None,
        ) -> None: ...
    @classmethod
    def FromString(cls, s: bytes) -> AdminOperation: ...
    def MergeFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    def CopyFrom(self, other_msg: google___protobuf___message___Message) -> None: ...
    if sys.version_info >= (3,):
        def HasField(self, field_name: typing_extensions___Literal[u"content",u"logReq",u"logSpecReq"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"content",u"logReq",u"logSpecReq"]) -> None: ...
    else:
        def HasField(self, field_name: typing_extensions___Literal[u"content",b"content",u"logReq",b"logReq",u"logSpecReq",b"logSpecReq"]) -> bool: ...
        def ClearField(self, field_name: typing_extensions___Literal[u"content",b"content",u"logReq",b"logReq",u"logSpecReq",b"logSpecReq"]) -> None: ...
    def WhichOneof(self, oneof_group: typing_extensions___Literal[u"content",b"content"]) -> typing_extensions___Literal["logReq","logSpecReq"]: ...
