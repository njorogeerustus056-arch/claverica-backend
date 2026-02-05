"""
kyc/views.py - UPDATED VERSION (ADD DRF API VIEWS)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import KYCDocument, KYCSetting, KYCSubmission
from .forms import KYCDocumentForm
from .serializers import (
    KYCDocumentSerializer, KYCStatusSerializer,
    KYCRequirementSerializer, KYCRequirementResponseSerializer,
    KYCSubmissionSerializer, KYCSettingSerializer
)
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
import uuid

# ========== FUNCTION-BASED VIEWS (HTML PAGES) ==========

@login_required
def submit_documents(request):
    """HTML page for submitting KYC documents"""
    if request.method == 'POST':
        form = KYCDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            kyc_doc = form.save(commit=False)
            kyc_doc.user = request.user
            kyc_doc.save()
            messages.success(request, 'KYC documents submitted successfully! They will be reviewed within 24-48 hours.')
            return redirect('kyc_status')
    else:
        form = KYCDocumentForm()
    
    return render(request, 'kyc/submit.html', {'form': form})

@login_required
def kyc_status(request):
    """HTML page to check KYC status"""
    try:
        latest_kyc = KYCDocument.objects.filter(user=request.user).latest('submitted_at')
        context = {
            'kyc_document': latest_kyc,
            'is_approved': latest_kyc.is_approved,
            'status': latest_kyc.status,
        }
    except KYCDocument.DoesNotExist:
        context = {
            'kyc_document': None,
            'has_kyc': False,
        }
    
    return render(request, 'kyc/status.html', context)

@login_required
def check_kyc_requirement(request):
    """HTML page to check if KYC is required"""
    if request.method == 'POST':
        service_type = request.POST.get('service_type')
        amount = request.POST.get('amount', 0)
        
        try:
            setting = KYCSetting.objects.get(service_type=service_type, is_active=True)
            requires_kyc = setting.requires_kyc and float(amount) > float(setting.threshold_amount)
            
            # Check if user already has approved KYC
            has_approved_kyc = KYCDocument.objects.filter(
                user=request.user,
                status='approved'
            ).exists()
            
            context = {
                'requires_kyc': requires_kyc and not has_approved_kyc,
                'threshold_amount': setting.threshold_amount,
                'requested_amount': amount,
                'service_type': service_type,
                'has_approved_kyc': has_approved_kyc,
                'setting': setting,
            }
        except KYCSetting.DoesNotExist:
            context = {
                'requires_kyc': False,
                'error': 'Service not configured for KYC',
            }
        
        return render(request, 'kyc/check_requirement_result.html', context)
    
    return render(request, 'kyc/check_requirement.html')

def test_api_page(request):
    """Test page for API documentation"""
    return render(request, 'kyc/test_api.html')

# Admin views
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    """Admin dashboard for KYC review"""
    pending_docs = KYCDocument.objects.filter(status='pending').order_by('submitted_at')
    under_review = KYCDocument.objects.filter(status='under_review').order_by('submitted_at')
    
    context = {
        'pending_docs': pending_docs,
        'under_review_docs': under_review,
        'total_pending': pending_docs.count(),
    }
    return render(request, 'kyc/admin/dashboard.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_review_document(request, document_id):
    """Admin page to review a specific KYC document"""
    kyc_doc = get_object_or_404(KYCDocument, id=document_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            kyc_doc.status = 'approved'
            kyc_doc.reviewed_by = request.user
            kyc_doc.reviewed_at = timezone.now()
            messages.success(request, f'KYC approved for {kyc_doc.user.email}')
        
        elif action == 'reject':
            kyc_doc.status = 'rejected'
            kyc_doc.reviewed_by = request.user
            kyc_doc.reviewed_at = timezone.now()
            kyc_doc.rejection_reason = notes or 'Rejected by administrator'
            messages.warning(request, f'KYC rejected for {kyc_doc.user.email}')
        
        elif action == 'request_correction':
            kyc_doc.status = 'needs_correction'
            kyc_doc.rejection_reason = notes or 'Correction required'
            messages.info(request, f'Correction requested for {kyc_doc.user.email}')
        
        kyc_doc.admin_notes = notes
        kyc_doc.save()
        return redirect('admin_dashboard')
    
    context = {
        'kyc_doc': kyc_doc,
        'user': kyc_doc.user,
    }
    return render(request, 'kyc/admin/review_document.html', context)

# ========== DRF API VIEWS ==========

class KYCDocumentViewSet(viewsets.ModelViewSet):
    """DRF ViewSet for KYC Document API"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KYCDocumentSerializer

    def get_queryset(self):
        """Users can only see their own documents"""
        return KYCDocument.objects.filter(user=self.request.user).order_by('-submitted_at')

    def perform_create(self, serializer):
        """Save with current user and pending status"""
        serializer.save(
            user=self.request.user,
            status='pending'
        )

        # Send confirmation email (you need to implement this function)
        # send_kyc_submission_email(self.request.user, serializer.instance)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current KYC status for user"""
        try:
            latest_kyc = KYCDocument.objects.filter(user=request.user).latest('submitted_at')

            data = {
                'has_kyc': True,
                'is_approved': latest_kyc.is_approved,
                'status': latest_kyc.status,
                'status_display': latest_kyc.get_status_display(),
                'submitted_at': latest_kyc.submitted_at,
                'reviewed_at': latest_kyc.reviewed_at,
                'rejection_reason': latest_kyc.rejection_reason,
                'document_type': latest_kyc.document_type
            }

        except KYCDocument.DoesNotExist:
            data = {
                'has_kyc': False,
                'is_approved': False,
                'status': 'no_kyc',
                'status_display': 'No KYC Submitted'
            }

        serializer = KYCStatusSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def submissions(self, request):
        """Get user's KYC submission history"""
        submissions = KYCSubmission.objects.filter(user=request.user).order_by('-created_at')
        serializer = KYCSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class KYCRequirementAPIView(APIView):
    """API endpoint to check if KYC is required"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Check if KYC is required for a service/amount"""
        serializer = KYCRequirementSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        service_type = data['service_type']
        amount = data['amount']

        try:
            # Get KYC setting for this service
            setting = KYCSetting.objects.get(service_type=service_type, is_active=True)
        except KYCSetting.DoesNotExist:
            return Response({
                'requires_kyc': False,
                'has_approved_kyc': False,
                'threshold_amount': 1500.00,
                'requested_amount': float(amount),
                'service_type': service_type,
                'message': 'Service not configured for KYC'
            })

        # Check if user already has approved KYC
        has_approved_kyc = KYCDocument.objects.filter(
            user=request.user,
            status='approved'
        ).exists()

        # If user has approved KYC, no need for new one
        if has_approved_kyc:
            return Response({
                'requires_kyc': False,
                'has_approved_kyc': True,
                'threshold_amount': float(setting.threshold_amount),
                'requested_amount': float(amount),
                'service_type': service_type,
                'message': 'User has approved KYC'
            })

        # Check threshold
        requires_kyc = setting.requires_kyc and float(amount) > float(setting.threshold_amount)

        # If KYC is required, create a submission record
        if requires_kyc:
            submission = KYCSubmission.objects.create(
                user=request.user,
                service_type=service_type,
                requested_for=f"{setting.get_service_type_display()} (${amount})",
                amount_triggered=amount,
                threshold_amount=setting.threshold_amount
            )

            response_data = {
                'requires_kyc': True,
                'has_approved_kyc': False,
                'threshold_amount': float(setting.threshold_amount),
                'requested_amount': float(amount),
                'service_type': service_type,
                'submission_id': submission.id,
                'message': f'KYC required for {setting.get_service_type_display()} above ${setting.threshold_amount}'
            }
        else:
            response_data = {
                'requires_kyc': False,
                'has_approved_kyc': False,
                'threshold_amount': float(setting.threshold_amount),
                'requested_amount': float(amount),
                'service_type': service_type,
                'message': f'Amount below threshold of ${setting.threshold_amount}'
            }

        response_serializer = KYCRequirementResponseSerializer(response_data)
        return Response(response_serializer.data)


class AdminKYCViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-only API for KYC management"""

    permission_classes = [permissions.IsAdminUser]
    queryset = KYCDocument.objects.all().order_by('-submitted_at')
    serializer_class = KYCDocumentSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a KYC document (admin only)"""
        kyc_doc = self.get_object()

        kyc_doc.status = 'approved'
        kyc_doc.reviewed_by = request.user
        kyc_doc.reviewed_at = timezone.now()
        kyc_doc.admin_notes = f"Approved by {request.user.email} via API"
        kyc_doc.save()

        # Send approval email (you need to implement this function)
        # send_kyc_approval_email(kyc_doc.user, kyc_doc)

        return Response({
            'success': True,
            'message': f'KYC approved for {kyc_doc.user.email}',
            'status': kyc_doc.status
        })

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending KYC documents"""
        pending_docs = KYCDocument.objects.filter(status='pending').order_by('submitted_at')
        serializer = self.get_serializer(pending_docs, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_kyc_status(request):
    """Simple API endpoint for KYC status"""
    try:
        latest_kyc = KYCDocument.objects.filter(user=request.user).latest('submitted_at')

        return Response({
            'has_kyc': True,
            'status': latest_kyc.status,
            'is_approved': latest_kyc.is_approved,
            'submitted_at': latest_kyc.submitted_at,
            'document_type': latest_kyc.get_document_type_display()
        })

    except KYCDocument.DoesNotExist:
        return Response({
            'has_kyc': False,
            'status': 'no_kyc',
            'is_approved': False,
            'message': 'No KYC documents submitted'
        })