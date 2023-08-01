import os

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings


def main():
    
    # Create streaming environment
    env = StreamExecutionEnvironment.get_execution_environment()

    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()

    # create table environment
    tbl_env = StreamTableEnvironment.create(
        stream_execution_environment=env, environment_settings=settings
    )

    # add kafka connector dependency
    kafka_jar = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "flink-sql-connector-kafka-1.17.1.jar",
    )

    tbl_env.get_config().get_configuration().set_string(
        "pipeline.jars", "file://{}".format(kafka_jar)
    )
    tbl_env.get_config().set_local_timezone("Europe/Paris")
    

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
            evttime AS TO_TIMESTAMP_LTZ(sale_ts, 0),
            WATERMARK FOR evttime AS evttime - INTERVAL '5' SECOND 
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'salesitems',
            'properties.group.id' = 'salesitems_tumble',
            'scan.startup.mode' = 'latest-offset',
            'properties.bootstrap.servers' = 'localhost:9092',
            'format' = 'json'
        )
    """

    tbl_env.execute_sql(src_ddl)

    # create and initiate loading of source Table
    tbl = tbl_env.from_path("salesitems")

    print("\nSource Schema")
    tbl.print_schema()

    # Troubleshoot
    sink_ddl_salesitems = """
        CREATE TABLE salesitems_out (
            seller_id VARCHAR,
            product VARCHAR,
            quantity INT,
            product_price DOUBLE,
            sale_ts BIGINT,
            evttime TIMESTAMP_LTZ(3)
        ) WITH (
            'connector' = 'print'
        )
    """
    tbl_env.execute_sql(sink_ddl_salesitems)

    select_query = """
        select * from salesitems
    """
    select_query_exec = tbl_env.sql_query(select_query)
    
    select_query_exec.execute_insert('salesitems_out').wait()

    #####################################################################
    # Define Tumbling Window Aggregate Calculation of Revenue per Seller
    #
    # - for every 30 second non-overlapping window
    # - calculate the revenue per seller
    #####################################################################
    # windowed_rev = tbl.window(Tumble.over(lit(30).seconds)
    #                           .on(tbl.evttime)
    #                           .alias('w'))\
    #                   .group_by(col('w'), tbl.seller_id)\
    #                   .select(tbl.seller_id,
    #                           col('w').start.alias('window_start'),
    #                           col('w').end.alias('window_end'),
    #                           (tbl.quantity * tbl.product_price).sum.alias('window_sales'))
    
    # window_rev_sql = """
    #     SELECT 
    #         seller_id,
    #         window_start,
    #         window_end,
    #         window_time,
    #         SUM(quantity * product_price) AS window_sales
    #     FROM TABLE(
    #         TUMBLE(
    #             DATA => TABLE salesitems,
    #             TIMECOL => DESCRIPTOR(evttime),
    #             SIZE => INTERVAL '30' SECONDS))
    #     GROUP BY seller_id, window_start, window_end, window_time;
    # """
    # window_rev = tbl_env.sql_query(window_rev_sql)

    # ###############################################################
    # # Create Kafka Sink Table
    # ###############################################################
    # sink_ddl = """
    #     CREATE TABLE processedsales (
    #         seller_id VARCHAR,
    #         window_start  TIMESTAMP(3),
    #         window_end  TIMESTAMP(3),
    #         window_sales DOUBLE
    #     ) WITH (
    #         'connector' = 'kafka',
    #         'topic' = 'processedsales',
    #         'properties.bootstrap.servers' = 'localhost:9092',
    #         'scan.startup.mode' = 'latest-offset',
    #         'format' = 'json'
    #     )
    # """
    # sink_ddl = """
    #     CREATE TABLE processedsales (
    #         seller_id VARCHAR,
    #         window_start  TIMESTAMP(3),
    #         window_end  TIMESTAMP(3),
    #         window_time TIMESTAMP(3),
    #         window_sales DOUBLE
    #     ) WITH (
    #         'connector' = 'print'
    #     )
    # """
    # tbl_env.execute_sql(sink_ddl)
    # sink_tbl = tbl_env.from_path("processedsales")
    # print("\nSource Schema")
    # sink_tbl.print_schema()
    # # write time windowed aggregations to sink table
    # window_rev.execute_insert("processedsales").wait()
    

    tbl_env.execute("tbl-api-tumbling-windows-demo")


if __name__ == "__main__":
    main()
