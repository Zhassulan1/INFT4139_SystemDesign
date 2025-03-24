"""
Database Module
Handles connections to PostgreSQL databases
"""
import os
import logging
import psycopg2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def get_config():
    """Get db configuration from env"""
    load_dotenv()
    HOST = os.environ.get("HOST")
    PORT = os.environ.get("PORT")
    USER = os.environ.get("USER")
    PASSWORD = os.environ.get("PASSWORD")
    config = {
        'host': HOST,
        'port': PORT,
        'user': USER,
        'password': PASSWORD
    }
    return config

def connect(db_name, isolation=False):
    """Connect to db"""
    try:
        params = get_config()
        params['database'] = db_name
        
        conn = psycopg2.connect(**params)
        if isolation:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ)
        
        logger.info(f"Connected to {db_name} database")
        return conn
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error connecting to database: {error}")
        raise