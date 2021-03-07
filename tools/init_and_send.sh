for i in {1..5}
do
   echo "Welcome $i times"
done

python3 readfromsocket.py --port 3002 --data "SET:MYCALLSIGN:DJ2LS"
python3 readfromsocket.py --port 3000 --data "SET:MYCALLSIGN:DH3WO"
sleep 3
#python3 readfromsocket.py --port 3002 --data "CQCQCQ"
#sleep 5
python3 readfromsocket.py --port 3002 --data "PING:DH3WO"
sleep 5
python3 readfromsocket.py --port 3002 --data "ARQ:CONNECT:DH3WO"
#sleep 1
python3 readfromsocket.py --port 3000 --data "GET:ARQ_STATE"
sleep 5
echo "ACHTUNG DATEI"
python3 socketclient.py --port 3002 --random 100


sleep 10
python3 readfromsocket.py --port 3000 --data "ARQ:DISCONNECT"
echo "ende..."
