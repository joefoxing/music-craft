import logging
import json
from datetime import datetime
from flask import request, has_request_context

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output logs in JSON format.
    """
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'funcName': record.funcName,
            'lineno': record.lineno,
        }

        if has_request_context():
            log_record.update({
                'remote_addr': request.remote_addr,
                'method': request.method,
                'path': request.path,
                'user_agent': str(request.user_agent),
            })
            # Try to add user_id if available (assuming flask_login)
            try:
                from flask_login import current_user
                if current_user.is_authenticated:
                    log_record['user_id'] = str(current_user.id)
            except ImportError:
                pass
            
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_record)

def configure_logging(app):
    """
    Configure structured JSON logging for the Flask app.
    """
    # Create handler
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    # Configure app logger
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    # Remove default Flask handlers to avoid duplicate/non-JSON logs if necessary
    # Check if there are existing handlers and remove them if they are not our JSON handler
    # Note: Flask adds a default handler. We want to replace it or ensure ours is used.
    # A safe approach is to keep ours and let Flask manage its own, but typically 
    # for production we want only JSON.
    
    # Clear existing handlers to ensure we only have the JSON handler
    if app.logger.hasHandlers():
        app.logger.handlers.clear()
    
    app.logger.addHandler(handler)
    
    # Optional: Configure werkzeug logger to also use JSON if desired, 
    # but usually app logs are the most important.
    # werkzeug_logger = logging.getLogger('werkzeug')
    # werkzeug_logger.handlers.clear()
    # werkzeug_logger.addHandler(handler)
