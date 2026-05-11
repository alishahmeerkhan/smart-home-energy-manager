import oracledb
import random
import time
from datetime import datetime, timedelta

try:
    oracledb.init_oracle_client()
    print('Thick mode enabled.')
except Exception as e:
    print(f'Failed to start Thick mode: {e}')
    print('You may need to pass the lib_dir argument with the path to your Oracle bin folder.')

DB_USER = 'smart_home_energy_manager'
DB_PASS = 'fast'
DB_DSN = '192.168.18.97/xe'

print('Starting Flux IoT Simulator...')

try:
    pool = oracledb.create_pool(user=DB_USER, password=DB_PASS, dsn=DB_DSN, min=2, max=5, increment=1)
    print('Connected to Database.')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit()

def get_all_devices():
    '''Fetches all devices, their wattage, and their CURRENT STATUS.'''
    with pool.acquire() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT d.DeviceID, d.DeviceName, dt.AverageWattage, d.Status 
                FROM Devices d
                JOIN Device_Types dt ON d.TypeID = dt.TypeID
            ''')
            return cursor.fetchall()

def backfill_history(days=30):
    '''Generates historical data so your dashboard charts look full instantly.'''
    devices = get_all_devices()
    if not devices:
        print('No devices found. Please add a device on the dashboard first.')
        return

    print(f'Backfilling {days} days of historical data...')
    
    with pool.acquire() as conn:
        with conn.cursor() as cursor:
            now = datetime.now()
            
            for device in devices:
                device_id, name, wattage = device
                kw = wattage / 1000

                for day in range(days):
                    for hour in range(24):
                        log_time = now - timedelta(days=day, hours=hour)
                        
                        is_active = random.choice([True, False, False])
                        
                        if is_active:
                            hours_active = random.uniform(0.1, 1.0)
                            kwh_used = kw * hours_active
                            
                            cursor.execute('''
                                INSERT INTO Energy_Logs (DeviceID, LogDate, kWh_Used) 
                                VALUES (:1, :2, :3)
                            ''', (device_id, log_time, round(kwh_used, 4)))
            
            conn.commit()
            print('Historical backfill complete! Check your dashboard.')

def run_live_simulation(interval_seconds=60):
    '''Infinite loop that adds new data every X seconds.'''
    print(f'Starting live telemetry feed (New data every {interval_seconds} seconds). Press Ctrl+C to stop.')
    
    while True:
        devices = get_all_devices()
        with pool.acquire() as conn:
            with conn.cursor() as cursor:
                now = datetime.now()
                
                for device in devices:
                    device_id, name, wattage, status = device 
                    kw = wattage / 1000
                    
                    if status == 'ON':
                        hours_passed = interval_seconds / 3600
                        kwh_used = kw * hours_passed * random.uniform(0.5, 1.0)
                        
                        cursor.execute('''
                            INSERT INTO Energy_Logs (DeviceID, LogDate, kWh_Used) 
                            VALUES (:1, :2, :3)
                        ''', (device_id, now, round(kwh_used, 6)))
                        
                        print(f'   [{now.strftime('%H:%M:%S')}] {name} used {round(kwh_used, 6)} kWh')
                
                conn.commit()
        
        time.sleep(interval_seconds)

if __name__ == '__main__':
    print('-' * 40)
    run_live_simulation(interval_seconds=10)