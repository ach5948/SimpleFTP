import os
import sys
import socket
import auth_db
import hashlib
import threading

# andrew: password1
#  guest: password
user_info = {"andrew": '0b14d501a594442a01c6859541bcb3e8164d183d32937b851835442f69d5c94e',
              "guest": '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'}
prefix = "files/"

TCP_IP = "127.0.0.1"
TCP_PORT = 5000
NUM_USERS = 50

BUFFER_SIZE = 1024

def send(client, string):
  try:
    client.send(string)
  except:
    pass
  return

def data_conn(client, sock):
  portmod = 0
  while True:
    try:
      sock.bind((TCP_IP, TCP_PORT + portmod))
      break
    except OSError:
      if portmod >= NUM_USERS:
        send(client, b'425')
        sock.close()
        return None 
      portmod += 1
  # successfull creation
  sock.listen(1)
  send(client, b'225')
  # send portnumber
  send(client, str(sock.getsockname()[1]).encode("utf-8"))
  data = sock.accept()
  return data


def rget(client, filename, user):
  path = prefix + user + "/"
  try:
    with open(path + filename, mode="rb") as fopen:
      send(client, b'150')
      with socket.socket() as temp:
        data, data_addr = data_conn(client, temp)
        if not data:
          # Data connection creation failed
          # client has already been alerted
          return
        l = fopen.read(BUFFER_SIZE)
        while l:
          send(data, l)
          l = fopen.read(BUFFER_SIZE)
        data.close()
      send(client, b'250')
  except FileNotFoundError:
    send(client, b'550')
    return
  return

def rput(client, filename, user):
  if not os.path.exists(prefix + user):
    os.makedirs(prefix + user)
  path = prefix + user + "/"

  send(client, b'150')
  with socket.socket() as temp:
    data, data_addr = data_conn(client, temp)
    if not data:
      return
    l = data.recv(BUFFER_SIZE)
    # Wait to create the file until the first piece of data has been received
    if l:
      with open(path + filename, mode='wb') as fout:
        while l:
          fout.write(l)
          l = data.recv(BUFFER_SIZE)
  send(client, b'250')
  return


def connection(cursor, client):
  """Thread worker function"""

  # Authentication
  send(client, b'330')

  username = client.recv(BUFFER_SIZE).decode("utf-8")

  send(client, b'331')

  pw = client.recv(BUFFER_SIZE)

  if not auth_db.auth_user(cursor, username, pw):
    send(client, b'430')
    client.close()
    return

  send(client, b'230')

  while True:
    cmd = client.recv(BUFFER_SIZE).decode("utf-8")
    cmd = cmd.split(" ")
    cmd[0] = cmd[0].lower()
    
    if cmd[0] == "rget":
      if len(cmd) != 2:
        client.send(b'501')
        continue
      rget(client, cmd[1], username)

    elif cmd[0] == "rput":
      if len(cmd) != 2:
        client.send(b'501')
        continue
      rput(client, cmd[1], username)

    elif cmd[0] == "bye":
      send(client, b'221')
      client.shutdown(socket.SHUT_RDWR)
      client.close()
      return

    else:
      send(client, b'502')
      continue

def main(argv):
  #threads = []
  global TCP_PORT

  db = auth_db.connect_db()
  try:
    with socket.socket() as server:
      while True:
        try:
          server.bind((TCP_IP, TCP_PORT))
          break
        except OSError:
          TCP_PORT += 1
      
      server.listen()
      print("TCP Server listens at: " + str(TCP_IP) + ":" + str(TCP_PORT))
      
      while True:
        client, addr = server.accept()
        print("Connection recieved from: " + str(addr[0]) + ":" + str(addr[1]))
        t = threading.Thread(target=connection, args=[db.cursor(), client])
        #threads.append(t)
        t.start()
  finally:
    db.close()

if __name__ == "__main__":
  main(sys.argv)
  sys.exit()
