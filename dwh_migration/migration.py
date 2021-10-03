import os
import sys
import mysql.connector
import psycopg2
from pprint import pprint
from config import config

params = config()

try:
    cnx_msql = mysql.connector.connect(host='localhost', user='', password='',
                            database='sensor_db', buffered=True)
    print("connected to mysql")
except mysql.connector.Error as e:
    print("MYSQL: Unable to connect!", e.msg)
    sys.exit(1)

# Postgresql connection
try:
    cnx_psql = psycopg2.connect(**params)
    print("connected to postgresql")
except psycopg2.Error as e:
    print('PSQL: Unable to connect!\n{0}').format(e)
    sys.exit(1)

# Cursors initializations
cur_msql = cnx_msql.cursor()
cur_psql = cnx_psql.cursor()

def select_and_insert(select_query, insert_query):
    cur_msql.execute(select_query)
    try:
        for row in cur_msql:
            cur_psql.execute(insert_query, row)
            print('row inserted')
    except psycopg2.Error as e:
        print('failed to execute query', e.pgerror)
        sys.exit("Problem Occured")

maindata_select_query = "SELECT * FROM maindata"
metadata_select_query = "SELECT * FROM metadata"
maindata_insert_query = '''INSERT INTO maindata (utc_time_id,
source_id,
primary_link_source_flag,avg_speed,avg_flow,avg_occ,avg_freeflow_speed,
avg_travel_time,high_quality_samples,samples_below_100pct_ff,samples_below_95pct_ff,
samples_below_90pct_ff,samples_below_85pct_ff,samples_below_80pct_ff,samples_below_75pct_ff,
samples_below_70pct_ff,samples_below_65pct_ff,samples_below_60pct_ff,samples_below_55pct_ff,
samples_below_50pct_ff,samples_below_45pct_ff,samples_below_40pct_ff,samples_below_35pct_ff,
samples_below_30pct_ff,samples_below_25pct_ff,samples_below_20pct_ff)
VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
       %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''
metadata_insert_query = '''
INSERT INTO metadata (
ID,Fwy,Dir,District,County,City,State_PM,Abs_PM,Latitude,Longitude,Length,Type,Lanes,Name,USER_ID_1,
USER_ID_2,USER_ID_3,USER_ID_4)
VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, 
       %s, %s, %s, %s, %s, %s, %s, %s, %s);
'''

if __name__ =="__main__":
    select_and_insert(maindata_select_query,maindata_insert_query)
    select_and_insert(metadata_select_query,metadata_insert_query)
    ## Closing cursors
    cur_msql.close()
    print('MySQL cursor closed.')
    cur_psql.close()
    print('Posgres cursor closed.')

    ## Committing 
    cnx_psql.commit()
    print('Committed!')

    ## Closing database connections
    cnx_msql.close()
    print('Mysql Database connection closed.')
    cnx_psql.close()
    print('Postgres Database connection closed.')
