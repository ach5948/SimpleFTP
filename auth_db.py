import sys
import string
import random
import getpass
import mysql.connector

def add_user(db, cursor, username, password):
  # check if username already exists
  cursor.execute("SELECT username FROM users WHERE username=%s;", (username,))
  if cursor.fetchall():
    print("Username '" + username + "' already exists")
    return False

  # generate salt
  salt = ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(64))

  try:
    cursor.execute("INSERT INTO users VALUES (%s, SHA2(%s, 256), %s);", (username, salt + password, salt))
  except mysql.connector.IntegrityError as err:
    print("Error: {}".format(err))
    return False

  db.commit()
  return True

def auth_user(cursor, username, password):
  query = "SELECT * FROM users WHERE username=%s and password=SHA2(CONCAT(salt, %s), 256)"
  data = (username, password)
  cursor.execute(query, data)
  # return whether there was a result or not
  return bool(cursor.fetchall())

def connect_db(sqluser="dbadmin", host="localhost", db="auth"):
  """
  Attempt to connect to an existing database. If it doesn't exist, it creates it.
  """
  try:
    db = mysql.connector.connect(user=sqluser, host=host, db=db)
    cur = db.cursor()
  except mysql.connector.errors.ProgrammingError:
    db = mysql.connector.connect(user=sqluser, host=host)
    cur = db.cursor()
    cur.execute("CREATE DATABASE " + db)
    cur.execute("USE " + db)
  return db


def main(argv):
  db = connect_db()
  
  try:
    while True:
      cmd = input('> ')
      cmd = cmd.split(" ")
      cmd[0] = cmd[0].lower()
      
      if cmd[0] == "create":
        user = input('Username: ')
        if len(user) < 3:
          print("Username must be at least 3 characters long")
        
        pw = getpass.getpass()
        if len(pw) < 8:
          print("Password must be at least 8 characters long")
          return False
        
        confirm = getpass.getpass('Confirm Password: ')
        if confirm != pw:
          print("Passwords do not match")
        
        if add_user(db, cur, user, pw):
          print("Account successfully created")
      
      elif cmd[0] == "login":
        user = input('Username: ')
        pw = getpass.getpass()
        if auth_user(cur, user, pw):
          print("Access Granted")
        else:
          print("Access Denied")
      
      elif cmd[0] == "exit":
        return
      
      else:
        print("Unknown Command '" + cmd[0] + "'")
        print("Valid Commands are 'create' and 'login'")

  finally:
    # Close the database no matter what happens
    db.close()

if __name__ == "__main__":
  main(sys.argv)
  sys.exit()

