"""
OTP Service - One-Time Password generation and verification
Handles OTP creation, validation, and email sending for user verification
"""

import random
import string
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from utils.env_utils import get_env_int, get_env_bool
from utils.models import OTPVerification
from utils.email_service import email_service
from utils.logging_config import get_logger

logger = get_logger(__name__)

class OTPService:
    """Service for managing OTP verification"""
    
    def __init__(self):
        # Environment variables
        self.otp_length = get_env_int("OTP_LENGTH", 6)
        self.otp_expiry_minutes = get_env_int("OTP_EXPIRY_MINUTES", 10)
        self.max_attempts = get_env_int("OTP_MAX_ATTEMPTS", 3)
        self.resend_cooldown_minutes = get_env_int("OTP_RESEND_COOLDOWN", 2)
        self.cleanup_enabled = get_env_bool("OTP_CLEANUP_ENABLED", True)
    
    def generate_otp(self) -> str:
        """Generate a random OTP code"""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def create_otp_verification(
        self, 
        db: Session, 
        email: str, 
        purpose: str = "email_verification"
    ) -> Tuple[str, bool]:
        """
        Create and send OTP verification
        
        Returns:
            Tuple of (otp_code, email_sent_successfully)
        """
        try:
            # Check for existing active OTP
            existing_otp = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose,
                OTPVerification.is_active == True,
                OTPVerification.expires_at > datetime.utcnow()
            ).first()
            
            # Check resend cooldown
            if existing_otp:
                time_since_creation = datetime.utcnow() - existing_otp.created_at
                cooldown_delta = timedelta(minutes=self.resend_cooldown_minutes)
                
                if time_since_creation < cooldown_delta:
                    remaining_seconds = int((cooldown_delta - time_since_creation).total_seconds())
                    logger.warning(f"OTP resend attempted too soon for {email}")
                    raise ValueError(f"Please wait {remaining_seconds} seconds before requesting a new OTP")
                
                # Deactivate existing OTP
                existing_otp.is_active = False
                db.commit()
            
            # Generate new OTP
            otp_code = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Create OTP record
            otp_record = OTPVerification(
                email=email,
                otp_code=otp_code,
                purpose=purpose,
                expires_at=expires_at,
                max_attempts=self.max_attempts
            )
            
            db.add(otp_record)
            db.commit()
            db.refresh(otp_record)
            
            # Send email
            email_sent, email_message = email_service.send_otp_email(email, otp_code, purpose)
            
            if email_sent:
                logger.info(f"OTP created and sent successfully for {email}")
            else:
                logger.error(f"OTP created but email failed for {email}: {email_message}")
            
            return otp_code, email_sent
            
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to create OTP for {email}: {e}")
            raise Exception(f"Failed to create OTP verification: {str(e)}")
    
    def verify_otp(
        self, 
        db: Session, 
        email: str, 
        otp_code: str, 
        purpose: str = "email_verification"
    ) -> Tuple[bool, str, Optional[OTPVerification]]:
        """
        Verify OTP code
        
        Returns:
            Tuple of (is_valid, message, otp_record)
        """
        try:
            # Find active OTP
            otp_record = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose,
                OTPVerification.is_active == True
            ).first()
            
            if not otp_record:
                return False, "No active OTP found for this email", None
            
            # Check if expired
            if datetime.utcnow() > otp_record.expires_at:
                otp_record.is_active = False
                db.commit()
                return False, "OTP has expired. Please request a new one", otp_record
            
            # Check attempts
            if otp_record.attempts >= otp_record.max_attempts:
                otp_record.is_active = False
                db.commit()
                return False, "Maximum verification attempts exceeded. Please request a new OTP", otp_record
            
            # Increment attempts
            otp_record.attempts += 1
            
            # Verify code
            if otp_record.otp_code != otp_code:
                db.commit()
                remaining_attempts = otp_record.max_attempts - otp_record.attempts
                if remaining_attempts > 0:
                    return False, f"Invalid OTP code. {remaining_attempts} attempts remaining", otp_record
                else:
                    otp_record.is_active = False
                    db.commit()
                    return False, "Invalid OTP code. Maximum attempts exceeded", otp_record
            
            # Success - mark as verified
            otp_record.is_verified = True
            otp_record.verified_at = datetime.utcnow()
            otp_record.is_active = False
            db.commit()
            
            logger.info(f"OTP verified successfully for {email}")
            return True, "OTP verified successfully", otp_record
            
        except Exception as e:
            logger.error(f"Failed to verify OTP for {email}: {e}")
            return False, "OTP verification failed. Please try again", None
    
    def resend_otp(
        self, 
        db: Session, 
        email: str, 
        purpose: str = "email_verification"
    ) -> Tuple[bool, str]:
        """
        Resend OTP code
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check for existing active OTP
            existing_otp = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose,
                OTPVerification.is_active == True
            ).first()
            
            if not existing_otp:
                return False, "No active OTP found to resend"
            
            # Check cooldown
            time_since_creation = datetime.utcnow() - existing_otp.created_at
            cooldown_delta = timedelta(minutes=self.resend_cooldown_minutes)
            
            if time_since_creation < cooldown_delta:
                remaining_seconds = int((cooldown_delta - time_since_creation).total_seconds())
                return False, f"Please wait {remaining_seconds} seconds before requesting a new OTP"
            
            # Create new OTP
            otp_code, email_sent = self.create_otp_verification(db, email, purpose)
            
            if email_sent:
                return True, "OTP resent successfully"
            else:
                return False, "Failed to send OTP email"
                
        except Exception as e:
            logger.error(f"Failed to resend OTP for {email}: {e}")
            return False, "Failed to resend OTP. Please try again"
    
    def get_otp_status(
        self, 
        db: Session, 
        email: str, 
        purpose: str = "email_verification"
    ) -> Dict[str, Any]:
        """Get OTP status for an email"""
        try:
            otp_record = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.purpose == purpose,
                OTPVerification.is_active == True
            ).first()
            
            if not otp_record:
                return {
                    "has_active_otp": False,
                    "is_expired": False,
                    "attempts_remaining": 0,
                    "can_resend": True,
                    "expires_in_seconds": 0
                }
            
            now = datetime.utcnow()
            is_expired = now > otp_record.expires_at
            expires_in_seconds = max(0, int((otp_record.expires_at - now).total_seconds()))
            attempts_remaining = max(0, otp_record.max_attempts - otp_record.attempts)
            
            # Check if can resend
            time_since_creation = now - otp_record.created_at
            cooldown_delta = timedelta(minutes=self.resend_cooldown_minutes)
            can_resend = time_since_creation >= cooldown_delta
            
            return {
                "has_active_otp": True,
                "is_expired": is_expired,
                "attempts_remaining": attempts_remaining,
                "can_resend": can_resend,
                "expires_in_seconds": expires_in_seconds,
                "created_at": otp_record.created_at.isoformat(),
                "expires_at": otp_record.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get OTP status for {email}: {e}")
            return {
                "has_active_otp": False,
                "is_expired": False,
                "attempts_remaining": 0,
                "can_resend": True,
                "expires_in_seconds": 0
            }
    
    def cleanup_expired_otps(self, db: Session) -> int:
        """Clean up expired OTP records"""
        if not self.cleanup_enabled:
            return 0
        
        try:
            # Delete expired OTPs older than 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            deleted_count = db.query(OTPVerification).filter(
                OTPVerification.expires_at < cutoff_time
            ).delete()
            
            db.commit()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired OTP records")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired OTPs: {e}")
            db.rollback()
            return 0
    
    def invalidate_user_otps(
        self, 
        db: Session, 
        email: str, 
        purpose: str = None
    ) -> int:
        """Invalidate all active OTPs for a user"""
        try:
            query = db.query(OTPVerification).filter(
                OTPVerification.email == email,
                OTPVerification.is_active == True
            )
            
            if purpose:
                query = query.filter(OTPVerification.purpose == purpose)
            
            updated_count = query.update({"is_active": False})
            db.commit()
            
            if updated_count > 0:
                logger.info(f"Invalidated {updated_count} OTP records for {email}")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate OTPs for {email}: {e}")
            db.rollback()
            return 0
    
    def get_service_stats(self, db: Session) -> Dict[str, Any]:
        """Get OTP service statistics"""
        try:
            now = datetime.utcnow()
            
            # Count active OTPs
            active_otps = db.query(OTPVerification).filter(
                OTPVerification.is_active == True,
                OTPVerification.expires_at > now
            ).count()
            
            # Count expired OTPs
            expired_otps = db.query(OTPVerification).filter(
                OTPVerification.expires_at <= now
            ).count()
            
            # Count verified OTPs
            verified_otps = db.query(OTPVerification).filter(
                OTPVerification.is_verified == True
            ).count()
            
            # Count total OTPs
            total_otps = db.query(OTPVerification).count()
            
            return {
                "active_otps": active_otps,
                "expired_otps": expired_otps,
                "verified_otps": verified_otps,
                "total_otps": total_otps,
                "otp_length": self.otp_length,
                "expiry_minutes": self.otp_expiry_minutes,
                "max_attempts": self.max_attempts,
                "resend_cooldown_minutes": self.resend_cooldown_minutes
            }
            
        except Exception as e:
            logger.error(f"Failed to get OTP service stats: {e}")
            return {}

# Global service instance
otp_service = OTPService() 