import socket
import threading
import argparse
import time
import sys

# ---------- colors ----------
RESET = "\033[0m"
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"

def ts():
    return time.strftime("[%H:%M:%S]")

# ---------- args ----------
parser = argparse.ArgumentParser(description="minimal irc client (raw sockets)")
parser.add_argument("--server", default="irc.libera.chat")
parser.add_argument("--port", type=int, default=6667)
parser.add_argument("--nick", default="socketUser42")
parser.add_argument("--channel", default="#test")

args = parser.parse_args()

server = args.server
port = args.port
nick = args.nick
channel = args.channel
realname = "learning irc"

connected = True

# ---------- socket ----------
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((server, port))

# handshake
sock.send(f"NICK {nick}\r\n".encode())
sock.send(f"USER {nick} 0 * :{realname}\r\n".encode())

print(GREEN + ts(), "connected to", server + RESET)

# ---------- receive loop ----------
def listen():
    global connected
    while connected:
        try:
            data = sock.recv(4096).decode(errors="ignore")
            if not data:
                break

            for line in data.split("\r\n"):
                if not line:
                    continue

                # keepalive
                if line.startswith("PING"):
                    token = line.split()[1]
                    sock.send(f"PONG {token}\r\n".encode())
                    continue

                # basic message parsing
                if "PRIVMSG" in line:
                    try:
                        prefix, msg = line.split(" PRIVMSG ", 1)
                        user = prefix.split("!")[0][1:]
                        text = msg.split(" :", 1)[1]
                        print(BLUE + ts(), f"<{user}>", text + RESET)
                    except:
                        print(YELLOW + ts(), line + RESET)
                else:
                    print(YELLOW + ts(), line + RESET)

        except:
            break

    connected = False

# background listener
threading.Thread(target=listen, daemon=True).start()

# join channel
sock.send(f"JOIN {channel}\r\n".encode())
print(GREEN + ts(), "joined", channel + RESET)

# ---------- input loop ----------
while connected:
    try:
        msg = input()

        if msg.startswith("/quit"):
            sock.send(b"QUIT :leaving\r\n")
            print(RED + ts(), "disconnected" + RESET)
            connected = False
            sock.close()
            sys.exit()

        elif msg.startswith("/join"):
            parts = msg.split()
            if len(parts) == 2:
                channel = parts[1]
                sock.send(f"JOIN {channel}\r\n".encode())
                print(GREEN + ts(), "switched to", channel + RESET)
            else:
                print("usage: /join #channel")

        else:
            sock.send(f"PRIVMSG {channel} :{msg}\r\n".encode())

    except KeyboardInterrupt:
        sock.send(b"QUIT :ctrl-c\r\n")
        sock.close()
        sys.exit()
