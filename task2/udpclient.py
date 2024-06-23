import socket
import sys      # 用于从命令行接收参数
import select   # 可以提供异步I/O操作，用于监听规定时间内是否响应，未响应则超时重传
import time
import math

# Constants
BUFFER_SIZE = 256   # 最大接受字节数
TIMEOUT = 0.1       # 超时时间100ms
MAX_RETRIES = 3     # 最多重传两次
NUM_REQUESTS = 12   # 发送REQUEST报文数目

# 打印使用说明并退出程序
def usage():
    print("用法: python udpclient.py <服务器IP> <服务器端口号>")
    sys.exit(1)

# 检查命令行参数
def parse_arguments():
    if len(sys.argv) != 3:
        usage()
    return sys.argv[1], int(sys.argv[2])

# 验证IP地址的有效性
def validate_ip(ip):
    try:
        socket.inet_aton(ip)
    except socket.error:
        print(f"无效的服务器IP地址: {ip}")
        sys.exit(1)

# 验证端口号的有效性
def validate_port(port):
    if not (0 <= port <= 65535):
        print(f"无效的端口号: {port}. 端口号应在0到65535之间。")
        sys.exit(1)

try:
    SERVER_IP, SERVER_PORT = parse_arguments()  # 从命令行获取 IP 地址和端口号，并将端口号转换为整数
except ValueError as e:
    print(f"参数错误: {e}")
    usage()

validate_ip(SERVER_IP)
validate_port(SERVER_PORT)

def create_socket():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(TIMEOUT)
    return client_socket

client_socket = create_socket()     # 创建一个UDP套接字对象

def send_message(message, address):
    client_socket.sendto(message.encode(), address)

def receive_message():
    return client_socket.recvfrom(BUFFER_SIZE)

# 连接建立方法
def start_connection():
    try:
        # 1. 发送 SYN
        send_message('SYN', (SERVER_IP, SERVER_PORT))
        print("SYN sent")

        # 2. 接收 SYN-ACK
        response, _ = receive_message()
        if response.decode() == 'SYN-ACK':
            print("SYN-ACK received")

            # 3. 发送 ACK
            send_message('ACK', (SERVER_IP, SERVER_PORT))
            print("ACK sent")
            print("Connected")
            return True
        else:
            print("意外的响应:", response.decode())
    except socket.timeout:
        print("连接超时")
    except Exception as e:
        print(f"发生错误: {e}")
    return False

# 关闭连接方法
def stop_connection():
    try:
        # 发送 FIN
        send_message('FIN', (SERVER_IP, SERVER_PORT))
        print("FIN sent")

        # 接收 ACK
        response, _ = receive_message()
        if response.decode() == 'ACK':
            print("ACK received")

            # 接收 FIN
            response, _ = receive_message()
            if response.decode() == 'FIN':
                print("FIN received")

                # 发送 ACK
                send_message('ACK', (SERVER_IP, SERVER_PORT))
                print("ACK sent")
                print("\nDisconnected")
                client_socket.close()
                return True
            else:
                print("意外的响应:", response.decode())
        else:
            print("意外的响应:", response.decode())
    except socket.timeout:
        print("关闭连接超时")
    except ConnectionResetError:
        print("远程主机主动关闭了连接")
    except Exception as e:
        print(f"发生错误: {e}")
    return False

def calculate_rtt_statistics(rtts):
    return {
        'avg': sum(rtts) / len(rtts),
        'std_dev': math.sqrt(sum((rtt - (sum(rtts) / len(rtts))) ** 2 for rtt in rtts) / len(rtts)),
        'min': min(rtts),
        'max': max(rtts)
    }

def run():
    # 初始化报文首部信息，序列号和版本号
    sequence_number = 0
    version = 2

    rtts = []               # 初始化一个列表用于记录所有的RTT数据
    received_packets = 0    # 初始化接收到的UDP数据包数量为0
    try_to_send_count = 0   # 初始化发送UDP数据包次数为0
    server_response_time = 0.0 # 初始化服务器整体响应时间为0
    start_time = 0.0     # 初始化服务器开始响应时间
    end_time = 0.0         # 初始化服务器最后响应时间


    # 开始十二次request发送
    for _ in range(NUM_REQUESTS):
        sequence_number += 1
        message = f"{sequence_number}:{version}:其余部分为空：客户端 -> 服务器" # 封装消息内容，包括序列号、版本号和其它内容

        rtt_start = time.time() * 1000  # 获取当前时间（以毫秒为单位），用于计算RTT
        send_message(message, (SERVER_IP, SERVER_PORT)) # 发送消息到指定IP和端口
        try_to_send_count += 1 # 记录发送次数

        retries = 0 # 初始化重传次数为0
        while True:
            # 使用select模块在100毫秒内监听是否有回传数据可读
            ready = select.select([client_socket], [], [], TIMEOUT)
            # 如果有回传数据可读
            if ready[0]:
                rtt_end = time.time() * 1000    # 获取当前时间（以毫秒为单位），用于计算RTT
                rtt = rtt_end - rtt_start       # 计算RTT
                try:
                    if start_time is None:
                        start_time = time.time()  # 记录第一次发送的开始时间
                    back_data, server_address = receive_message()  # 接收服务器的响应数据
                    received_packets += 1                          # 增加接收到的UDP数据包计数
                    data = back_data.decode().split(':')           # 回传的数据
                    print(f'sequence number: {data[0]} | server IP: {server_address[0]} | server Port: {server_address[1]} | RTT: {rtt} ms')
                    rtts.append(rtt)                               # 将计算的RTT记录在rtt_total中
                    if end_time is None:
                        end_time = time.time()  # 记录第一次接收的结束时间
                    else:
                        end_time = max(end_time, time.time())  # 更新结束时间
                except OSError:
                    print('接收数据包超出预期长度或套接字在操作过程中被关闭')
                break
            else:
                retries += 1                # 重传计数+1
                print(f"sequence no: {sequence_number}, 请求超时")
                if retries >= MAX_RETRIES:  # 如果已重传两次仍失败，放弃本次重传退出内部循环
                    break
                rtt_start = time.time() * 1000  #重新获取当前时间，用于计算RTT
                send_message(message, (SERVER_IP, SERVER_PORT))  # 尝试重传
                try_to_send_count += 1          # 发送次数+1

    loss_rate = (1 - received_packets / try_to_send_count) * 100  # 计算丢包率
    rtt_stats = calculate_rtt_statistics(rtts)

    server_response_time = end_time - start_time # 服务器总响应时间

    # 打印汇总信息，包括接收到的UDP数据包数、丢包率、服务器响应时间、RTT的最大值、最小值、平均值和标准差
    if received_packets > 0:
        print("\n--- 汇总消息 ---")
        print(f'\n接收到的 udp packets 数目:  {received_packets}')
        print(f'丢包率:  {loss_rate}%')
        print(f'server 的整体响应时间:  {server_response_time} s')
        print(f'最大 RTT: {rtt_stats["max"]} ms')
        print(f'最小 RTT: {rtt_stats["min"]} ms')
        print(f'平均 RTT: {rtt_stats["avg"]} ms')
        print(f'RTT 的标准差: {rtt_stats["std_dev"]} ms')
    else:
        print("未接收到任何报文")

if __name__ == '__main__':
    if start_connection():
        run()
        stop_connection()