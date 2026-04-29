import oracledb

oracledb.init_oracle_client()

with oracledb.connect(user='smart_home_energy_manager', 
                      password='fast',
                      dsn='192.168.18.97/XE') as connection:
    with connection.cursor() as cursor:
        query = 'SELECT * FROM users WHERE userid = 1'
        for r in cursor.execute(query):
            print(r)