import os

from pyflink.common import Configuration
from pyflink.table import EnvironmentSettings, TableEnvironment

def main():
    # create a streaming TableEnvironment
    config = Configuration()
    config.set_string('execution.buffer-timeout', '1 min')
    config.set_string('parallelism.default', '1')
    
    env_settings = EnvironmentSettings \
        .new_instance() \
        .in_streaming_mode() \
        .with_configuration(config) \
        .build()

    # create table environment
    tbl_env = TableEnvironment.create(env_settings)
    
    # add kafka connector dependency
    kafka_jar = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'flink-sql-connector-kafka-1.17.1.jar')

    tbl_env.get_config()\
           .set("pipeline.jars", "file://{}".format(kafka_jar))
           
    print(tbl_env.get_config().get_configuration())


    ###############################################################
    # Create Kafka Source Table
    ###############################################################
    source_ddl_tbl = """
        CREATE TABLE `productsales_source` (
            `seller_id` STRING,
            `product` STRING,
            `quantity` INT,
            `product_price` DOUBLE,
            `sales_date` STRING
        ) WITH (
          'connector' = 'kafka',
          'topic' = 'productsales',
          'properties.bootstrap.servers' = 'localhost:9092',
          'properties.group.id' = 'source-demo',
          'scan.startup.mode' = 'latest-offset',
          'format' = 'json',
          'json.ignore-parse-errors' = 'true'
        );
    """
    tbl_env.execute_sql(source_ddl_tbl)

    tbl = tbl_env.from_path('productsales_source')
    print("\nProduct Sales Kafka Source Schema")
    tbl.print_schema()

    ###############################################################
    # Create Kafka Sink Table
    ###############################################################
    sink_ddl_table = """
        CREATE TABLE `productsales_sink` (
            `seller_id` STRING,
            `product` STRING,
            `quantity` INT,
            `product_price` DOUBLE,
            `sales_date` STRING
        ) WITH (
          'connector' = 'kafka',
          'topic' = 'productsales_out',
          'properties.group.id' = 'productsales_sink',
          'properties.bootstrap.servers' = 'localhost:9092',
          'format' = 'json'
        );
    """
    tbl_env.execute_sql(sink_ddl_table)

    insert_into = """
        INSERT INTO productsales_sink 
         SELECT * FROM productsales_source
    """
    tbl_env.execute_sql(insert_into)
    
    tale_sink = tbl_env.from_path("productsales_sink")
    print(tale_sink.explain())

if __name__ == '__main__':
    main()

