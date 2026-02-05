from django.core.management.base import BaseCommand
import os
from pathlib import Path

class Command(BaseCommand):
    help = "Initialize KYC Spec storage directories"
    
    def handle(self, *args, **options):
        self.stdout.write("Initializing KYC Spec storage...")
        
        # Get project root
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        media_dir = base_dir / "media" / "kyc_spec"
        
        # Create directories
        directories = [
            media_dir / "dumps" / "loan",
            media_dir / "dumps" / "insurance", 
            media_dir / "dumps" / "escrow",
            media_dir / "logs",
            media_dir / "uploads"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.stdout.write(f"  Created: {directory.relative_to(base_dir)}")
        
        # Create placeholder files
        leads_csv = media_dir / "logs" / "leads.csv"
        submissions_log = media_dir / "logs" / "submissions.log"
        
        leads_csv.touch()
        submissions_log.touch()
        
        # Add headers if file is empty
        if leads_csv.stat().st_size == 0:
            with open(leads_csv, "w") as f:
                f.write("timestamp,dump_id,product_type,product_subtype,user_email,user_phone,document_count,source,status,ip_address\n")
        
        self.stdout.write(self.style.SUCCESS("? KYC Spec storage initialized!"))
