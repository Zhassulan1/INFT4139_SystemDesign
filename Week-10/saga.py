"""
Saga Module
Implements Saga pattern to manage worker processes
"""
import logging
import time
from multiprocessing import Pool
import sys

logger = logging.getLogger(__name__)

class Saga:
    """Implements Saga pattern, allows restarting failed workers"""
    
    def __init__(self, table_name, worker_args):
        """Initialize saga coordinator"""
        self.table_name = table_name
        self.worker_args = worker_args
        self.num_workers = len(worker_args)
        self.failed_workers = []
    
    def ask_for_retry(self):
        """Ask if user wants to retry failed workers"""
        worker_ids = [self.worker_args[i][0] for i in self.failed_workers]
        
        while True:
            print(f"\nThe following workers failed: {worker_ids}")
            print(f"for table {self.table_name}")
            print("Do you want to retry these workers? (y/n): ", end='')
            
            try:
                answer = input().lower().strip()
                if answer in ('y', 'yes'):
                    return True
                elif answer in ('n', 'no'):
                    return False
                else:
                    print("Please enter 'y' or 'n'")
            except KeyboardInterrupt:
                print("\nOperation cancelled")
                return False

    def execute(self, worker_function):
        """Execute all workers and manage any failures"""
        max_attempts = 3
        attempt = 1
        
        while attempt <= max_attempts:
            logger.info(f"Saga attempt {attempt}/{max_attempts} for table {self.table_name}")
            
            # Run all workers in parallel
            with Pool(processes=self.num_workers) as pool:
                results = pool.map(worker_function, self.worker_args)
            
            # Check for failures
            self.failed_workers = [i for i, success in enumerate(results) if not success]
            
            if not self.failed_workers:
                logger.info(f"All workers completed successfully for table {self.table_name}")
                return True

            # Retry failed workers
            if attempt < max_attempts:
                should_retry = self.ask_for_retry()
                if not should_retry:
                    logger.info("User chose not to retry failed workers")
                    return False
                    
                # Update worker args to include only failed workers
                self.worker_args = [self.worker_args[i] for i in self.failed_workers]
                self.num_workers = len(self.worker_args)
                
            attempt += 1
            
        logger.error(f"Failed to complete all workers for table {self.table_name} after {max_attempts} attempts")
        return False