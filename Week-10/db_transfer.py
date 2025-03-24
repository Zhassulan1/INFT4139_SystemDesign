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
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('db_transfer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger()


def get_db_config():
    """Get db configuration from env"""
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
        
        logger.info(f"Connected to {db_name} db")
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error connecting to db: {error}")
        raise


def count_rows(cursor, table_name, where_clause=None):
    """Count rows"""
    query = f"SELECT COUNT(*) FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    cursor.execute(query)
    return cursor.fetchone()[0]


def clear_table(cursor, table_name):
    """Clearing table"""
    cursor.execute(f"DELETE FROM {table_name}")


def columns_name(cursor, table_name):
    """Get column names"""
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
    columns = [desc[0] for desc in cursor.description]
    return columns


def fetch_rows(cursor, table_name, columns, batch_size, offset, where_clause=None):
    """Fetch batch of rows"""
    columns_str = ', '.join(columns)
    query = f"SELECT {columns_str} FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    
    query += f" ORDER BY id LIMIT {batch_size} OFFSET {offset}"
    cursor.execute(query)
    return cursor.fetchall()


def insert_rows(cursor, table_name, columns, rows):
    """Insert multiple rows with single statement"""
    if not rows:
        return 0
        
    columns_str = ', '.join(columns)
    values_template = ','.join(['%s'] * len(columns))
    args_str = ','.join(
        cursor.mogrify(f"({values_template})", row).decode('utf-8') 
        for row in rows
    )
    
    cursor.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES {args_str}")
    return len(rows)


def update_rows(cursor, table_name, column_names, rows):
    """Update rows one by one"""
    if not rows:
        return 0
        
    for row in rows:
        id_value = row[0]  # First column is id
        # Prepare SET clause for all columns except id
        columns_list = [f"{column_names[i]} = %s" for i in range(1, len(column_names))]
        columns = ', '.join(columns_list)
        update_query = f"UPDATE {table_name} SET {columns} WHERE id = %s"
        cursor.execute(update_query, row[1:] + (id_value,))
    return len(rows)


def process_rows(source_conn, target_conn, table_name, processor_func, where_clause=None):
    """Function to process rows"""
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    total_rows = count_rows(source_cursor, table_name, where_clause)


    columns = columns_name(source_cursor, table_name)
    processed_rows = 0
    offset = 0
    batch_size = DEFAULT_BATCH_SIZE
    while True:
        rows = fetch_rows(source_cursor, table_name, columns, batch_size, offset, where_clause)
        if not rows:
            break

        rows_affected = processor_func(target_cursor, table_name, columns, rows)
        processed_rows += rows_affected
        offset += batch_size
        target_conn.commit()
        logger.info(f"Processed batch: {offset} of {total_rows} rows in {table_name}")

    return processed_rows


def copy_db_table(source_conn, target_conn, table_name):
    """Copy all data from table in source DB to target DB"""
    try:
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        clear_table(target_cursor, table_name)
        rows_copied = process_rows(
            source_conn, 
            target_conn, 
            table_name,
            insert_rows,
        )
        logger.info(f"Transferred {rows_copied} rows to {table_name}")
        return rows_copied
        
    except (Exception, psycopg2.DatabaseError) as error:
        target_conn.rollback()
        logger.error(f"Error copying data for table {table_name}: {error}")
        raise


def sync_db_table(source_conn, target_conn, table_name, last_sync_time):
    """Sync updates between tables"""
    try:
        # 1 - insert new rows
        insert_where = f"created_at >= '{last_sync_time}'"
        rows_inserted = process_rows(
            source_conn,
            target_conn,
            table_name,
            insert_rows,
            insert_where,
        )
        
        # 2 - update updated rows
        update_where = f"updated_at >= '{last_sync_time}' AND created_at < '{last_sync_time}'"
        rows_updated = process_rows(
            source_conn,
            target_conn,
            table_name,
            update_rows,
            update_where,
        )
        
        total_synced = rows_inserted + rows_updated
        logger.info(f"Synced {total_synced} total rows in {table_name} ({rows_inserted} new, {rows_updated} updated)")
        return total_synced
        
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
        raise e


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