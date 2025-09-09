#!/usr/bin/env python3
"""
Email Notification Service for Vehicle Maintenance Tracker
Uses Gmail SMTP for free email notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta
from typing import List, Optional
import os
from sqlmodel import Session, select
from database import get_engine
from models import Vehicle, FutureMaintenance, MaintenanceRecord, EmailSubscription

class EmailNotificationService:
    """Service for sending maintenance reminder emails"""
    
    def __init__(self):
        # Gmail SMTP configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("GMAIL_EMAIL")  # Your Gmail address
        self.sender_password = os.getenv("GMAIL_APP_PASSWORD")  # Gmail App Password
        
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send an email using Gmail SMTP"""
        
        if not self.sender_email or not self.sender_password:
            print("❌ Gmail credentials not configured")
            return False
            
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add body to email
            message.attach(MIMEText(body, "html"))
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def send_maintenance_reminder(self, vehicle: Vehicle, future_maintenance: List[FutureMaintenance]) -> bool:
        """Send maintenance reminder email for a vehicle"""
        
        if not vehicle.email_notification_email or not vehicle.email_notifications_enabled:
            return False
            
        # Check if we should send reminder (based on frequency)
        if vehicle.last_email_sent:
            days_since_last = (date.today() - vehicle.last_email_sent).days
            if days_since_last < vehicle.email_reminder_frequency:
                return False
        
        # Create email content
        subject = f"🔧 Maintenance Reminder: {vehicle.name}"
        
        # Build maintenance list
        maintenance_list = ""
        for maintenance in future_maintenance:
            if maintenance.is_active:
                maintenance_list += f"""
                <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #007bff;">
                    <h3 style="margin: 0 0 10px 0; color: #333;">{maintenance.maintenance_type}</h3>
                    <p style="margin: 5px 0;"><strong>Vehicle:</strong> {vehicle.name} ({vehicle.year} {vehicle.make} {vehicle.model})</p>
                    {f'<p style="margin: 5px 0;"><strong>Target Mileage:</strong> {maintenance.target_mileage:,} miles</p>' if maintenance.target_mileage else ''}
                    {f'<p style="margin: 5px 0;"><strong>Target Date:</strong> {maintenance.target_date}</p>' if maintenance.target_date else ''}
                    {f'<p style="margin: 5px 0;"><strong>Estimated Cost:</strong> ${maintenance.estimated_cost:.2f}</p>' if maintenance.estimated_cost else ''}
                    {f'<p style="margin: 5px 0;"><strong>Notes:</strong> {maintenance.notes}</p>' if maintenance.notes else ''}
                </div>
                """
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #007bff; text-align: center;">🔧 Vehicle Maintenance Reminder</h1>
                
                <p>Hello!</p>
                
                <p>This is a friendly reminder that your vehicle <strong>{vehicle.name}</strong> has upcoming maintenance items:</p>
                
                {maintenance_list}
                
                <div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 8px;">
                    <h3 style="margin: 0 0 10px 0; color: #007bff;">📋 Next Steps:</h3>
                    <ul>
                        <li>Review the maintenance items above</li>
                        <li>Schedule service appointments as needed</li>
                        <li>Update your maintenance records after service</li>
                        <li>Mark completed items in your Vehicle Maintenance Tracker</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="https://your-app-url.com" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Maintenance Tracker
                    </a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                
                <p style="font-size: 12px; color: #666; text-align: center;">
                    This email was sent from your Vehicle Maintenance Tracker.<br>
                    You can disable these notifications in your vehicle settings.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email
        success = self.send_email(vehicle.email_notification_email, subject, body)
        
        if success:
            # Update last email sent date
            with Session(get_engine()) as session:
                vehicle.last_email_sent = date.today()
                session.add(vehicle)
                session.commit()
        
        return success
    
    def check_and_send_reminders(self) -> int:
        """Check all vehicles and send maintenance reminders"""
        
        emails_sent = 0
        
        with Session(get_engine()) as session:
            # Get all vehicles with email notifications enabled
            statement = select(Vehicle).where(
                Vehicle.email_notifications_enabled == True,
                Vehicle.email_notification_email.isnot(None)
            )
            vehicles = session.exec(statement).all()
            
            for vehicle in vehicles:
                # Get active future maintenance for this vehicle
                maintenance_statement = select(FutureMaintenance).where(
                    FutureMaintenance.vehicle_id == vehicle.id,
                    FutureMaintenance.is_active == True
                )
                future_maintenance = session.exec(maintenance_statement).all()
                
                if future_maintenance:
                    if self.send_maintenance_reminder(vehicle, future_maintenance):
                        emails_sent += 1
        
        print(f"📧 Sent {emails_sent} maintenance reminder emails")
        return emails_sent
    
    def send_subscription_reminder(self, subscription: EmailSubscription, future_maintenance: List[FutureMaintenance]) -> bool:
        """Send maintenance reminder email for a specific subscription"""
        
        if not subscription.is_active:
            return False
            
        # Check if we should send reminder (based on frequency)
        if subscription.last_email_sent:
            days_since_last = (date.today() - subscription.last_email_sent).days
            if days_since_last < subscription.reminder_frequency:
                return False
        
        # Create email content
        subject = f"🔧 Maintenance Reminder: {subscription.vehicle.name}"
        
        # Build maintenance list
        maintenance_list = ""
        for maintenance in future_maintenance:
            if maintenance.is_active:
                maintenance_list += f"""
                <div style="background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #007bff;">
                    <h3 style="margin: 0 0 10px 0; color: #333;">{maintenance.maintenance_type}</h3>
                    <p style="margin: 5px 0;"><strong>Vehicle:</strong> {subscription.vehicle.name} ({subscription.vehicle.year} {subscription.vehicle.make} {subscription.vehicle.model})</p>
                    {f'<p style="margin: 5px 0;"><strong>Target Mileage:</strong> {maintenance.target_mileage:,} miles</p>' if maintenance.target_mileage else ''}
                    {f'<p style="margin: 5px 0;"><strong>Target Date:</strong> {maintenance.target_date}</p>' if maintenance.target_date else ''}
                    {f'<p style="margin: 5px 0;"><strong>Estimated Cost:</strong> ${maintenance.estimated_cost:.2f}</p>' if maintenance.estimated_cost else ''}
                    {f'<p style="margin: 5px 0;"><strong>Notes:</strong> {maintenance.notes}</p>' if maintenance.notes else ''}
                </div>
                """
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #007bff; text-align: center;">🔧 Vehicle Maintenance Reminder</h1>
                
                <p>Hello!</p>
                
                <p>This is a friendly reminder that your vehicle <strong>{subscription.vehicle.name}</strong> has upcoming maintenance items:</p>
                
                {maintenance_list}
                
                <div style="background-color: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 8px;">
                    <h3 style="margin: 0 0 10px 0; color: #007bff;">📋 Next Steps:</h3>
                    <ul>
                        <li>Review the maintenance items above</li>
                        <li>Schedule service appointments as needed</li>
                        <li>Update your maintenance records after service</li>
                        <li>Mark completed items in your Vehicle Maintenance Tracker</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="https://your-app-url.com" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Maintenance Tracker
                    </a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                
                <p style="font-size: 12px; color: #666; text-align: center;">
                    This email was sent from your Vehicle Maintenance Tracker.<br>
                    You can manage your email subscriptions at: <a href="https://your-app-url.com/notifications">Email Notifications</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email
        success = self.send_email(subscription.email_address, subject, body)
        
        if success:
            # Update last email sent date
            with Session(get_engine()) as session:
                subscription.last_email_sent = date.today()
                session.add(subscription)
                session.commit()
        
        return success
    
    def check_and_send_subscription_reminders(self) -> int:
        """Check all email subscriptions and send maintenance reminders"""
        
        emails_sent = 0
        
        with Session(get_engine()) as session:
            # Get all active email subscriptions
            statement = select(EmailSubscription).where(EmailSubscription.is_active == True)
            subscriptions = session.exec(statement).all()
            
            for subscription in subscriptions:
                # Get active future maintenance for this vehicle
                maintenance_statement = select(FutureMaintenance).where(
                    FutureMaintenance.vehicle_id == subscription.vehicle_id,
                    FutureMaintenance.is_active == True
                )
                future_maintenance = session.exec(maintenance_statement).all()
                
                if future_maintenance:
                    if self.send_subscription_reminder(subscription, future_maintenance):
                        emails_sent += 1
        
        print(f"📧 Sent {emails_sent} subscription reminder emails")
        return emails_sent
    
    def send_test_email(self, email_address: str) -> bool:
        """Send a test email to verify configuration"""
        
        subject = "🧪 Test Email - Vehicle Maintenance Tracker"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #007bff; text-align: center;">🧪 Test Email</h1>
                
                <p>Hello!</p>
                
                <p>This is a test email from your Vehicle Maintenance Tracker to verify that email notifications are working correctly.</p>
                
                <div style="background-color: #d4edda; padding: 15px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #28a745;">
                    <h3 style="margin: 0 0 10px 0; color: #155724;">✅ Email Service Working!</h3>
                    <p style="margin: 0; color: #155724;">
                        If you received this email, your notification system is properly configured and ready to send maintenance reminders.
                    </p>
                </div>
                
                <p style="text-align: center; margin-top: 30px;">
                    <a href="https://your-app-url.com/notifications" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Manage Email Notifications
                    </a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                
                <p style="font-size: 12px; color: #666; text-align: center;">
                    This test email was sent from your Vehicle Maintenance Tracker.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email_address, subject, body)

def setup_gmail_credentials():
    """Instructions for setting up Gmail App Password"""
    
    instructions = """
    📧 Gmail SMTP Setup Instructions:
    
    1. Enable 2-Factor Authentication on your Gmail account
    2. Generate an App Password:
       - Go to Google Account settings
       - Security → 2-Step Verification → App passwords
       - Generate password for "Mail"
    3. Set environment variables:
       export GMAIL_EMAIL="your-email@gmail.com"
       export GMAIL_APP_PASSWORD="your-app-password"
    
    Or add to your .env file:
    GMAIL_EMAIL=your-email@gmail.com
    GMAIL_APP_PASSWORD=your-app-password
    """
    
    print(instructions)

if __name__ == "__main__":
    # Test email service
    service = EmailNotificationService()
    
    if not service.sender_email or not service.sender_password:
        setup_gmail_credentials()
    else:
        print("🧪 Testing email service...")
        # You can add a test email here
        print("✅ Email service configured successfully")
