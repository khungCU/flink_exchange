from pyflink.table import (
    TableEnvironment, EnvironmentSettings
)
import os

def main():
    env_settings = EnvironmentSettings.new_instance()\
                        .in_batch_mode()\
                        .build()
    tbl_env = TableEnvironment.create(env_settings)

    source_sql = """
        CREATE TABLE employee_information (
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
    tbl_env.execute_sql(source_sql)
    
    tbl = tbl_env.from_path('employee_information')
    print('\nProduct Sales Schema')
    tbl.print_schema()

    print('\nProduct Locale Sales Data')
    print(tbl.to_pandas())



if __name__ == '__main__':
    main()
