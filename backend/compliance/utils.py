"""
compliance/utils.py - Utility functions for compliance app
"""

import re
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.validators import ValidationError
from django.core.exceptions import ObjectDoesNotExist
import phonenumbers
from phonenumbers import NumberParseException
import logging

logger = logging.getLogger(__name__)


def validate_id_number(id_number, id_type):
    """
    Validate ID number based on document type
    
    Args:
        id_number (str): The ID number to validate
        id_type (str): Type of ID document
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not id_number or not isinstance(id_number, str):
        return False
    
    id_number = id_number.strip()
    
    if id_type == 'passport':
        # Passport: Usually 8-9 characters, starts with a letter
        # Format: Letter followed by 7-8 digits
        return re.match(r'^[A-Z][0-9]{7,8}$', id_number.upper()) is not None
    
    elif id_type == 'national_id':
        # National ID: Varies by country, typically 6-20 digits, may include dashes
        # Accept digits and dashes, length 6-20
        return re.match(r'^[0-9\-]{6,20}$', id_number) is not None
    
    elif id_type == 'drivers_license':
        # Driver's license: Alphanumeric, varies by country
        # Accept alphanumeric, length 5-20
        return re.match(r'^[A-Z0-9]{5,20}$', id_number.upper()) is not None
    
    return True  # Default to True for other types


def validate_phone_number(phone_number, country_code=None):
    """
    Validate phone number using phonenumbers library
    
    Args:
        phone_number (str): Phone number to validate
        country_code (str): Default country code (e.g., 'US')
    
    Returns:
        tuple: (is_valid, formatted_number, error_message)
    """
    if not phone_number:
        return False, None, "Phone number is required"
    
    try:
        # Parse phone number
        parsed_number = phonenumbers.parse(phone_number, country_code)
        
        # Check if number is valid
        is_valid = phonenumbers.is_valid_number(parsed_number)
        
        if is_valid:
            # Format in E.164 format
            formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return True, formatted, None
        else:
            return False, None, "Invalid phone number"
    
    except NumberParseException as e:
        return False, None, str(e)
    except Exception as e:
        logger.error(f"Error validating phone number {phone_number}: {e}")
        return False, None, "Error validating phone number"


def calculate_age(date_of_birth):
    """
    Calculate age from date of birth
    
    Args:
        date_of_birth (datetime): Date of birth
    
    Returns:
        int: Age in years
    """
    if not date_of_birth:
        return 0
    
    today = timezone.now().date()
    birth_date = date_of_birth.date() if hasattr(date_of_birth, 'date') else date_of_birth
    
    age = today.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age


def calculate_risk_score(user_data, transactions=None):
    """
    Calculate risk score for KYC based on user data
    
    Args:
        user_data (dict): User information
        transactions (list): Optional transaction history
    
    Returns:
        tuple: (risk_score, risk_level)
    """
    risk_score = 0
    risk_factors = []
    
    # Age risk
    age = calculate_age(user_data.get('date_of_birth'))
    if age < 18:
        risk_score += 50
        risk_factors.append({'factor': 'under_18', 'score': 50})
    elif age < 25:
        risk_score += 15
        risk_factors.append({'factor': 'young_adult', 'score': 15})
    elif age > 65:
        risk_score += 10
        risk_factors.append({'factor': 'senior', 'score': 10})
    
    # Country risk
    high_risk_countries = ['AF', 'IR', 'KP', 'SY', 'YE', 'MM', 'SD', 'ZW']
    country = user_data.get('country_of_residence', '').upper()
    
    if country in high_risk_countries:
        risk_score += 40
        risk_factors.append({'factor': 'high_risk_country', 'score': 40, 'country': country})
    
    # Occupation risk
    high_risk_occupations = [
        'politician', 'government', 'official', 'cash business',
        'gambling', 'casino', 'adult entertainment', 'cryptocurrency',
        'money service', 'precious metals', 'art dealer'
    ]
    
    occupation = (user_data.get('occupation') or '').lower()
    for risk_occ in high_risk_occupations:
        if risk_occ in occupation:
            risk_score += 25
            risk_factors.append({'factor': 'high_risk_occupation', 'score': 25, 'occupation': occupation})
            break
    
    # Source of funds risk
    vague_sources = ['gift', 'inheritance', 'savings', 'investment', 'other']
    source = (user_data.get('source_of_funds') or '').lower()
    
    if any(vague in source for vague in vague_sources):
        risk_score += 20
        risk_factors.append({'factor': 'vague_source', 'score': 20, 'source': source})
    
    # Purpose of account risk
    high_risk_purposes = ['investment', 'trading', 'business', 'other']
    purpose = (user_data.get('purpose_of_account') or '').lower()
    
    if any(risk_purpose in purpose for risk_purpose in high_risk_purposes):
        risk_score += 15
        risk_factors.append({'factor': 'high_risk_purpose', 'score': 15, 'purpose': purpose})
    
    # Determine risk level
    if risk_score >= 70:
        risk_level = 'high'
    elif risk_score >= 30:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    return risk_score, risk_level, risk_factors


def check_sanctions(name, country, date_of_birth=None):
    """
    Check if name/country is in sanctions list (mock implementation)
    
    Args:
        name (str): Full name to check
        country (str): Country code to check
        date_of_birth (datetime): Optional date of birth
    
    Returns:
        tuple: (is_sanctioned, match_details)
    """
    # This is a mock implementation
    # In production, integrate with actual sanctions databases
    
    sanctions_list = [
        {
            'name': 'terror organization',
            'country': 'AF',
            'type': 'organization'
        },
        {
            'name': 'drug cartel',
            'country': 'MX',
            'type': 'organization'
        },
        {
            'name': 'john doe',
            'country': 'US',
            'type': 'individual',
            'date_of_birth': '1980-01-01'
        }
    ]
    
    name_lower = name.lower() if name else ''
    country_upper = country.upper() if country else ''
    
    for sanction in sanctions_list:
        # Check country match
        if sanction['country'] != country_upper:
            continue
        
        # Check name match (partial match for demonstration)
        sanction_name = sanction['name'].lower()
        if sanction_name in name_lower or name_lower in sanction_name:
            # If date of birth provided, check for individual sanctions
            if date_of_birth and sanction.get('type') == 'individual':
                sanction_dob = sanction.get('date_of_birth')
                if sanction_dob:
                    # Simple date comparison
                    dob_str = date_of_birth.strftime('%Y-%m-%d') if hasattr(date_of_birth, 'strftime') else str(date_of_birth)
                    if dob_str == sanction_dob:
                        return True, {'sanction': sanction, 'match_type': 'exact'}
            
            return True, {'sanction': sanction, 'match_type': 'name_match'}
    
    return False, None


def generate_verification_summary(verification):
    """
    Generate a summary of verification
    
    Args:
        verification (KYCVerification): Verification object
    
    Returns:
        dict: Summary information
    """
    from .models import KYCDocument
    
    documents = verification.documents.all() if hasattr(verification, 'documents') else []
    
    summary = {
        'verification_id': str(verification.id),
        'user_id': verification.user_id,
        'name': f"{verification.first_name} {verification.last_name}",
        'email': verification.email,
        'status': verification.verification_status,
        'compliance_level': verification.compliance_level,
        'risk_level': verification.risk_level,
        'risk_score': verification.risk_score,
        'documents': {
            'total': documents.count(),
            'approved': documents.filter(status='approved').count(),
            'pending': documents.filter(status='pending').count(),
            'types': list(documents.values_list('document_type', flat=True).distinct())
        },
        'timeline': {
            'created': verification.created_at.isoformat() if verification.created_at else None,
            'verified': verification.verified_at.isoformat() if verification.verified_at else None,
            'updated': verification.updated_at.isoformat() if verification.updated_at else None
        },
        'compliance_checks': verification.compliance_checks.count() if hasattr(verification, 'compliance_checks') else 0
    }
    
    return summary


def mask_sensitive_data(data, fields_to_mask=None):
    """
    Mask sensitive data for logging or display
    
    Args:
        data (dict): Data containing sensitive information
        fields_to_mask (list): List of field names to mask
    
    Returns:
        dict: Data with masked sensitive fields
    """
    if fields_to_mask is None:
        fields_to_mask = [
            'id_number', 'phone_number', 'email',
            'address_line1', 'address_line2',
            'account_number', 'wallet_address'
        ]
    
    masked_data = data.copy() if isinstance(data, dict) else dict(data)
    
    for field in fields_to_mask:
        if field in masked_data and masked_data[field]:
            value = str(masked_data[field])
            if len(value) > 4:
                masked_data[field] = value[:2] + '*' * (len(value) - 4) + value[-2:]
            else:
                masked_data[field] = '*' * len(value)
    
    return masked_data


def format_currency(amount, currency='USD'):
    """
    Format currency amount
    
    Args:
        amount (float): Amount to format
        currency (str): Currency code
    
    Returns:
        str: Formatted currency string
    """
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'CNY': '¥',
        'INR': '₹',
        'RUB': '₽',
        'BTC': '₿',
        'ETH': 'Ξ'
    }
    
    symbol = currency_symbols.get(currency.upper(), currency.upper())
    
    # Format with appropriate decimal places
    if currency.upper() in ['JPY', 'KRW']:
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:,.2f}"


def calculate_processing_time(start_time, end_time=None):
    """
    Calculate processing time between two timestamps
    
    Args:
        start_time (datetime): Start time
        end_time (datetime): End time (defaults to now)
    
    Returns:
        dict: Processing time in various units
    """
    if not start_time:
        return None
    
    if end_time is None:
        end_time = timezone.now()
    
    if end_time < start_time:
        return None
    
    delta = end_time - start_time
    
    return {
        'total_seconds': delta.total_seconds(),
        'seconds': delta.seconds % 60,
        'minutes': (delta.seconds // 60) % 60,
        'hours': delta.seconds // 3600,
        'days': delta.days,
        'formatted': str(delta).split('.')[0]  # Remove microseconds
    }


def validate_json_field(value, field_name, required_keys=None):
    """
    Validate JSON field structure
    
    Args:
        value: JSON value to validate
        field_name (str): Name of the field for error messages
        required_keys (list): List of required keys
    
    Returns:
        tuple: (is_valid, error_message, parsed_value)
    """
    if required_keys is None:
        required_keys = []
    
    # Check if value is a string that needs parsing
    if isinstance(value, str):
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in {field_name}: {str(e)}", None
    else:
        parsed_value = value
    
    # Check if it's a dict
    if not isinstance(parsed_value, dict):
        return False, f"{field_name} must be a JSON object", None
    
    # Check required keys
    missing_keys = [key for key in required_keys if key not in parsed_value]
    if missing_keys:
        return False, f"{field_name} missing required keys: {', '.join(missing_keys)}", None
    
    return True, None, parsed_value


def generate_report_id():
    """
    Generate a unique report ID
    
    Returns:
        str: Unique report ID
    """
    import uuid
    import time
    
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:8].upper()
    
    return f"REP-{timestamp}-{unique_id}"


def get_country_name(country_code):
    """
    Get country name from country code
    
    Args:
        country_code (str): 2-letter country code
    
    Returns:
        str: Country name or code if not found
    """
    country_names = {
        'US': 'United States',
        'GB': 'United Kingdom',
        'CA': 'Canada',
        'AU': 'Australia',
        'DE': 'Germany',
        'FR': 'France',
        'JP': 'Japan',
        'CN': 'China',
        'IN': 'India',
        'BR': 'Brazil',
        'RU': 'Russia',
        'ZA': 'South Africa',
        'NG': 'Nigeria',
        'KE': 'Kenya',
        'GH': 'Ghana',
        'EG': 'Egypt',
        'AE': 'United Arab Emirates',
        'SA': 'Saudi Arabia',
        'SG': 'Singapore',
        'MY': 'Malaysia',
        'ID': 'Indonesia',
        'TH': 'Thailand',
        'VN': 'Vietnam',
        'PH': 'Philippines',
        'KR': 'South Korea',
        'MX': 'Mexico',
        'AR': 'Argentina',
        'CL': 'Chile',
        'CO': 'Colombia',
        'PE': 'Peru',
    }
    
    return country_names.get(country_code.upper(), country_code.upper())


def is_business_hours(timestamp=None):
    """
    Check if current time is within business hours (9 AM - 5 PM, Monday-Friday)
    
    Args:
        timestamp (datetime): Timestamp to check (defaults to now)
    
    Returns:
        bool: True if within business hours
    """
    if timestamp is None:
        timestamp = timezone.now()
    
    # Convert to local time if timezone aware
    if timezone.is_aware(timestamp):
        timestamp = timezone.localtime(timestamp)
    
    # Check if weekday (Monday=0, Sunday=6)
    if timestamp.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if within 9 AM - 5 PM
    hour = timestamp.hour
    return 9 <= hour < 17