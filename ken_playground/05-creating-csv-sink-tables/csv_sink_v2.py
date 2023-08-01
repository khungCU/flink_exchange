from pyflink.table import (
     TableEnvironment, EnvironmentSettings
)


def main():
    env_settings = EnvironmentSettings.new_instance()\
                        .in_batch_mode()\
                        .build()
    tbl_env = TableEnvironment.create(env_settings)

    # all data to one output file
    tbl_env.get_config().get_configuration().set_string("parallelism.default", "1")
    
    # Source Tale
    source_csv_table = """
        CREATE TABLE source_csv_tbl (
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
    
    tbl_env.execute_sql(source_csv_table)

    tbl = tbl_env.from_path('source_csv_tbl')

    print('\nProduct Sales Schema')
    tbl.print_schema()

    # Sink Table
    sink_csv_table = """
        CREATE TABLE sink_csv_tbl (
            seller_id STRING,
            product STRING,
            quantity INT,
            product_price DOUBLE,
            sales_date DATE
        ) WITH (
            'connector' = 'filesystem',
            'path' = './csv-output/',
            'format' = 'csv'
        );
    """
    tbl_env.execute_sql(sink_csv_table)
    
    
    # Insert the source into sink
    insert_csv_table = """
        INSERT INTO sink_csv_tbl 
        SELECT * from source_csv_tbl;
    """
    tbl_env.execute_sql(insert_csv_table)

    tbl_sink = tbl_env.from_path("sink_csv_tbl")
    tbl_sink.execute()

if __name__ == '__main__':
    main()
