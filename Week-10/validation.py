"""
Validator Module
To ensure all data was moved correctly and completely
"""
import logging
from db import connect

logger = logging.getLogger(__name__)

class Validator:
    """Validator class, ensuring data integrity"""
    
    def __init__(self, source_db, target_db):
        """
        Initialize validator
        """
        self.source_db = source_db
        self.target_db = target_db
    
    def _table_hash(self, conn, table_name, where_clause=None):
        """Calculate hash for table"""
        cursor = conn.cursor()
        try:
            # Column names
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
            columns = [desc[0] for desc in cursor.description]
            columns_str = ', '.join(columns)
            
            query = f"""
            SELECT md5(string_agg(row::text, ''))
            FROM (
                SELECT row_to_json(row({columns_str})) as row
                FROM {table_name}
            """
            
            if where_clause:
                query += f" WHERE {where_clause}"
                
            query += " ORDER BY id) as subquery"
            
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else None
            
        finally:
            cursor.close()
    
    def _row_count(self, conn, table_name, where_clause=None):
        """Count rows in table"""
        cursor = conn.cursor()
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
                
            cursor.execute(query)
            return cursor.fetchone()[0]
        finally:
            cursor.close()
    
    def validate_table(self, table_name, where_clause=None):
        """Validate data integrity"""
        logger.info(f"Validating table {table_name}...")
        
        source_conn = None
        target_conn = None
        
        try:
            source_conn = connect(self.source_db)
            target_conn = connect(self.target_db)
            
            # Compare row numbers
            source_count = self._row_count(source_conn, table_name, where_clause)
            target_count = self._row_count(target_conn, table_name, where_clause)

            if source_count != target_count:
                logger.error(f"Row count mismatch for {table_name}: Source={source_count}, Target={target_count}")
                return False
                
            # Compare hashes for tables
            source_hash = self._table_hash(source_conn, table_name, where_clause)
            target_hash = self._table_hash(target_conn, table_name, where_clause)
            
            if source_hash != target_hash:
                logger.error(f"Hash mismatch for {table_name}")
                return False
                
            logger.info(f"Validation passed for {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False
            
        finally:
            if source_conn:
                source_conn.close()
            if target_conn:
                target_conn.close()