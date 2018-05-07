# SimpleFTP
A simple FTP client and server written with sockets in python

The implemented commands are:
rftp <FTP Server Address> <User> <Password>
rget <File Name>
rput <File Name>

This is purely a programming exercise. The code is by no means secure. Not that FTP was ever secure.

The accepted usernames and passwords are currently stored as a dictionary in the server.
I'm planning on moving these to a database and adding a way to create an account at some point.

The current usernames and passwords are:
andrew password1
guest password
