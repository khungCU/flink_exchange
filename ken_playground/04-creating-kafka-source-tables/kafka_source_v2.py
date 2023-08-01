import os

from pyflink.common import Configuration
from pyflink.table import EnvironmentSettings, TableEnvironment, StreamTableEnvironment
from pyflink.datastream import StreamExecutionEnvironment

def main():
    
    # create a streaming TableEnvironment
    env = StreamExecutionEnvironment.get_execution_environment()
    
    settings = EnvironmentSettings.new_instance()\
                      .in_streaming_mode()\
                      .build()
    
    # config = Configuration()
    # config.set_string('execution.buffer-timeout', '1 min')
    # env_settings = EnvironmentSettings \
    #     .new_instance() \
    #     .in_streaming_mode() \
    #     .with_configuration(config) \
    #     .build()

    # create table environment
    # tbl_env = TableEnvironment.create(env_settings)
    
    tbl_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                            environment_settings=settings)
    
    # add kafka connector dependency
    kafka_jar = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'flink-sql-connector-kafka-1.17.1.jar')

    tbl_env.get_config()\
           .set("pipeline.jars", "file://{}".format(kafka_jar))
           
    print(tbl_env.get_config().get_configuration())

    ###############################################################
    # Create Kafka Source Table
    ###############################################################
    source_ddl = """
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
    tbl_env.execute_sql(source_ddl)

    black_hole = """
        CREATE TABLE blackhole (
                seller_id VARCHAR,
                product VARCHAR,
                quantity INT,
                product_price DOUBLE,
                sales_date VARCHAR
        ) WITH (
                'connector' = 'blackhole'
        );
    """
    tbl_env.execute_sql(black_hole)
    
    insert_into = """
        INSERT INTO blackhole 
         SELECT * FROM productsales_source
    """

    tbl_env.execute_sql(insert_into)
    
    # Blackhole is as it called it can be a source hence we can't select the stream  and print it
    # Blackhole can only be the sink
    
if __name__ == '__main__':
    main()

