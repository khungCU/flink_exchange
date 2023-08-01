# pyflink-hands-on


## Create a kafka connector
cd local-playgroud
curl -i -X POST -H "Accept:application/json" -H  "Content-Type:application/json" http://localhost:8083/connectors/ -d @register-postgres.json

## Checking if kafka connector is running
curl http://localhost:8083/connectors/claims-connector/status | jq

## Checking the messages inside the topic
docker exec -it broker /kafka/bin/kafka-console-consumer.sh \
    --bootstrap-server broker:9092 \
    --from-beginning \
    --property print.key=true \
    --topic pg_claims.claims.accident_claims

## Access to the ksql flink
docker exec -it sql-client bash
${FLINK_HOME}/bin/sql-client.sh embedded -d ${FLINK_HOME}/conf/sql-client-conf.yaml -l ${FLINK_HOME}/lib/

## Register a Postgres catalog, so you can access the metadata of the external tables over JDBC:
CREATE CATALOG postgres WITH (
    'type'='jdbc',
    'property-version'='1',
    'base-url'='jdbc:postgresql://postgres:5432/',
    'default-database'='postgres',
    'username'='postgres',
    'password'='postgres'
);


## Create a changelog table to consume the change events from the pg_claims.claims.accident_claims topic, with the same schema as the accident_claims source table, that consumes the debezium-json format:
CREATE TABLE accident_claims
WITH (
  'connector' = 'kafka',
  'topic' = 'pg_claims.claims.accident_claims',
  'properties.bootstrap.servers' = 'broker:9092',
  'properties.group.id' = 'test-consumer-group',
  'value.format' = 'debezium-json',
  'scan.startup.mode' = 'earliest-offset'
 )
LIKE postgres.postgres.`claims.accident_claims` ( 
EXCLUDING OPTIONS);

## and register a reference members table:
CREATE TABLE members
LIKE postgres.postgres.`claims.members` ( 
INCLUDING OPTIONS);

## visualized the result
CREATE TABLE agg_insurance_costs (
  es_key STRING PRIMARY KEY NOT ENFORCED,
  insurance_company STRING,
  accident_detail STRING,
  accident_agg_cost DOUBLE
) WITH (
  'connector' = 'print'
);

## submit a continuous query to the Flink cluster
INSERT INTO agg_insurance_costs
SELECT UPPER(SUBSTRING(m.insurance_company,0,4) || '_' || SUBSTRING (ac.accident_detail,0,4)) es_key,
       m.insurance_company,
       ac.accident_detail,
       SUM(ac.claim_total) member_total
FROM accident_claims ac
JOIN members m
ON ac.member_id = m.id
WHERE ac.claim_status <> 'DENIED'
GROUP BY m.insurance_company, ac.accident_detail;

## Read the result streams
select * from agg_insurance_costs;

