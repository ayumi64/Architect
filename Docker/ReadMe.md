# DVWA
### Pull image
 docker pull sonic64/dvwa

### Start with random mysql password
 docker run -d -p 8901:80 sonic64/dvwa:new

 exposure port: 8901
 server port: 80
 new means: tag

### Start Run
 sudo docker run -d --rm -it -p 80:80 -p 3306:3306 -e MYSQL_PASS="Chang3ME!" sonic64/dvwa

### Test
 http://localhost:8901/setup.php