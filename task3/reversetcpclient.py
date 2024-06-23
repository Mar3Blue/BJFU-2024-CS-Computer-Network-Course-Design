import socket
import random
import sys
import os
import time

def validate_args():
    if len(sys.argv) != 5:
        print("用法: python client.py <服务器IP> <端口号> <最小块长度> <最大块长度>")
        sys.exit(1)

    # 从命令行参数获取服务器IP、端口号、最小和最大块长度
    try:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
        lmin = int(sys.argv[3])
        lmax = int(sys.argv[4])
    except ValueError:
        print("端口号、最小块长度和最大块长度都必须是整数")
        sys.exit(1)

    # 检查服务器IP是否有效
    try:
        socket.inet_aton(server_ip)
    except socket.error:
        print(f"无效的服务器IP地址: {server_ip}")
        sys.exit(1)

    # 检查端口号是否在有效范围内
    if not (0 <= server_port <= 65535):
        print(f"无效的端口号: {server_port}. 端口号应在0到65535之间。")
        sys.exit(1)

    if lmin > lmax or lmax > 512 or lmin*lmax <= 0:
        print(f"无效的块长度: Lmin={lmin}, Lmax={lmax}.块长度应为正整数，最小块长度应小于或等于最大块长度，且最大块长度应小于或等于512")
        sys.exit(1)

    # 参数合法，继续执行程序
    print(f"服务器IP: {server_ip}")
    print(f"端口号: {server_port}")
    print(f"块长度范围: {lmin}-{lmax}")

    return server_ip, server_port, lmin, lmax

def read_file_segments(file_path, segment_size_range):
    # 检查文件路径是否存在且可读
    if not os.path.isfile(file_path):
        print(f"文件不存在或不可读: {file_path}")
        sys.exit(1)

    # 检查文件是否为空
    if os.path.getsize(file_path) == 0:
        print(f"文件为空: {file_path}")
        sys.exit(1)

    segments = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            # 循环将数据分块
            while True:
                seg_size = random.randint(*segment_size_range)  # 随机生成块的长度
                message = file.read(seg_size)   # 获取数据块
                if not message:
                    break
                segments.append(message)    # 将数据块添加到列表中
    except IOError as e:
        print(f"读取文件时出错: {e}")
        sys.exit(1)
    return segments

def main():
    server_ip, server_port, lmin, lmax = validate_args()
    segment_size_range = (lmin, lmax)
    file_path = 'ASCII.txt'
    segment_messages = read_file_segments(file_path, segment_size_range)
    msg_type = [1, 2, 3, 4]
    reversed_data = []  # 用于存储反转后的数据块

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:    # 创建一个TCP套接字
            client_socket.connect((server_ip, server_port))     # 连接到服务器

            # 发送初始化报文，包含块数量
            init_msg = f"{msg_type[0]}:{len(segment_messages)}"
            client_socket.send(init_msg.encode())
            # 等待Agree报文
            response = client_socket.recv(512).decode()
            if int(response) != msg_type[1]:
                print('服务器不同意')
                return

            # 发送Reverse Request报文并接收响应
            for idx, data in enumerate(segment_messages):
                msg = f"{msg_type[2]}:{len(data)}:{data}"   # 创建请求反转报文
                client_socket.sendall(msg.encode('utf-8'))  # 发送请求反转报文
                time.sleep(2)  # 等待2秒，方便观察多个client连接的情况
                try:
                    response_data = client_socket.recv(512).decode('utf-8').split(':')  # 接收来自服务器响应
                    print(f"第{idx + 1}块: {response_data[2]}")
                    reversed_data.append(response_data[2])  # 将反转后的数据块添加到列表
                except Exception as e:
                    print(f"接收数据时出错: {e}")
                    break
    except Exception as e:
        print(f"发生错误: {e}")

    # 输出一个文本文件，该文件是原始文件的全部反转
    with open('reversed_ASCII.txt', 'w') as file:  # 在当前目录中打开一个名为reversed_ASCII.txt的文件。如果该文件不存在，它会自动创建。如果文件已经存在，它将清空文件的内容，然后以写入模式（'w'）打开
        file.write(''.join(reversed_data))  # 将反转后的全部数据写入文件

    client_socket.close()  # 关闭客户端socket

if __name__ == "__main__":
    main()
