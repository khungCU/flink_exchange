from pyflink.table import (
    TableEnvironment,
    EnvironmentSettings,
    StreamTableEnvironment
)
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table.expressions import col, to_date
from pyflink.table.types import DataTypes

def main():
    
    env = StreamExecutionEnvironment.get_execution_environment()
    
    settings = EnvironmentSettings.new_instance()\
                        .in_batch_mode()\
                        .build()
                        
    tbl_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                      environment_settings=settings)

    
    source_ddl = """
        CREATE TABLE product_locale_sales (
            seller_id STRING,
            product STRING,
            quantity INT,
            product_price DOUBLE,
            sales_date DATE
        ) WITH ( 
                'connector' = 'filesystem',
                'path' = './csv-input',
                'csv.ignore-parse-errors' = 'true',
                'format' = 'csv'
            );   
    """
    
    tbl_env.execute_sql(source_ddl)

    tbl = tbl_env.from_path('product_locale_sales')

    # important to note that operations will be parallelized over
    # task slots across system cores so output will appear randomly
    # ordered and differ from run to run

    # Use Table API to calculate the product sales for each day
    # and filter down to just those with sales of $80 or better
    high_sales = tbl.select(tbl.sales_date,
                              tbl.seller_id,
                              tbl.product,
                              (tbl.product_price * tbl.quantity).alias('sales'))\
                        .distinct()\
                        .where(col('sales') >= 80)

    print('\nhigh_sales data')
    print(high_sales.to_pandas())


    # Use SQL to calculate the product sales for each day
    # and filter down to just those with sales of $80 or better
    high_sales2 = tbl_env.sql_query("""
        SELECT * FROM (
            SELECT DISTINCT sales_date, seller_id, product,
                product_price * quantity AS sales
            FROM product_locale_sales) t
        WHERE t.sales >= 80
    """)

    print('\nhigh_sales2 data')
    print(high_sales2.to_pandas())

    # Use table API to select all high sales products (at least $80)
    # for July 1, 2021
    july1_high_sales = tbl.select(tbl.sales_date,
                              tbl.seller_id,
                              tbl.product,
                              (tbl.product_price * tbl.quantity).alias('sales'))\
                        .distinct()\
                        .where((col('sales') >= 80) & (col("sales_date") == to_date('2021-07-01')))

    print('\njuly1_high_sales data')
    print(july1_high_sales.to_pandas())


    # Use SQL to select all high sales products (at least $80)
    # for July 1, 2021
    july1_high_sales2 = tbl_env.sql_query("""
        SELECT * FROM (
            SELECT DISTINCT sales_date, seller_id, product,
                product_price * quantity AS sales
            FROM product_locale_sales) t
        WHERE t.sales >= 80 AND t.sales_date = '2021-07-01'
    """)

    print('\njuly1_high_sales2 data')
    print(july1_high_sales2.to_pandas())


if __name__ == '__main__':
    main()
