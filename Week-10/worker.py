"""
Worker Module
Handles the actual data transfer operations
"""
import logging
import psycopg2
import time
from db import connect

DEFAULT_BATCH_SIZE = 5000
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

logger = logging.getLogger(__name__)

class Worker:
    """Worker class, to handle portion of data transfer"""
    
    def __init__(self, worker_id, table_name, source_db, target_db, mode):
        """Initialize worker"""
        self.worker_id = worker_id
        self.table_name = table_name
        self.source_db = source_db
        self.target_db = target_db
        self.mode = mode
        self.process_name = f"Worker-{worker_id}-{table_name}"
    
    def fetch_rows(self, cursor, columns, batch_size, offset, limit, where_clause=None):
        """Fetch a batch of rows"""
        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {self.table_name}"
        
        conditions = []
        if where_clause:
            conditions.append(where_clause)
        
        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"
        
        query += f" ORDER BY id LIMIT {limit} OFFSET {offset}"
        cursor.execute(query)
        return cursor.fetchall()
    
    def insert_rows(self, cursor, columns, rows):
        """Insert multiple rows with a single statement"""
        if not rows:
            return 0
            
        columns_str = ', '.join(columns)
        values_template = ','.join(['%s'] * len(columns))
        args_str = ','.join(
            cursor.mogrify(f"({values_template})", row).decode('utf-8') 
            for row in rows
        )
        
        cursor.execute(f"INSERT INTO {self.table_name} ({columns_str}) VALUES {args_str}")
        return len(rows)
    
    def update_rows(self, cursor, columns, rows):
        """Update rows one by one"""
        if not rows:
            return 0
            
        for row in rows:
            id_value = row[0]  # First column is id
            # Prepare SET clause for all columns except id
            set_clauses = [f"{columns[i]} = %s" for i in range(1, len(columns))]
            set_clause = ', '.join(set_clauses)
            
            update_query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = %s"
            cursor.execute(update_query, row[1:] + (id_value,))
        
        return len(rows)
    
    def process(self, start_id, end_id, where_clause=None, retry_state=None):
        """Process a range of rows"""
        logger.info(f"{self.process_name}: Starting processing range {start_id} to {end_id}")
        
        retries = 0
        while retries <= MAX_RETRIES:
            try:
                # Check if this range was already processed
                if retry_state and retry_state.get(f"{self.worker_id}_completed", False):
                    logger.info(f"{self.process_name}: Range was already processed")
                    return True
                
                source_conn = connect(self.source_db)
                target_conn = connect(self.target_db)
                
                source_cursor = source_conn.cursor()
                target_cursor = target_conn.cursor()
                
                # Column names
                source_cursor.execute(f"SELECT * FROM {self.table_name} LIMIT 0")
                columns = [desc[0] for desc in source_cursor.description]

                # Process data in batches
                batch_size = DEFAULT_BATCH_SIZE
                processed = 0
                offset = start_id
                
                while offset < end_id:
                    # Batch limit
                    limit = min(batch_size, end_id - offset)
                    
                    # Fetch batch of rows
                    rows = self.fetch_rows(source_cursor, columns, batch_size, offset, limit, where_clause)
                    if not rows:
                        break
                    
                    # Process rows based on mode
                    if self.mode in ('copy', 'sync'):
                        rows_affected = self.insert_rows(target_cursor, columns, rows)
                    elif self.mode == 'update':
                        rows_affected = self.update_rows(target_cursor, columns, rows)

                    processed += rows_affected
                    offset += batch_size

                    target_conn.commit()
                    
                    logger.info(f"{self.process_name}: Processed {processed}/{end_id - start_id} rows")
                
                # Mark this range as completed in shared state
                if retry_state is not None:
                    retry_state[f"{self.worker_id}_completed"] = True
                
                source_conn.close()
                target_conn.close()
                
                logger.info(f"{self.process_name}: Finished, {processed} rows")
                return True
                
            except Exception as e:
                retries += 1
                logger.error(f"{self.process_name}: Error during processing (attempt {retries}/{MAX_RETRIES}): {e}")
                
                if retries <= MAX_RETRIES:
                    logger.info(f"{self.process_name}: Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"{self.process_name}: Max retries exceeded")
                    return False
                    
        return False