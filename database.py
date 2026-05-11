import oracledb
from datetime import datetime

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
                labels.append(row[0])
                data_points.append(row[1])
                
            return {
                'labels': labels,
                'data': data_points
            }
        
def get_user_devices(user_id):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = '''
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
            '''

            cursor.execute(query, (user_id,))
            columns = [col[0].lower() for col in cursor.description]
            cursor.rowfactory = lambda *args: dict(zip(columns, args))
            
            devices = cursor.fetchall()
            return devices
        
def set_new_budget(userid, new_budget):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = f'UPDATE budgets SET budgetlimit = :1 WHERE userid = :2'
            cursor.execute(query, (new_budget, userid))
            connection.commit()

def add_new_device(user_id, device_name, room_name, max_wattage, type_name='Home Appliance'):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            home_query = '''SELECT HomeID FROM Homes WHERE UserID = :1'''
            cursor.execute(home_query, (user_id,))
            home_row = cursor.fetchone()
            if not home_row:
                raise Exception('No home found for this user.')
            home_id = home_row[0]

            room_query = '''SELECT RoomID FROM Rooms WHERE RoomName = :1 AND HomeID = :2'''
            cursor.execute(room_query, (room_name, home_id))
            room_row = cursor.fetchone()
            if room_row:
                room_id = room_row[0]
            else:
                out_room_id = cursor.var(int)
                insert_query_room = '''INSERT INTO Rooms (HomeID, RoomName) VALUES (:1, :2) RETURNING RoomID INTO :3'''
                cursor.execute(insert_query_room, 
                               [home_id, room_name, out_room_id])
                room_id = out_room_id.getvalue()[0]

            type_query = '''SELECT TypeID FROM device_types WHERE typename = :1 AND averagewattage = :2'''
            cursor.execute(type_query, (type_name, max_wattage))
            type_row = cursor.fetchone()
            
            if type_row:
                type_id = type_row[0]
            else:
                out_type_id = cursor.var(int)
                insert_query_type = '''INSERT INTO device_types (typename, averagewattage) 
                                       VALUES (:1, :2) RETURNING typeid INTO :3'''
                cursor.execute(insert_query_type, [type_name, max_wattage, out_type_id])
                type_id = out_type_id.getvalue()[0]

            insert_query_device = '''INSERT INTO devices (roomid, typeid, devicename, status) 
                                     VALUES (:1, :2, :3, 'OFF')'''
            cursor.execute(insert_query_device, (room_id, type_id, device_name))

            connection.commit()

def remove_old_device(user_id):
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            query = '''DELETE FROM devices WHERE deviceid = :1'''
            cursor.execute(query, (user_id,))
            connection.commit()

def check_and_enforce_budget(user_id):
    '''
    Checks if the user exceeded their monthly financial budget. 
    If yes, turns ALL devices OFF automatically.
    '''
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            now = datetime.now()
            
            cursor.execute('''
                SELECT BudgetLimit FROM Budgets 
                WHERE UserID = :1 AND BudgetMonth = :2 AND BudgetYear = :3
            ''', (user_id, now.month, now.year))
            budget_row = cursor.fetchone()
            
            if not budget_row:
                return False
            
            budget_limit = budget_row[0]

            cursor.execute('''
                SELECT NVL(SUM(el.kWh_Used), 0) * NVL((SELECT PricePerKWh FROM Tariffs WHERE ROWNUM = 1), 1) AS TotalCost
                FROM Energy_Logs el
                JOIN Devices d ON el.DeviceID = d.DeviceID
                JOIN Rooms r ON d.RoomID = r.RoomID
                JOIN Homes h ON r.HomeID = h.HomeID
                WHERE h.UserID = :1 AND EXTRACT(MONTH FROM el.LogDate) = :2
            ''', (user_id, now.month))
            current_cost = cursor.fetchone()[0]

            if current_cost >= budget_limit:
                print(f'USER {user_id} EXCEEDED BUDGET OF ${budget_limit}! Auto-shutting down devices...')
                
                cursor.execute('''
                    UPDATE Devices d
                    SET Status = 'OFF'
                    WHERE d.RoomID IN (
                        SELECT r.RoomID FROM Rooms r 
                        JOIN Homes h ON r.HomeID = h.HomeID 
                        WHERE h.UserID = :1
                    )
                ''', (user_id,))
                connection.commit()
                return True
                
            return False 