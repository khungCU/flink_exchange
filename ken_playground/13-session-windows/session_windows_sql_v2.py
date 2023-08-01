import os

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings


def main():
    # Create streaming environment
    env = StreamExecutionEnvironment.get_execution_environment()

    settings = EnvironmentSettings.new_instance()\
                      .in_streaming_mode()\
                      .build()

    # create table environment
    tbl_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                            environment_settings=settings)

    # add kafka connector dependency
    kafka_jar = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'flink-sql-connector-kafka-1.17.1.jar')

    tbl_env.get_config()\
            .get_configuration()\
            .set_string("pipeline.jars", "file://{}".format(kafka_jar))

    #######################################################################
    # Create Kafka Source Table with DDL
    #
    # - The Table API Descriptor source code is undergoing a refactor
    #   and currently has a bug associated with time (event and processing)
    #   so it is recommended to use SQL DDL to define sources / sinks
    #   that require time semantics.
    #   - http://apache-flink-mailing-list-archive.1008284.n3.nabble.com/DISCUSS-FLIP-129-Refactor-Descriptor-API-to-register-connector-in-Table-API-tt42995.html
    #   - http://apache-flink-user-mailing-list-archive.2336050.n4.nabble.com/PyFlink-Table-API-quot-A-group-window-expects-a-time-attribute-for-grouping-in-a-stream-environment--td36578.html
    #######################################################################
    src_ddl = """
        CREATE TABLE salesitems (
            seller_id VARCHAR,
            product VARCHAR,
            quantity INT,
            product_price DOUBLE,
            sale_ts BIGINT,
            proctime TIMESTAMP_LTZ(3) METADATA FROM 'timestamp',
            WATERMARK FOR proctime AS proctime - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'salesitems',
            'scan.startup.mode' = 'latest-offset',
            'properties.bootstrap.servers' = 'localhost:9092',
            'properties.group.id' = 'session-windows-sql',
            'format' = 'json'
        )
    """

    tbl_env.execute_sql(src_ddl)

    # create and initiate loading of source Table
    tbl = tbl_env.from_path('salesitems')

    print('\nSource Schema')
    tbl.print_schema()

    #####################################################################
    # Define Session Window Aggregate Calculation of Revenue per Seller
    #
    # - Calculate last 30 seconds of revenue per seller
    # - incrementing (updating) every 20 seconds
    #####################################################################
    sql = """
        SELECT
          seller_id,
          SESSION_START(proctime, INTERVAL '20' SECONDS) AS window_start,
          SESSION_END(proctime, INTERVAL '20' SECONDS) AS window_end,
          SUM(quantity * product_price) AS window_sales
        FROM salesitems
        GROUP BY
          SESSION(proctime, INTERVAL '20' SECONDS),
          seller_id
    """
    sql_test = """
        SELECT 
            seller_id,
            product,
            quantity,
            product_price,
            sale_ts,
            proctime
        FROM salesitems;
    """
    windowed_rev = tbl_env.sql_query(sql)

    print('\nProcess Sink Schema')
    windowed_rev.print_schema()

    ###############################################################
    # Create Kafka Sink Table
    ###############################################################
    sink_ddl = """
        CREATE TABLE processedsales2 (
            seller_id VARCHAR,
            window_start TIMESTAMP,
            window_end TIMESTAMP,
            window_sales DOUBLE
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'processedsales2',
            'properties.bootstrap.servers' = 'localhost:9092',
            'format' = 'json'
        )
    """
    sink_ddl_2 = """
        CREATE TABLE test_print_sink (
            seller_id VARCHAR,
            product VARCHAR,
            quantity INT,
            product_price DOUBLE,
            sale_ts BIGINT,
            proctime TIMESTAMP_LTZ(3) NOT NULL
        ) WITH (
            'connector' = 'print'
        );
    """
    tbl_env.execute_sql(sink_ddl)

    # write time windowed aggregations to sink table
    windowed_rev.execute_insert('processedsales2').wait()
    #windowed_rev.execute_insert('test_print_sink').wait()

    tbl_env.execute('sql-session-windows-demo')


if __name__ == '__main__':
    #  proctime AS PROCTIME()
    # +I[KC, Toothpaste, 5, 4.99, 1688142469381, 2023-06-30T16:27:49.598Z]
    
    # `proctime` TIMESTAMP_LTZ(3) METADATA FROM 'timestamp'
    # +I[LNK, Toothbrush, 2, 3.99, 1688142668302, 2023-06-30T16:31:08.302Z]
    main()