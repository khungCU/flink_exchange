from statistics import stdev, mean

from pyflink.table import (
    DataTypes,
    TableEnvironment,
    EnvironmentSettings
)
from pyflink.table.udf import udf


@udf(input_type = [DataTypes.INT(), DataTypes.INT(), DataTypes.INT(), DataTypes.INT()],
    result_type = DataTypes.FIELD('sales_total', DataTypes.INT()))
def sales_total(q1, q2 ,q3, q4):
    sales = (q1, q2, q3, q4)
    total_sales = sum(sales)
    return total_sales
    
@udf(input_type = [DataTypes.INT(), DataTypes.INT(), DataTypes.INT(), DataTypes.INT()],
    result_type = DataTypes.FIELD('qtr_avg', DataTypes.DOUBLE()))
def qtr_avg(q1, q2, q3, q4):
    sales = (q1, q2, q3, q4)
    qtr_avg = round(mean(sales), 2)
    return qtr_avg

@udf(input_type = [DataTypes.INT(), DataTypes.INT(), DataTypes.INT(), DataTypes.INT()],
    result_type = DataTypes.FIELD('qtr_stdev', DataTypes.DOUBLE()))
def qtr_stdev(q1, q2, q3, q4):
    sales = (q1, q2, q3, q4)
    qtr_stdev = round(stdev(sales), 2)
    return qtr_stdev


def main():
    env_settings = EnvironmentSettings.new_instance()\
                        .in_batch_mode()\
                        .build()
    tbl_env = TableEnvironment.create(env_settings)
    
    ddl_sql = """
        CREATE TABLE quarterly_sales (
            seller_id VARCHAR,
            q1 INT,
            q2 INT,
            q3 INT,
            q4 INT
        ) WITH (
            'connector' = 'filesystem',
            'path' = './csv-input',
            'csv.ignore-parse-errors' = 'true',
            'format' = 'csv'
        );
    """
    tbl_env.execute_sql(ddl_sql)

    tbl = tbl_env.from_path('quarterly_sales')

    print('\nQuarterly Sales Schema')
    tbl.print_schema()

    print('\nQuarterly Sales Data')
    print(tbl.to_pandas().sort_values('seller_id'))
    

    sales_stats_ddl = """
        CREATE table sales_states (
            seller_id VARCHAR,
            total_sales INT,
            quarter_avg DOUBLE,
            quarter_stdev DOUBLE,
        ) WITH (
            type = "print"
        )
    """
    
    tbl_env.execute_sql(sales_stats_ddl)
    
    sales_stats_select = """
        SELECT
            seller_id,
            sales_total(q1,q2,q3,q4) AS sales_totals,
            qtr_avg(q1,q3,q3,q4) AS qtr_avg,
            qtr_stdev(q1,q2,q3,q4) AS qtr_stdev
        FROM quarterly_sales
    """
    
    tbl_sales_stats = tbl_env.execute_sql(sales_stats_select)
    
    tbl_sales_stats.execute_insert("sales_states")
    
    tbl_env.execute('tbl-python-udf-demo')


if __name__ == '__main__':
    main()
