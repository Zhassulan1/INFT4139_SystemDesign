#!/usr/bin/env python3
"""
Data transfer
Handles command line arguments
"""
import argparse
import logging
from datetime import datetime
import os
import time
from multiprocessing import Pool, Manager

from db import connect
from worker import Worker
from validation import Validator
from saga import Saga


TABLES = ['users', 'products', 'recommendations']

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(processName)s - %(message)s',
    handlers=[
        logging.FileHandler('db_transfer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()


def count_rows(connection, table_name, where_clause=None):
    """Get total number of rows in a table"""
    cursor = connection.cursor()
    query = f"SELECT COUNT(*) FROM {table_name}"
    if where_clause:
        query += f" WHERE {where_clause}"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def get_last_sync_time():
    """Get last sync time from file"""
    try:
        if os.path.exists('last_sync.txt'):
            with open('last_sync.txt', 'r') as f:
                return datetime.fromisoformat(f.read().strip())
        return datetime.min
    except Exception as e:
        logger.error(f"Error reading last sync time: {e}")
        return datetime.min


def save_sync_time(sync_time):
    """Save the current time to file"""
    try:
        with open('last_sync.txt', 'w') as f:
            f.write(sync_time.isoformat())
    except Exception as e:
        logger.error(f"Error saving sync time: {e}")
        raise e


def clear_table(connection, table_name):
    """Clear table"""
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM {table_name}")
    connection.commit()
    cursor.close()
    logger.info(f"Cleared table {table_name}")


def worker_process(args):
    """Function that will be EXECUTED in worker process"""
    worker_id, table_name, start_id, end_id, source_db, target_db, mode, where_clause, retry_state = args
    worker = Worker(worker_id, table_name, source_db, target_db, mode)
    return worker.process(start_id, end_id, where_clause, retry_state)


def transfer_table(table_name, source_db, target_db, num_workers, mode, where_clause=None):
    """Transfer a single table using multiple workers"""
    source_conn = connect(source_db, isolation=True)
    target_conn = connect(target_db)
    
    # In copy mode clear target table
    if mode == 'copy':
        clear_table(target_conn, table_name)
    
    # Count rows
    total_rows = count_rows(source_conn, table_name, where_clause)
    logger.info(f"Processing {total_rows} rows from {table_name} with {num_workers} workers")
    
    if total_rows == 0:
        logger.info(f"No rows to process for {table_name}")
        source_conn.close()
        target_conn.close()
        return True
    
    # Calculate ranges for each worker
    rows_per_worker = max(1, total_rows // num_workers)
    
    # Create manager to share state between processes
    manager = Manager()
    retry_state = manager.dict()
    
    # Prepare arguments for each worker
    worker_args = []
    for i in range(num_workers):
        start_id = i * rows_per_worker
        end_id = total_rows if i == num_workers - 1 else (i + 1) * rows_per_worker
        worker_args.append((i, table_name, start_id, end_id, source_db, target_db, mode, where_clause, retry_state))
    
    # Initialize Saga coordinator
    saga = Saga(table_name, worker_args)
    
    # Start workers with process pool
    success = saga.execute(worker_process)
    
    source_conn.close()
    target_conn.close()
    
    # Validate transfer
    if success:
        validator = Validator(source_db, target_db)
        if not validator.validate_table(table_name, where_clause):
            logger.error(f"Data validation failed for {table_name}")
            return False
    return success


def transfer_all(source_db, target_db, num_workers):
    """Copy all tables"""
    try:
        # Save current time as last sync time
        current_time = datetime.now()
        
        for table_name in TABLES:
            logger.info(f"Starting full transfer of table {table_name}")
            if not transfer_table(table_name, source_db, target_db, num_workers, 'copy'):
                logger.error(f"Transfer failed for table {table_name}")
                return False
            logger.info(f"Completed full transfer of table {table_name}")
        
        save_sync_time(current_time)
        logger.info("Transferred all tables successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during transfer all: {e}")
        return False


def transfer_updates(source_db, target_db, num_workers):
    """Update tables"""
    try:
        # Get the last sync time
        last_sync_time = get_last_sync_time()
        logger.info(f"Syncing updates since {last_sync_time}")
        
        # Save current time as last sync time
        current_time = datetime.now()
        
        for table_name in TABLES:
            # Insert new rows
            logger.info(f"Starting insertion of new rows for table {table_name}")
            insert_where = f"created_at >= '{last_sync_time}'"
            if not transfer_table(table_name, source_db, target_db, num_workers, 'sync', insert_where):
                logger.error(f"Insert failed for table {table_name}")
                return False
            
            # Update modified rows
            logger.info(f"Starting update of modified rows for table {table_name}")
            update_where = f"updated_at >= '{last_sync_time}' AND created_at < '{last_sync_time}'"
            if not transfer_table(table_name, source_db, target_db, num_workers, 'update', update_where):
                logger.error(f"Update failed for table {table_name}")
                return False
                
            logger.info(f"Completed updates for table {table_name}")
        
        save_sync_time(current_time)
        logger.info("Synced all updates successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during sync: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['copy', 'sync'], required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--workers', type=int, default=4)
    
    args = parser.parse_args()
    
    if args.mode == 'copy':
        transfer_all(args.source, args.target, args.workers)
    else:
        transfer_updates(args.source, args.target, args.workers)