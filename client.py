import grpc
from app.proxyman.command import command_pb2_grpc as command_grpc
from app.proxyman.command import command_pb2 as command
from common.protocol import user_pb2 as user
from common.serial import typed_message_pb2 as serial
from proxy.vless import account_pb2 as vless_account

def get_message_type(message):
    """
    Получает полный путь типа сообщения из объекта proto.Message.
    """
    if message is None:
        return None

    message_type = message.DESCRIPTOR.full_name
    return message_type

def to_typed_message(message):
    """
    Конвертирует proto.Message в TypedMessage с автоматическим определением типа.
    """
    if message is None:
        return None

    # Сериализуем сообщение
    serialized_message = message.SerializeToString()

    # Определяем тип сообщения
    message_type = get_message_type(message)

    # Создаём и возвращаем TypedMessage
    return serial.TypedMessage(
        type=message_type,
        value=serialized_message
    )

class XrayController:
    def __init__(self, api_address, api_port):
        self.channel = grpc.insecure_channel(f'{api_address}:{api_port}')
        self.handler_client = command_grpc.HandlerServiceStub(self.channel)

class UserInfo:
    def __init__(self, uuid, level, in_tag, email, flow=""):
        self.uuid = uuid
        self.level = level
        self.in_tag = in_tag
        self.email = email
        self.flow = flow

def add_vless_user(client, user_info):
    try:
        account = vless_account.Account(
            id=user_info.uuid,
            flow=user_info.flow,
            encryption="none"
        )
        protocol_user = user.User(
            level=user_info.level,
            email=user_info.email,
            account=to_typed_message(account)
        )
        operation = command.AddUserOperation(
            user=protocol_user
        )
        request = command.AlterInboundRequest(
            tag=user_info.in_tag,
            operation=to_typed_message(operation)
        )
        response = client.AlterInbound(request)
        return response
    except grpc.RpcError as e:
        print(f"gRPC error occurred: {e.code()} - {e.details()}")
        # Handle specific errors or log them accordingly
        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
            print("The user already exists.")
        else:
            print("An unknown error occurred.")
        return None

def remove_user(client, user):
    try:
        # Используем email для удаления
        operation = command.RemoveUserOperation(
            email=user.email
        )
        request = command.AlterInboundRequest(
            tag=user.in_tag,
            operation=to_typed_message(operation)
        )
        response = client.AlterInbound(request)
        return response
    except grpc.RpcError as e:
        print(f"gRPC error occurred: {e.code()} - {e.details()}")
        return None

if __name__ == "__main__":
    cfg = {
        "APIAddress": "127.0.0.1",
        "APIPort": 8080
    }
    user_info = UserInfo(
        uuid="099d680f-1e2d-4ef3-9973-64044ff8009b",
        level=0,
        in_tag="vless_tls",
        email="love@xray.com",
        flow="xtls-rprx-vision"
    )

    xray_ctl = XrayController(cfg['APIAddress'], cfg['APIPort'])
    
    # Add VLESS User
    response = add_vless_user(xray_ctl.handler_client, user_info)
    print("Add VLESS User Response:", response)
    
    # Remove User
    #response = remove_user(xray_ctl.handler_client, user_info)
    #print("Remove User Response:", response)