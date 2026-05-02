import oracledb

oracledb.init_oracle_client()

pool = oracledb.create_pool(
    user='smart_home_energy_manager',
    password='fast',
    dsn='192.168.18.97/xe',
    min=2,
    max=5,
    increment=1
)
    
def getUserData(userid):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = f'SELECT * FROM users WHERE userid = {userid}'
            for r in cursor.execute(query):
                return r
            
def createNewUser(userData):
    pass 