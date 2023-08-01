from pyflink.table import (
    DataTypes,
    TableEnvironment,
    EnvironmentSettings,
    StreamTableEnvironment
)
from pyflink.datastream import StreamExecutionEnvironment


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    settings = EnvironmentSettings.new_instance()\
                        .in_batch_mode()\
                        .build()
    tbl_env = StreamTableEnvironment.create(stream_execution_environment=env,
                                      environment_settings=settings)

    # Define and register Sales Source Table
    source_fact_ddl = """
      CREATE TABLE product_locale_sales (
            seller_id STRING,
            product STRING,
            quantity INT,
            product_price DOUBLE,
            sales_date DATE
        ) WITH ( 
                'connector' = 'filesystem',
                'path' = './locale-sales',
                'csv.ignore-parse-errors' = 'true',
                'format' = 'csv'
            );  
    """
    tbl_env.execute_sql(source_fact_ddl)

    # Define and register Seller locations Source Table
    source_dim_ddl = """
      CREATE TABLE seller_locales (
        id STRING,
        city STRING,
        state STRING
      ) WITH (
        'connector' = 'filesystem',
        'path' = './locales',
        'csv.ignore-parse-errors' = 'true',
        'format' = 'csv'
      );
    """
    tbl_env.execute_sql(source_dim_ddl) 
    
    sales_tbl = tbl_env.from_path('product_locale_sales')
    sellers_tbl = tbl_env.from_path('seller_locales')

    # important to note that operations will be parallelized over
    # task slots across system cores so output will appear randomly
    # ordered and differ from run to run

    # Use Table API to perform inner join between sellers and product sales
    # to yield result of all sellers who have sales
    seller_products = sales_tbl.join(sellers_tbl, sales_tbl.seller_id == sellers_tbl.id)\
                            .select(sellers_tbl.city, sellers_tbl.state,
                                  sales_tbl.product, sales_tbl.product_price)\
                            .distinct()

    print('\nseller_products data')
    print(seller_products.to_pandas())


    # Use SQL to perform inner join between sellers and product sales
    # to yield result of all sellers who have sales
    seller_products2 = tbl_env.sql_query("""
        SELECT DISTINCT city, state, product, product_price
        FROM
          product_locale_sales s 
            JOIN
          seller_locales l ON s.seller_id = l.id
    """)

    print('\nseller_products2 data')
    print(seller_products2.to_pandas())


    # Use Table API with RIGHT OUTER JOIN to find seller locations
    # which have no sales (ie, NULLs for values in sales side of join)
    sellers_no_sales = sales_tbl.right_outer_join(sellers_tbl,
                                                sales_tbl.seller_id == sellers_tbl.id)\
                            .where(sales_tbl.product.is_null)\
                            .select(sellers_tbl.city, sellers_tbl.state, sales_tbl.product)\
                            .distinct()

    print('\nsellers_no_sales data')
    print(sellers_no_sales.to_pandas())


    # Use SQL with RIGHT OUTER JOIN to find seller locations
    # which have no sales (ie, NULLs for values in sales side of join)
    sellers_no_sales2 = tbl_env.sql_query("""
        SELECT DISTINCT city, state, product
        FROM
          product_locale_sales s 
            RIGHT OUTER JOIN
          seller_locales l ON s.seller_id = l.id
        WHERE s.product IS NULL
    """)

    print('\nsellers_no_sales2 data')
    print(sellers_no_sales2.to_pandas())


if __name__ == '__main__':
    main()
