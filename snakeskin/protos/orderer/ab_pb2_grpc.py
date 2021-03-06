# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from snakeskin.protos.common import common_pb2 as snakeskin_dot_protos_dot_common_dot_common__pb2
from snakeskin.protos.orderer import ab_pb2 as snakeskin_dot_protos_dot_orderer_dot_ab__pb2


class AtomicBroadcastStub(object):
  # missing associated documentation comment in .proto file
  pass

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.Broadcast = channel.stream_stream(
        '/orderer.AtomicBroadcast/Broadcast',
        request_serializer=snakeskin_dot_protos_dot_common_dot_common__pb2.Envelope.SerializeToString,
        response_deserializer=snakeskin_dot_protos_dot_orderer_dot_ab__pb2.BroadcastResponse.FromString,
        )
    self.Deliver = channel.stream_stream(
        '/orderer.AtomicBroadcast/Deliver',
        request_serializer=snakeskin_dot_protos_dot_common_dot_common__pb2.Envelope.SerializeToString,
        response_deserializer=snakeskin_dot_protos_dot_orderer_dot_ab__pb2.DeliverResponse.FromString,
        )


class AtomicBroadcastServicer(object):
  # missing associated documentation comment in .proto file
  pass

  def Broadcast(self, request_iterator, context):
    """broadcast receives a reply of Acknowledgement for each common.Envelope in order, indicating success or type of failure
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def Deliver(self, request_iterator, context):
    """deliver first requires an Envelope of type DELIVER_SEEK_INFO with Payload data as a mashaled SeekInfo message, then a stream of block replies is received.
    """
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_AtomicBroadcastServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'Broadcast': grpc.stream_stream_rpc_method_handler(
          servicer.Broadcast,
          request_deserializer=snakeskin_dot_protos_dot_common_dot_common__pb2.Envelope.FromString,
          response_serializer=snakeskin_dot_protos_dot_orderer_dot_ab__pb2.BroadcastResponse.SerializeToString,
      ),
      'Deliver': grpc.stream_stream_rpc_method_handler(
          servicer.Deliver,
          request_deserializer=snakeskin_dot_protos_dot_common_dot_common__pb2.Envelope.FromString,
          response_serializer=snakeskin_dot_protos_dot_orderer_dot_ab__pb2.DeliverResponse.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'orderer.AtomicBroadcast', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
