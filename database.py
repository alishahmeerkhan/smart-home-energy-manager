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

def energy_used(userId):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = '''SELECT NVL(SUM(el.kWh_Used), 0) 
                FROM Users u 
                JOIN Homes h ON u.UserID = h.UserID 
                JOIN Rooms r ON h.HomeID = r.HomeID 
                JOIN Devices d ON r.RoomID = d.RoomID 
                JOIN Energy_Logs el ON d.DeviceID = el.DeviceID 
                WHERE u.UserID = :1'''
            
            cursor.execute(query, (userId,))
            
            result = cursor.fetchone()
            
            return result[0]
        
def get_hourly_energy_usage(user_id):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = '''
                SELECT 
                    TO_CHAR(el.LogDate, 'HH24') || ':00' AS LogHour, -- The Safe Fix!
                    NVL(SUM(el.kWh_Used), 0) AS HourlyTotal
                FROM Users u
                JOIN Homes h ON u.UserID = h.UserID
                JOIN Rooms r ON h.HomeID = r.HomeID
                JOIN Devices d ON r.RoomID = d.RoomID
                JOIN Energy_Logs el ON d.DeviceID = el.DeviceID
                WHERE u.UserID = :1
                  AND el.LogDate >= SYSDATE - 1
                
                -- Group and Order using safe Oracle date formats
                GROUP BY 
                    TO_CHAR(el.LogDate, 'YYYY-MM-DD HH24'), 
                    TO_CHAR(el.LogDate, 'HH24') || ':00'
                ORDER BY 
                    TO_CHAR(el.LogDate, 'YYYY-MM-DD HH24') ASC
            '''
            
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
            
            labels = []
            data_points = []
            
            for row in results:
                labels.append(row[0])      # The Hour (e.g., "14:00")
                data_points.append(row[1]) # The Total kWh (e.g., 2.5)
                
            return {
                "labels": labels,
                "data": data_points
            }
        
def get_user_devices(user_id):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = """
                SELECT 
                    d.DeviceID AS device_id,
                    d.DeviceName AS device_name,
                    r.RoomName AS room_name,
                    d.Status AS status,
                    dt.AverageWattage AS max_wattage,
                    CASE 
                        WHEN d.Status = 'ON' THEN dt.AverageWattage 
                        ELSE 0 
                    END AS current_wattage
                FROM Users u
                JOIN Homes h ON u.UserID = h.UserID
                JOIN Rooms r ON h.HomeID = r.HomeID
                JOIN Devices d ON r.RoomID = d.RoomID
                JOIN Device_Types dt ON d.TypeID = dt.TypeID
                WHERE u.UserID = :1
                ORDER BY d.deviceid ASC
            """
            
            # Execute the query with our positional bind variable
            cursor.execute(query, (user_id,))
            
            # THE TRICK: Convert the results into a list of Dictionaries
            columns = [col[0].lower() for col in cursor.description]
            cursor.rowfactory = lambda *args: dict(zip(columns, args))
            
            # Fetch and return the list of dictionaries
            devices = cursor.fetchall()
            return devices