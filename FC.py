import os
import sys
import socket

codes = {150 : "File status okay; about to open data connection",
         221 : "Service closing control connection",
         225 : "Data connection open; no transfer in progress",
         230 : "User logged in, proceed",
         250 : "Requested file action okay, completed",
         330 : "Connection Successful. Authetication Required",
         331 : "User name okay, need password",
         425 : "Can't open data connection",
         430 : "Invalid username or password",
         501 : "Syntax error in parameters or arguments",
         502 : "Command not implemented",
         550 : "Requested action not taken. File unavailable",
         553 : "Requested action not taken. File name not allowed"}

BUFFER_SIZE = 1024

def get_code(client):
  try:
    # codes are 3 digits
    code = int(client.recv(3).decode("utf-8"))
  except:
    return

  if code in codes:
    print(str(code) + ": " + codes[code])
  else:
    print("Unknown code: '" + str(code) + "'")

  return code


def close_connection(client):
  code = None
  try:
    client.send(b'bye')
    code = get_code(client)
  except:
    pass

  try:
    client.close()
  except:
    pass

  client = None
  if code == 221:
    print("Connection closed successfully")

def open_data(client, sock):
  code = get_code(client)
  if code != 225:
    # data connection failed
    sock.close()
    return 0
  try:
    # get port number
    port = int(client.recv(BUFFER_SIZE).decode("utf-8"))
  except:
    sock.close()
    return 0
  sock.connect((client.getpeername()[0], port))
  return 1

def rftp(client, host, port, user, pw):
  try:
    port = int(port)
  except:
    print("Invalid port number '" + str(port) + "'. Port number must be an integer")
    return
  
  addr = (host, port)
  
  client.connect(addr)
  
  code = get_code(client)
  if code != 330:
    # Connection not successful 
    return
 
  client.send(user.encode("utf-8"))
  code = get_code(client)
  if code != 331:
    # username not accepted
    return
 
  client.send(pw.encode("utf-8"))
  code = get_code(client)
  if code != 230:
    # password not accepted
    return
  return


def rget(client, filename):
  if os.path.exists(filename):
    oops = input("File will be overwritten. Continue[y/n]:")
    if oops.lower()[0] != "y":
      return
  
  client.send(("rget " + filename).encode("utf-8"))
  code = get_code(client)
  if code != 150:
    return

  with socket.socket() as data:
    if not open_data(client, data):
      return
    with open(filename, mode='wb') as fout:
      l = data.recv(BUFFER_SIZE)
      while l:
        fout.write(l)
        l = data.recv(BUFFER_SIZE)

  code = get_code(client)
  if code == 250:
    print("Transmission Successful")
  else:
    print("Transmission Failed")
  return


def rput(client, filename):
  try:
    with open(filename, mode="rb") as fopen:
      fname = os.path.basename(filename)
      client.send(("rput " + fname).encode("utf-8"))
      code = get_code(client)
      if code != 150:
        return

      with socket.socket() as data:
        if not open_data(client, data):
          return
        l = fopen.read(BUFFER_SIZE)
        while l:
          data.send(l)
          l = fopen.read(BUFFER_SIZE)
  except FileNotFoundError:
    print("File '" + filename + "' Not Found")
    return
  code = get_code(client)

  if code == 250:
    print("Transmission Successful")
  else:
    print("Transmission Failed")
  return


def main(argv):

  client = None
  while True:
    cmd = input('> ')
    cmd = cmd.split(" ")
    cmd[0] = cmd[0].lower()
    
    if cmd[0] == "rftp":
      if len(cmd) < 4:
        print("Not enough arguments")
        print("Usage: rftp <FTP Server Address> <User> <Password>")
        continue
      
      if len(cmd) > 4:
        print("Too many arguments")
        print("Usage: rftp <FTP Server Address> <User> <Password>")
        continue
      
      addr = cmd[1].split(":")
      
      if len(addr) != 2:
        print("Invalid address: '" + cmd[1] + "'")
        print("Server Address Structure is: Address:Port")
        continue
      
      # close old connection
      close_connection(client)
      
      client = socket.socket()
     
      rftp(client, addr[0], addr[1], cmd[2], cmd[3])
   
    elif cmd[0] == "rget":
      if client == None:
        print("No active connection. Connect with rftp")
        continue
      
      if len(cmd) < 2:
        print("Not enough arguments")
        print("Usage: rget <File Name>")
        continue
      
      if len(cmd) > 2:
        print("Too many arguments")
        print("Usage: rget <File Name>")
        continue
      
      rget(client, cmd[1])
   
    elif cmd[0] == "rput":
      if client == None:
        print("No active connection. Connect with rftp")
        continue

      if len(cmd) < 2:
        print("Not enough arguments")
        print("Usage: rput <File Name>")
        continue

      if len(cmd) > 2:
        print("Too many arguments")
        print("Usage: rput <File Name>")
        continue
      
      rput(client, cmd[1])
   
    elif cmd[0] == "disconnect":
      if client == None:
        print("No active connection to disconnect.")
        continue
      close_connection(client)
      continue
   
    elif cmd[0] == "exit":
      if client != None:
        close_connection(client)
      return
   
    else:
      print("Unknown Command '" + cmd[0] + "'")
      print("Usage:")
      print("\trftp <FTP Server Address> <User> <Password>")
      print("\trget <File Name>")
      print("\trput <File Name>")
      print("\tdisconnect")
      print("\texit")
      continue

if __name__ == "__main__":
  main(sys.argv)
  sys.exit()
