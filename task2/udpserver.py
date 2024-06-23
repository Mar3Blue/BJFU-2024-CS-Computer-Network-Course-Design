import socket
import random
import time

IP = '0.0.0.0'  # 监听所有可用的网络接口
PORT = 1235
BUFFER_SIZE = 256  # 最大接受字节数
DROP_RATE = 0.50   # 丢包率设为50%

def create_server_socket(ip, port):
    """创建并绑定UDP服务器套接字"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # AF_INET表示IPv4，SOCK_DGRAM表示UDP
    server_socket.bind((ip, port))  # 绑定套接字到指定的IP地址和端口
    return server_socket

def handle_client_message(message, client_address, server_socket):
    """处理客户端消息"""
    try:
        message_decoded = message.decode()
        if message_decoded == 'SYN':  # 处理连接建立的第一步
            print(f"{client_address} sent SYN")
            send_syn_ack(server_socket, client_address)
        elif message_decoded == 'ACK':  # 处理连接建立的第三步
            print(f"{client_address} sent ACK, connection established")
        elif message_decoded == 'FIN':  # 处理连接释放的第一步
            print(f"{client_address} sent FIN")
            send_ack(server_socket, client_address)
            time.sleep(0.1)  # 模拟一个处理延迟
            send_fin(server_socket, client_address)
        elif message_decoded == 'ACK-FIN':  # 处理连接释放的第四步
            print(f"{client_address} sent ACK-FIN, connection terminated")
        else:
            process_data_message(message_decoded, client_address, server_socket)
    except (UnicodeDecodeError, ValueError) as e:
        print(f"解码或处理来自{client_address}的消息时出错: {e}")

def send_syn_ack(server_socket, client_address):
    """发送 SYN-ACK 消息给客户端"""
    syn_ack_message = 'SYN-ACK'
    server_socket.sendto(syn_ack_message.encode(), client_address)
    print("SYN-ACK sent")

def send_ack(server_socket, client_address):
    """发送确认信息 ACK 给客户端"""
    ack_message = 'ACK'
    server_socket.sendto(ack_message.encode(), client_address)
    print("ACK sent")

def send_fin(server_socket, client_address):
    """发送 FIN 消息给客户端"""
    fin_message = 'FIN'
    server_socket.sendto(fin_message.encode(), client_address)
    print("FIN sent")

def process_data_message(message, client_address, server_socket):
    """处理数据消息"""
    try:
        sequence_number, ver, _ = message.split(':')  # 分割接收到的数据，获取序列号(sequence_number)、版本号(ver)和其他数据 (_)
        server_time = time.strftime('%H:%M:%S', time.localtime())  # 获取当前系统时间，并格式化为 hh:mm:ss
        response = f"{sequence_number}:{ver}:{server_time}:服务器 -> 客户端"
        
        if random.random() >= DROP_RATE:
            print(f"响应具有序列号{sequence_number}的数据包")
            time.sleep(0.00035)  # 模拟RTT响应时间
            server_socket.sendto(response.encode(), client_address)  # 发送响应数据给客户端
        else:
            print(f"丢弃具有序列号{sequence_number}的数据包")
    except ValueError as e:
        print(f"处理数据消息时出错: {e}")

def main():
    server_socket = create_server_socket(IP, PORT)
    print(f"UDP 服务器已启动并在监听 {IP}:{PORT}")
    
    while True:
        try:
            message, client_address = server_socket.recvfrom(BUFFER_SIZE)
            handle_client_message(message, client_address, server_socket)
        except OSError as e:
            print(f"套接字错误: {e}")
        except KeyboardInterrupt:    # 捕获键盘中断
            print("服务器关闭中.")
            break
    
    server_socket.close()  # 关闭服务器套接字
    print("关闭服务器套接字.")

if __name__ == "__main__":
    main()
