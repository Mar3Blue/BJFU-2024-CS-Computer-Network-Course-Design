import socket
import select

# 定义一个处理客户端请求的函数
def handle_client(client_socket, client_address, message):
    msg_type = [1, 2, 3, 4]
    print(f"接受来自{client_address}的连接")
    
    try:
        data = message.decode('utf-8').split(':')
        msg_id = int(data[0])

        if msg_id == msg_type[0]:
            response = str(msg_type[1])
        elif msg_id == msg_type[2]:
            response = f"{msg_type[3]}:{data[1]}:{data[2][::-1]}"
        else:
            response = "无效的消息类型"
            
        client_socket.send(response.encode('utf-8'))
    except Exception as e:
        print(f"处理客户端{client_address}时出错: {e}")
        client_socket.send("数据处理错误".encode('utf-8'))
    except (IndexError, ValueError) as e:
        print(f"处理来自{client_address}的数据时错误: {e}")
        client_socket.send("数据处理错误".encode('utf-8'))

def main():
    server_ip = '0.0.0.0'   # 监听所有接口
    server_port = 1235      # 服务器端口号

    # 创建TCP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # 创建一个新的 TCP/IP 套接字，使用 IPv4 地址
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 告诉操作系统允许重用本地地址，这样如果程序异常终止或服务器重启，可以快速绑定到同一个地址上，从而避免因地址不可用而导致的错误
    server_socket.bind((server_ip, server_port))    # 将socket绑定到指定的IP地址和端口
    server_socket.listen(9)   # 开始监听传入连接，最多允许9个连接排队
    server_socket.setblocking(0)  # 设置套接字为非阻塞模式
    print(f"服务器正在监听{server_ip}:{server_port}")

    epoll = select.epoll()
    epoll.register(server_socket.fileno(), select.EPOLLIN)

    connections = {}
    addresses = {}
    messages = {}

    try:
        while True:
            events = epoll.poll(1)
            for fileno, event in events:
                if fileno == server_socket.fileno():
                    client_socket, client_address = server_socket.accept()
                    client_socket.setblocking(0)
                    epoll.register(client_socket.fileno(), select.EPOLLIN)
                    connections[client_socket.fileno()] = client_socket
                    addresses[client_socket.fileno()] = client_address
                    messages[client_socket.fileno()] = b''
                    print(f"与{client_address}建立连接")
                elif event & select.EPOLLIN:
                    client_socket = connections[fileno]
                    message = client_socket.recv(512)
                    if message:
                        messages[fileno] += message
                        epoll.modify(fileno, select.EPOLLOUT)
                    else:
                        print(f"连接被{addresses[fileno]}关闭")
                        epoll.unregister(fileno)
                        client_socket.close()
                        del connections[fileno]
                        del addresses[fileno]
                        del messages[fileno]
                elif event & select.EPOLLOUT:
                    client_socket = connections[fileno]
                    if messages[fileno]:
                        handle_client(client_socket, addresses[fileno], messages[fileno])
                        messages[fileno] = b''
                    epoll.modify(fileno, select.EPOLLIN)
                elif event & select.EPOLLHUP:
                    print(f"连接被{addresses[fileno]}关闭")
                    epoll.unregister(fileno)
                    connections[fileno].close()
                    del connections[fileno]
                    del addresses[fileno]
                    del messages[fileno]
    finally:
        epoll.unregister(server_socket.fileno())
        epoll.close()
        server_socket.close()

if __name__ == "__main__":
    main()
