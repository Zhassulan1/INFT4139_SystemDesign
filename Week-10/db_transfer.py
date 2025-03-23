"""
    Data transfer 
"""
import datetime
import logging
import os
import psycopg2
from dotenv import load_dotenv

DEFAULT_BATCH_SIZE = 5000

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(process)d - %(message)s',
    handlers=[
        logging.FileHandler('db_transfer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()


def get_db_config():
    """Get db configuration from environment variables"""
    load_dotenv()
    HOST = os.environ.get("HOST")
    PORT = os.environ.get("PORT")
    USER = os.environ.get("USER")
    PASSWORD = os.environ.get("PASSWORD")
    db_config = {
        'host': HOST,
        'port': PORT,
        'user': USER,
        'password': PASSWORD
    }
    return db_config


def connect_to_db(db_name, isolation=False):
    """Connect to the PostgreSQL database"""
    try:
        params = get_db_config()
        params['database'] = db_name
        
        conn = psycopg2.connect(**params)
        if isolation:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ)
        
        logger.info(f"Connected to db {db_name}...")
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error connecting to db: {error}")
        raise


def copy_db_table(source_conn, target_conn, table_name):
    """Copy all data from table in source DB to target db"""
    try:
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Get column names
        source_cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        columns = [desc[0] for desc in source_cursor.description]
        columns_str = ', '.join(columns)
        
        # Count rows
        source_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = source_cursor.fetchone()[0]
        logger.info(f"Copying {count} rows from table {table_name}")
        
        # Fetch data by batches to avoid memory issues
        batch_size = DEFAULT_BATCH_SIZE
        offset = 0

        # Delete all rows in target table for fresh copy
        target_cursor.execute(f"DELETE FROM {table_name}")

        while True:
            source_cursor.execute(f"SELECT {columns_str} FROM {table_name} ORDER BY id LIMIT {batch_size} OFFSET {offset}")
            rows = source_cursor.fetchall()

            if not rows:
                break

            values_template = ','.join(['%s'] * len(columns))
            args_str = ','.join(target_cursor.mogrify(f"({values_template})", row).decode('utf-8') for row in rows)
            
            target_cursor.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES {args_str}")
            
            offset += batch_size
            logger.info(f"Processed {offset} of {count} rows in {table_name}")
        
        target_conn.commit()
        logger.info(f"Transferred {count} rows to {table_name}")

    except (Exception, psycopg2.DatabaseError) as error:
        target_conn.rollback()
        logger.error(f"Error copying data for table {table_name}: {error}")
        raise


def sync_db_table(source_conn, target_conn, table_name, last_sync_time):
    """Sync updates between tables"""
    try:
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Get column names
        source_cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        columns = [desc[0] for desc in source_cursor.description]
        columns_str = ', '.join(columns)
        
        # Get new or updated rows
        query = f"""
        SELECT {columns_str} FROM {table_name}
        WHERE created_at >= %s OR updated_at >= %s
        """
        source_cursor.execute(query, (last_sync_time, last_sync_time))
        rows = source_cursor.fetchall()
        
        if not rows:
            logger.info(f"No new or updated rows found in {table_name}")
            return 0
        
        logger.info(f"Found {len(rows)} new or updated rows in {table_name}")
        
        # Insert or update rows in target DB
        for row in rows:
            # Check if row exists in target DB
            target_cursor.execute(f"SELECT id FROM {table_name} WHERE id = %s", (row[0],))
            exists = target_cursor.fetchone()
            
            if exists:
                # Update existing row
                set_clauses = [f"{columns[i]} = %s" for i in range(1, len(columns))]
                set_clause = ', '.join(set_clauses)
                update_query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
                target_cursor.execute(update_query, row[1:] + (row[0],))
            else:
                # Insert new row
                placeholders = ', '.join(['%s'] * len(columns))
                insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                target_cursor.execute(insert_query, row)
        
        target_conn.commit()
        logger.info(f"Transferred {len(rows)} rows to {table_name}")
        return len(rows)
        
    except (Exception, psycopg2.DatabaseError) as error:
        target_conn.rollback()
        logger.error(f"Error syncing data for table {table_name}: {error}")
        raise


def get_last_sync_time():
    """Get the last sync time from file"""
    try:
        if os.path.exists('last_sync.txt'):
            with open('last_sync.txt', 'r') as f:
                return datetime.datetime.fromisoformat(f.read().strip())
        return datetime.datetime.min
    except Exception as e:
        logger.error(f"Error reading last sync time: {e}")
        return datetime.datetime.min


def save_sync_time(sync_time):
    """Save the current time to file"""
    try:
        with open('last_sync.txt', 'w') as f:
            f.write(sync_time.isoformat())
    except Exception as e:
        logger.error(f"Error saving sync time: {e}")


def transfer_all(source_db, target_db):
    """Copy tables"""
    source_conn = None
    target_conn = None
    
    try:
        source_conn = connect_to_db(source_db, isolation=True)
        
        # Save current time as last sync time
        save_sync_time(datetime.datetime.now())

        target_conn = connect_to_db(target_db)
        
        copy_db_table(source_conn, target_conn, 'users')
        copy_db_table(source_conn, target_conn, 'products')
        copy_db_table(source_conn, target_conn, 'recommendations')
        
        logger.info("Copied all rows!!!")
        
    except Exception as e:
        logger.error(f"Error during transfer all: {e}")
        raise
    finally:
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()


def transfer_updates(source_db, target_db):
    """Update tables"""
    source_conn = None
    target_conn = None
    
    try:
        # Get the last sync time
        last_sync_time = get_last_sync_time()
        logger.info(f"Sync from {last_sync_time}")
        
        # Save current time as last sync time
        source_conn = connect_to_db(source_db, isolation=True)
        save_sync_time(datetime.datetime.now())
        
        target_conn = connect_to_db(target_db)
        
        # Sync updates for all tables
        sync_db_table(source_conn, target_conn, 'users', last_sync_time)
        sync_db_table(source_conn, target_conn, 'products', last_sync_time)
        sync_db_table(source_conn, target_conn, 'recommendations', last_sync_time)
        logger.info(f"Synced all updates")
        
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        raise
    finally:
        if source_conn:
            source_conn.close()
        if target_conn:
            target_conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['copy', 'sync'], required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    
    args = parser.parse_args()
    
    if args.mode == 'copy':
        transfer_all(args.source, args.target)
    else:
        transfer_updates(args.source, args.target)