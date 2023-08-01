from pyflink.table import (
    DataTypes,
    StreamTableEnvironment,
    EnvironmentSettings,
    CsvTableSource
)
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table.expressions import col


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    settings = EnvironmentSettings.new_instance()\
                        .in_batch_mode()\
                        .build()
    tbl_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                      environment_settings=settings)
    
    ddl_source = """
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
    tbl_env.execute_sql(ddl_source)
    
    tbl = tbl_env.from_path('product_locale_sales')

    # take a quick peek at the data before seeing the output
    # from aggregate calculations
    print('\nBase data (first 8 rows)')
    print_cols = ['sales_date', 'product', 'seller_id', 'quantity', 'product_price']
    print(tbl.to_pandas()[print_cols]\
              .sort_values(print_cols[:3])\
              .head(8))

    # important to note that operations will be parallelized over
    # task slots across system cores so output will appear randomly
    # ordered and differ from run to run

    # Use Table API to find average price of products through
    # selecting and averaging the product_price field
    avg_price = tbl.select(tbl.product_price)\
                    .distinct()\
                    .select(tbl.product_price.avg.alias('avg_price'))

    print('\navg_price data')
    print(avg_price.to_pandas())


    # Use SQL to find average price of products through
    # selecting and averaging the product_price field
    avg_price2 = tbl_env.sql_query("""
        SELECT AVG(DISTINCT product_price) AS avg_price
        FROM product_locale_sales
    """)

    print('\navg_price2 data')
    print(avg_price2.to_pandas())


    # Use Table API to calculate total revenue per seller through
    # calculating product sales (quantity * product_price) then
    # grouping by seller and summing the sales
    seller_revenue = tbl.select(tbl.seller_id,
                              tbl.product,
                              (tbl.product_price * tbl.quantity).alias('sales'))\
                      .group_by(tbl.seller_id)\
                      .select(tbl.seller_id, col('sales').sum.alias('seller_revenue'))

    print('\nseller_revenue data')
    print(seller_revenue.to_pandas())


    # Use SQL to calculate total revenue per seller through
    # calculating product sales (quantity * product_price) then
    # grouping by seller and summing the sales
    seller_revenue2 = tbl_env.sql_query("""
        SELECT t.seller_id, SUM(t.sales) AS seller_revenue
        FROM (
            SELECT DISTINCT seller_id, product,
                product_price * quantity AS sales
            FROM product_locale_sales
        ) t
        GROUP BY t.seller_id
    """)

    print('\nseller_revenue2 data')
    print(seller_revenue2.to_pandas())


if __name__ == '__main__':
    main()
