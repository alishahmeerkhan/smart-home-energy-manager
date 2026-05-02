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
            
            cursor.execute(query, name=name)
            user = cursor.fetchone()
            
            return user
            
def createNewUser(userData):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = f'INSERT INTO users(name, email, passwordHash, role) VALUES(:1, :2, :3, :4)'
            data_to_insert = (userData[0], userData[1], userData[2], 'Homeowner')
            cursor.execute(query, data_to_insert)
            connection.commit()