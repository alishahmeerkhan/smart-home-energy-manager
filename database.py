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
    
def getUserData(name):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = 'SELECT * FROM users WHERE name = :name'
            
            # 3. Pass the variable safely into the execute command
            cursor.execute(query, name=name)
            
            # 4. Use fetchone() instead of a for loop. It's much cleaner!
            user = cursor.fetchone()
            
            return user
            
def createNewUser(userData):
    pass 