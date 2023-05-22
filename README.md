## ports:

* 8000: Server
* 5000: Logstash TCP input
* 5044: Logstash Beats input
* 9600: Logstash monitoring API
* 9200: Elasticsearch HTTP
* 9300: Elasticsearch TCP transport
* 5601: Kibana

## Commands

`docker-compose build`

`docker-compose up -d`

`docker-compose down -v`