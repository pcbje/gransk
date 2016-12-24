curl -o docker-compose.yml -X GET https://raw.githubusercontent.com/pcbje/gransk/master/docker-compose.yml
docker-compose up -d
docker pull pcbje/gransk
if [ "`uname`" == "Darwin" ]; then IP=`docker-machine ip`; else IP=localhost; fi
echo "Go to: http://$IP:8084"
docker run -p 8084:8084 -i -t pcbje/gransk
