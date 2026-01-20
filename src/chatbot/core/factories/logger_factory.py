import logging
import datetime
from pathlib import Path
from typing import Optional, Tuple

class LoggerFactory:
    """
    Centralized factory for creating and configuring loggers.
    Promotes consistent formatting and handler management across the application.
    """
    
    _DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    _DEFAULT_LEVEL = logging.INFO
    
    @staticmethod
    def get_logger(name: str, level: int = _DEFAULT_LEVEL) -> logging.Logger:
        """
        Get a named logger with standard configuration.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Ensure we have at least a console handler if none exists
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(LoggerFactory._DEFAULT_FORMAT))
            logger.addHandler(console_handler)
            
        return logger

    @staticmethod
    def setup_task_logger(task_id: str, file_path: str, base_name: str = "document_processor") -> Tuple[logging.Logger, Optional[logging.FileHandler]]:
        """
        Sets up a logger specially for a task, with a file handler pointing to a timestamped log file.
        
        Args:
            task_id: Unique ID for the task (used for disambiguation if needed)
            file_path: The file being processed (used for filename generation)
            base_name: The base logger name to use
            
        Returns:
            Tuple of (logger, file_handler)
            Caller is responsible for closing/removing the handler if desired to prevent leaks.
        """
        # Ensure logs directory exists
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_filename = Path(file_path).stem.replace(" ", "_")
        log_file = log_dir / f"processing_{timestamp}_{clean_filename}.log"
        
        logger = logging.getLogger(base_name)
        logger.setLevel(LoggerFactory._DEFAULT_LEVEL)
        
        # Create file handler
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(LoggerFactory._DEFAULT_LEVEL)
            file_handler.setFormatter(logging.Formatter(LoggerFactory._DEFAULT_FORMAT))
            
            # Avoid duplicate handlers: Check if ANY handler writes to the exact same file
            # This is a robust check for re-entrant workers
            existing_handler = False
            for h in logger.handlers:
                if isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file.absolute()):
                    existing_handler = True
                    break
            
            if not existing_handler:
                logger.addHandler(file_handler)
            else:
                # If it exists, we might return None as handler, or find the expected one?
                # Ideally we shouldn't hit this often with unique timestamps.
                file_handler.close() # Close usage of this new instance
                file_handler = None
                
            return logger, file_handler
            
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
            return logger, None
    @staticmethod
    def setup_global_file_logger(base_filename: str = "app_session") -> Optional[logging.FileHandler]:
        """
        Sets up a global file logger for the application session.
        Attaches a file handler to the root logger so all modules log to it.
        """
        # Ensure logs directory exists
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{base_filename}_{timestamp}.log"
        
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(LoggerFactory._DEFAULT_LEVEL)
            file_handler.setFormatter(logging.Formatter(LoggerFactory._DEFAULT_FORMAT))
            
            # Attach to root logger to capture all child loggers
            root_logger = logging.getLogger()
            root_logger.setLevel(LoggerFactory._DEFAULT_LEVEL)
            root_logger.addHandler(file_handler)
            
            print(f"📄 Logging to file: {log_file}")
            return file_handler
            
        except Exception as e:
            print(f"Failed to setup global file logging: {e}")
            return None
