import io
import cbor2
from cbor2.types import CBORTag
from .replication_manager import (
    GameObjectRegistry,
    ActionsRegistry,
)
from .protocol import *


class RefTag(CBORTag):

    def __init__(self, obj):
        super().__init__(40, obj.id_)


class RefDecoder:

    registry = GameObjectRegistry()

    def __call__(self, decoder, id_, fp, shareable_index=None):
        return self.registry[id_]


class RemoteCallTag(CBORTag):
    def __init__(self, method):
        rem_call_struct = {
            'obj': RefTag(method.__self__),
            'name': method.__name__,
        }
        super().__init__(41, rem_call_struct)


def remote_call_decoder(decoder, rem_call_struct, fp, shareable_index=None):
    return getattr(rem_call_struct['obj'], rem_call_struct['name'])


def remote_call(method, *args, **kwargs):
    struct = {
        'message_type': (message_type.GAME, game_message.CALL),
        'payload': {
            'method': RemoteCallTag(method),
            'args': args,
            'kwargs': kwargs,
        }
    }
    return struct


class ActionTag(CBORTag):

    def __init__(self, action):
        super().__init__(42, action.dump())


class ActionDecoder:

    registry = ActionsRegistry()

    def __call__(self, decoder, action_struct, fp, shareable_index=None):
        print("\n\nACTION STRUCT")
        print(action_struct, self.registry.actions)
        # action = action_struct['action']
        action_name = action_struct.pop('name')
        return self.registry[action_name](**action_struct)


class CreateOrUpdateTag(CBORTag):

    def __init__(self, obj):
        super().__init__(43, obj.dump())


class CreateOrUpdateDecoder:

    registry = GameObjectRegistry()

    def __call__(self, decoder, obj_struct, fp, shareable_index=None):
        return self.registry.load_obj(obj_struct)


def remote_action_append(action):
    msg_struct = {
        "message_type": (message_type.GAME, game_message.ACTION_APPEND),
        "payload": {
            'action': ActionTag(action)
        }
    }
    return msg_struct


def remote_action_remove(action):
    unit = action.target
    action_index = unit.current_action_bar.actions.index(action)
    msg_struct = {
        "message_type": (message_type.GAME, game_message.ACTION_REMOVE),
        "payload": {
            'action_index': action_index,
            'unit': RefTag(unit),
        }
    }
    return msg_struct


mlp_decoder = cbor2.CBORDecoder(semantic_decoders={
    40: RefDecoder(),
    41: remote_call_decoder,
    42: ActionDecoder(),
    43: CreateOrUpdateDecoder(),
})
mlp_encoder = cbor2.CBOREncoder(value_sharing=False)


def mlp_dump(obj, fp):
    mlp_encoder.encode(obj, fp)


def mlp_load(fp):
    return mlp_decoder.decode(fp)


def mlp_dumps(obj):
    buf = io.BytesIO()
    mlp_encoder.encode(obj, buf)
    return buf.getvalue()


def mlp_loads(payload):
    buf = io.BytesIO(payload)
    return mlp_decoder.decode(buf)
