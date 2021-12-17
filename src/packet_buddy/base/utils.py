def make_socket(protocol: int):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, protocol)
    s.setsockopt(socket.SOL_IP, socket.IP_HDRINCL, 1)
    return s
