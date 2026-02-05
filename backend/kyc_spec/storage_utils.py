"""
Storage utilities for KYC Spec Dumpster
Handles file system operations for storing dumps, logs, and uploads
"""

import os
import json
import csv
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class KycSpecStorage:
    """Storage manager for KYC Spec dumpster"""
    
    @staticmethod
    def get_storage_root():
        """Get the root storage directory for KYC Spec"""
        return os.path.join(settings.MEDIA_ROOT, 'kyc_spec')
    
    @staticmethod
    def ensure_directories():
        """Ensure all necessary directories exist"""
        root = KycSpecStorage.get_storage_root()
        directories = [
            os.path.join(root, 'dumps', 'loan'),
            os.path.join(root, 'dumps', 'insurance'),
            os.path.join(root, 'dumps', 'escrow'),
            os.path.join(root, 'logs'),
            os.path.join(root, 'uploads'),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            # Create .gitkeep file to keep empty directories in git
            gitkeep = os.path.join(directory, '.gitkeep')
            if not os.path.exists(gitkeep):
                with open(gitkeep, 'w') as f:
                    f.write('# Directory placeholder')
        
        logger.info(f"KYC Spec storage directories ensured at: {root}")
        return True
    
    @staticmethod
    def save_json_dump(dump_id, product_type, data):
        """Save JSON dump to file system"""
        try:
            # Ensure directories exist
            KycSpecStorage.ensure_directories()
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{dump_id}_{timestamp}.json"
            
            # Determine directory based on product type
            product_dir = product_type.lower()
            if product_dir not in ['loan', 'insurance', 'escrow']:
                product_dir = 'other'
            
            dump_dir = os.path.join(
                KycSpecStorage.get_storage_root(),
                'dumps',
                product_dir,
                datetime.now().strftime('%Y-%m-%d')
            )
            os.makedirs(dump_dir, exist_ok=True)
            
            # Save the file
            filepath = os.path.join(dump_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'dump_id': dump_id,
                    'product_type': product_type,
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f, indent=2, default=str)
            
            logger.debug(f"Saved JSON dump to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save JSON dump: {str(e)}")
            return None
    
    @staticmethod
    def log_to_csv(dump_data):
        """Log dump entry to CSV file for sales team"""
        try:
            # Ensure directories exist
            KycSpecStorage.ensure_directories()
            
            csv_path = os.path.join(
                KycSpecStorage.get_storage_root(),
                'logs',
                'leads.csv'
            )
            
            # Check if file exists and has headers
            file_exists = os.path.exists(csv_path)
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'timestamp', 'dump_id', 'product_type', 'product_subtype',
                    'user_email', 'user_phone', 'document_count',
                    'source', 'status', 'ip_address'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'timestamp': dump_data.get('created_at', datetime.now().isoformat()),
                    'dump_id': dump_data.get('id', ''),
                    'product_type': dump_data.get('product_type', ''),
                    'product_subtype': dump_data.get('product_subtype', ''),
                    'user_email': dump_data.get('user_email', ''),
                    'user_phone': dump_data.get('user_phone', ''),
                    'document_count': dump_data.get('document_count', 0),
                    'source': dump_data.get('source', 'web'),
                    'status': dump_data.get('status', 'collected'),
                    'ip_address': dump_data.get('ip_address', '')
                })
            
            logger.debug(f"Logged to CSV: {dump_data.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log to CSV: {str(e)}")
            return False
    
    @staticmethod
    def log_submission(product_type, user_email):
        """Log simple submission to text log"""
        try:
            log_path = os.path.join(
                KycSpecStorage.get_storage_root(),
                'logs',
                'submissions.log'
            )
            
            with open(log_path, 'a', encoding='utf-8') as logfile:
                log_entry = f"{datetime.now().isoformat()} | {product_type} | {user_email or 'anonymous'}\n"
                logfile.write(log_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write to log: {str(e)}")
            return False
    
    @staticmethod
    def get_stats():
        """Get statistics about stored dumps"""
        try:
            root = KycSpecStorage.get_storage_root()
            stats = {
                'total_dumps': 0,
                'by_product': {'loan': 0, 'insurance': 0, 'escrow': 0, 'other': 0},
                'today': 0,
                'storage_size_mb': 0
            }
            
            # Count JSON files in dumps directory
            dumps_dir = os.path.join(root, 'dumps')
            if os.path.exists(dumps_dir):
                for product in ['loan', 'insurance', 'escrow', 'other']:
                    product_dir = os.path.join(dumps_dir, product)
                    if os.path.exists(product_dir):
                        count = sum(len(files) for _, _, files in os.walk(product_dir))
                        stats['by_product'][product] = count
                        stats['total_dumps'] += count
            
            # Get CSV entries count
            csv_path = os.path.join(root, 'logs', 'leads.csv')
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Subtract header line
                    stats['csv_entries'] = max(0, len(lines) - 1)
            
            # Calculate storage size (simplified)
            if os.path.exists(root):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(root):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                stats['storage_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {'error': str(e)}