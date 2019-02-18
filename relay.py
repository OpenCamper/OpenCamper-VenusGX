from socket import *
import sys

# Sainsmart relay board 8 channels with remote networking shield, python code. https://codecardinal.wordpress.com/2015/03/31/sainsmart-8-channel-relay-controller-python-linux-windows/
if len(sys.argv) != 3:
   sys.exit(2)

relay =  str(sys.argv[1])
state =  str(sys.argv[2])
data_send = "FD0220"

if int(relay) <= 8:
   data_send += "0" + relay
   if int(state) == 0:
      data_send += "00"
   elif int(state) == 1:
      data_send += "01"
	  
elif int(relay) == 9:
   data_send += "F8"
   if int(state) == 0:
      data_send += "80"
   elif int(state) == 1:
      data_send += "88"

data_send += "5D"

s = socket(AF_INET, SOCK_STREAM)
s.connect(("10.10.31.5", 30000))
s.send(data_send.decode('hex'))
data = s.recv(4)
print(data.encode('hex'))