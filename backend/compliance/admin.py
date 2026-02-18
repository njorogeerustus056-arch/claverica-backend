from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from .models import ComplianceSetting, TransferRequest, TransferLog
import json
from django.utils import timezone

@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'account', 'amount', 'status', 'tac_code', 'created_at', 'send_tac_button')
    readonly_fields = ('send_tac_button', 'created_at', 'updated_at', 'email_preview')
    fieldsets = (
        ('Transfer Details', {
            'fields': ('reference', 'account', 'amount', 'recipient_name', 'destination_type', 'destination_details')
        }),
        ('Verification', {
            'fields': ('requires_kyc', 'kyc_verified', 'tac_code', 'tac_generated_at', 'tac_expires_at', 'tac_sent_at')
        }),
        ('Settlement', {
            'fields': ('status', 'settled_by', 'settled_at', 'external_reference')
        }),
        ('Admin Actions', {
            'fields': ('send_tac_button', 'email_preview'),
            'classes': ('collapse', 'wide')
        }),
        ('Additional Info', {
            'fields': ('narration', 'generated_by', 'created_at', 'updated_at')
        }),
    )

    def send_tac_button(self, obj):
        if obj.status == 'tac_generated' and obj.tac_code:
            return format_html(
                '<a class="button" href="{}" style="background-color: #4CAF50; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-right: 10px;">'
                ' Send TAC Email</a>'
                '<a class="button" href="{}" style="background-color: #2196F3; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">'
                ' Send TAC SMS</a>',
                reverse('admin:send_tac_email', args=[obj.id]),
                reverse('admin:send_tac_sms', args=[obj.id])
            )
        elif obj.tac_code:
            return format_html('<span style="color: green;"> TAC Sent</span>')
        return "TAC not generated"
    send_tac_button.short_description = "Send TAC"

    def email_preview(self, obj):
        if obj.status == 'tac_generated' and obj.tac_code:
            #  FIXED: destination_details is already a dict, no json.loads needed
            dest_details = obj.destination_details if obj.destination_details else {}
            bank_name = dest_details.get('bank_name', 'your bank')
            account_number = dest_details.get('account_number', 'XXXX-XXXX')

            preview = f"""
            <div style="background: #f5f5f5; padding: 15px; border: 1px solid #ddd; margin: 10px 0;">
                <h4> Email Preview (will be sent from noreply@claverica.com):</h4>
                <div style="background: white; padding: 15px; border: 1px solid #ccc;">
                    <strong>Subject:</strong> Your Withdrawal Authorization Code - {obj.reference}<br><br>
                    <strong>To:</strong> {obj.account.email}<br><br>  #  FIXED: Changed obj.account.user.email to obj.account.email
                    Dear {obj.account.first_name or 'Valued Client'},<br><br>  #  FIXED: Changed obj.account.user.get_full_name() to obj.account.first_name
                    Your withdrawal request has been approved.<br><br>
                    <strong>Amount:</strong> ${obj.amount:,.2f}<br>
                    <strong>Recipient:</strong> {obj.recipient_name}<br>
                    <strong>Bank:</strong> {bank_name} ({account_number})<br><br>
                    <strong>Security Code:</strong> <code style="font-size: 18px; background: #f0f0f0; padding: 5px 10px; border-radius: 4px;">{obj.tac_code}</code><br><br>
                    The code is valid for 24 hours.<br><br>
                    <em>Claverica Security Team</em>
                </div>
            </div>
            """
            return format_html(preview)
        return "Email preview available after TAC generation"
    email_preview.short_description = "Email Preview"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/send-tac-email/',
                 self.admin_site.admin_view(self.send_tac_email),
                 name='send_tac_email'),
            path('<path:object_id>/send-tac-sms/',
                 self.admin_site.admin_view(self.send_tac_sms),
                 name='send_tac_sms'),
        ]
        return custom_urls + urls

    def send_tac_email(self, request, object_id):
        from django.http import HttpResponseRedirect
        from django.contrib import messages

        transfer = TransferRequest.objects.get(id=object_id)

        if transfer.status == 'tac_generated' and transfer.tac_code:
            try:
                #  FIXED: destination_details is already a dict
                dest_details = transfer.destination_details if transfer.destination_details else {}
                bank_name = dest_details.get('bank_name', 'your bank')
                account_number = dest_details.get('account_number', 'XXXX-XXXX')

                subject = f"Your Withdrawal Authorization Code - {transfer.reference}"
                message = f"""Dear {transfer.account.first_name or 'Valued Client'},

Your withdrawal request has been approved and is ready for processing.

TRANSACTION DETAILS:
 Reference: {transfer.reference}
 Amount: ${transfer.amount:,.2f}
 Recipient: {transfer.recipient_name}
 Destination: {bank_name} ({account_number})

YOUR SECURITY CODE:
{transfer.tac_code}

IMPORTANT INSTRUCTIONS:
1. Enter this 6-digit code in your Claverica dashboard to authorize the transfer
2. The code is valid for 24 hours
3. Do not share this code with anyone

After code verification, our team will process your funds transfer. You will receive another notification once the funds have been sent to your bank.

Processing typically takes 1-2 business days.

For security reasons, if you did not initiate this transaction, please contact our support team immediately.

Best regards,
The Claverica Security Team
noreply@claverica.com"""

                send_mail(
                    subject=subject,
                    message=message.strip(),
                    from_email='Claverica Security <noreply@claverica.com>',
                    recipient_list=[transfer.account.email],  #  FIXED: Changed transfer.account.user.email to transfer.account.email
                    fail_silently=False,
                )

                transfer.mark_tac_sent()

                messages.success(
                    request,
                    f" TAC {transfer.tac_code} sent from noreply@claverica.com to {transfer.account.email}"
                )

            except Exception as e:
                messages.error(request, f" Failed to send email: {str(e)}")

        return HttpResponseRedirect(
            reverse('admin:compliance_transferrequest_change', args=[object_id])
        )

    def send_tac_sms(self, request, object_id):
        from django.http import HttpResponseRedirect
        from django.contrib import messages

        transfer = TransferRequest.objects.get(id=object_id)

        if transfer.status == 'tac_generated' and transfer.tac_code:
            try:
                sms_message = f"Claverica: Your auth code is {transfer.tac_code} for ${transfer.amount} transfer to {transfer.recipient_name}. Code valid 24h."

                # For now, just log it (you'll integrate with SMS gateway later)
                print(f"\n SMS would be sent to {transfer.account.phone if hasattr(transfer.account, 'phone') else 'client'}:")
                print(sms_message)
                print(f"From: noreply@claverica.com\n")

                transfer.mark_tac_sent()

                messages.success(
                    request,
                    f" TAC {transfer.tac_code} SMS prepared for {transfer.account.email}"
                )

            except Exception as e:
                messages.error(request, f" Failed to prepare SMS: {str(e)}")

        return HttpResponseRedirect(
            reverse('admin:compliance_transferrequest_change', args=[object_id])
        )

@admin.register(ComplianceSetting)
class ComplianceSettingAdmin(admin.ModelAdmin):
    list_display = ('setting_type', 'value', 'description', 'is_active', 'updated_by')

@admin.register(TransferLog)
class TransferLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'transfer', 'log_type', 'created_by', 'created_at')