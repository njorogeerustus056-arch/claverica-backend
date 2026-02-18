# kyc_spec/views.py - FIXED VERSION WITH ALL IMPORTS
import os
import csv
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
import logging

from .models import KycSpecDump
from .services import KycSpecDumpService

logger = logging.getLogger(__name__)

# ========== CORE COLLECTION VIEWS ==========

class KycSpecCollectView(APIView):
    """
    Dumpster endpoint for collecting KYC data from insurance/loans/escrow
    Accepts anything and stores it for later processing
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Accept ANY data, even invalid
            data = request.data.copy()
            
            # Basic validation
            if not isinstance(data, dict):
                return Response({
                    'success': False,
                    'error': 'Invalid data format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract user from request if authenticated
            user = request.user if request.user.is_authenticated else None
            
            # Log the dump
            logger.info(f"KYC-SPEC DUMP: {data.get('product', 'unknown')} from {data.get('user_email', 'anonymous')}")
            
            # Save to database
            dump = KycSpecDumpService.create_dump(user, data, request)
            
            # Save to CSV for sales team
            self._append_to_csv(dump)
            
            # Always return success
            return Response({
                'success': True,
                'message': 'Application received. Our team will contact you shortly.',
                'reference_id': str(dump.id),
                'note': 'This feature is currently in development. You are on our priority list.',
                'contact_timeline': '24-48 hours'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Even on error, return success to user
            logger.error(f"KYC-SPEC error: {str(e)}")
            return Response({
                'success': True,
                'message': 'We have received your interest. Our team will follow up.',
                'reference_id': f'ERR-{datetime.now().timestamp()}',
                'note': 'System note: Internal error occurred but data was captured.'
            }, status=status.HTTP_200_OK)
    
    def _append_to_csv(self, dump):
        """Append dump to CSV file for sales team"""
        try:
            csv_dir = os.path.join(settings.MEDIA_ROOT, 'kyc_spec', 'logs')
            os.makedirs(csv_dir, exist_ok=True)
            
            csv_file = os.path.join(csv_dir, 'leads.csv')
            file_exists = os.path.isfile(csv_file)
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        'Timestamp', 'Reference ID', 'Product', 'Subtype',
                        'Email', 'Phone', 'Document Count', 'Source', 'Status', 'IP Address'
                    ])
                
                writer.writerow([
                    dump.created_at.isoformat(),
                    str(dump.id),
                    dump.product_type,
                    dump.product_subtype or '',
                    dump.user_email or '',
                    dump.user_phone or '',
                    dump.document_count,
                    dump.source,
                    dump.status,
                    dump.ip_address or ''
                ])
        except Exception as e:
            logger.warning(f"Failed to write CSV: {str(e)}")


class KycSpecStatsView(APIView):
    """Internal view to see dump statistics"""
    permission_classes = [AllowAny]  # Add proper permissions later
    
    def get(self, request):
        stats = {
            'total_dumps': KycSpecDump.objects.count(),
            'by_product': {
                'loan': KycSpecDump.objects.filter(product_type='loan').count(),
                'insurance': KycSpecDump.objects.filter(product_type='insurance').count(),
                'escrow': KycSpecDump.objects.filter(product_type='escrow').count(),
            },
            'today': KycSpecDump.objects.filter(
                created_at__date=datetime.now().date()
            ).count(),
            'unprocessed': KycSpecDump.objects.filter(status='collected').count(),
        }
        return Response(stats)


# Simple function-based view for backward compatibility
@csrf_exempt
@require_POST
def kyc_spec_collect_legacy(request):
    """Legacy endpoint for simple POST requests"""
    try:
        if request.body:
            data = json.loads(request.body)
        else:
            data = {}
    except:
        data = {}
    
    # Use the class-based view logic
    view = KycSpecCollectView()
    view.request = request
    return view.post(request)


# ========== NEW DASHBOARD & MANAGEMENT VIEWS ==========

class KycSpecDashboardView(APIView):
    """
    Dashboard to view KYC Spec submissions with filters
    For internal/admin use only
    """
    permission_classes = [AllowAny]  # TEMPORARY for testing
    
    def get(self, request):
        try:
            # Get query parameters
            product_type = request.GET.get('product')
            status_filter = request.GET.get('status')
            email = request.GET.get('email')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            search = request.GET.get('search', '')
            
            # Build queryset with filters
            queryset = KycSpecDump.objects.all()
            
            if product_type:
                queryset = queryset.filter(product_type=product_type)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            if email:
                queryset = queryset.filter(user_email__icontains=email)
            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)
            if search:
                queryset = queryset.filter(
                    Q(user_email__icontains=search) |
                    Q(user_phone__icontains=search) |
                    Q(product_subtype__icontains=search)
                )
            
            # Get counts for summary
            total_count = queryset.count()
            
            # Get counts by product
            product_counts = queryset.values('product_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Get counts by status
            status_counts = queryset.values('status').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Apply ordering and pagination
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 per page
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            paginated_queryset = queryset[start_idx:end_idx]
            
            # Prepare response data
            submissions = []
            for dump in paginated_queryset:
                submissions.append({
                    'id': str(dump.id),
                    'product_type': dump.product_type,
                    'product_subtype': dump.product_subtype or '',
                    'user_email': dump.user_email or '',
                    'user_phone': dump.user_phone or '',
                    'status': dump.status,
                    'document_count': dump.document_count,
                    'created_at': dump.created_at.isoformat(),
                    'updated_at': dump.updated_at.isoformat(),
                    'source': dump.source,
                    'has_documents': dump.document_count > 0,
                    'raw_data_keys': list(dump.raw_data.keys()) if dump.raw_data else []
                })
            
            # Calculate statistics
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            recent_stats = {
                'today': KycSpecDump.objects.filter(created_at__date=today).count(),
                'last_7_days': KycSpecDump.objects.filter(
                    created_at__date__gte=week_ago
                ).count(),
                'unprocessed': KycSpecDump.objects.filter(status='collected').count(),
            }
            
            return Response({
                'success': True,
                'summary': {
                    'total': total_count,
                    'by_product': {item['product_type']: item['count'] for item in product_counts},
                    'by_status': {item['status']: item['count'] for item in status_counts},
                    'recent': recent_stats,
                },
                'submissions': submissions,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size,
                    'total_items': total_count,
                    'has_next': end_idx < total_count,
                    'has_previous': page > 1,
                },
                'filters_applied': {
                    'product': product_type,
                    'status': status_filter,
                    'email_search': bool(email),
                    'date_range': {
                        'start': start_date,
                        'end': end_date
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KycSpecUpdateStatusView(APIView):
    """
    Update status of a KYC Spec submission
    """
    permission_classes = [AllowAny]  # TEMPORARY
    
    def patch(self, request, submission_id):
        try:
            # Find the submission
            try:
                submission = KycSpecDump.objects.get(id=submission_id)
            except KycSpecDump.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Submission {submission_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get update data
            data = request.data
            
            # Validate required fields
            if not any(key in data for key in ['status', 'notes']):
                return Response({
                    'success': False,
                    'error': "At least one of 'status' or 'notes' must be provided"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update fields
            if 'status' in data:
                valid_statuses = ['collected', 'processed', 'contacted', 'converted']
                if data['status'] not in valid_statuses:
                    return Response({
                        'success': False,
                        'error': f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                    }, status=status.HTTP_400_BAD_REQUEST)
                submission.status = data['status']
            
            if 'notes' in data:
                # Add notes to raw_data
                current_data = submission.raw_data or {}
                current_notes = current_data.get('admin_notes', [])
                if not isinstance(current_notes, list):
                    current_notes = []
                
                current_notes.append({
                    'note': data['notes'],
                    'updated_by': request.user.email if request.user.is_authenticated else 'system',
                    'timestamp': datetime.now().isoformat()
                })
                
                current_data['admin_notes'] = current_notes
                submission.raw_data = current_data
            
            # Update metadata
            submission.updated_at = datetime.now()
            
            if request.user.is_authenticated:
                current_data = submission.raw_data or {}
                current_data['last_updated_by'] = request.user.email
                submission.raw_data = current_data
            
            submission.save()
            
            return Response({
                'success': True,
                'message': f'Submission {submission_id} updated successfully',
                'data': {
                    'id': str(submission.id),
                    'product_type': submission.product_type,
                    'status': submission.status,
                    'updated_at': submission.updated_at.isoformat(),
                    'user_email': submission.user_email
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Update status error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class KycSpecExportView(APIView):
    """
    Export submissions as CSV
    """
    permission_classes = [AllowAny]  # TEMPORARY
    
    def get(self, request):
        try:
            # Get filter parameters
            product_type = request.GET.get('product')
            status_filter = request.GET.get('status')
            format_type = request.GET.get('format', 'csv')
            
            # Build queryset
            queryset = KycSpecDump.objects.all()
            
            if product_type:
                queryset = queryset.filter(product_type=product_type)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            queryset = queryset.order_by('-created_at')
            
            if format_type.lower() == 'csv':
                return self._export_csv(queryset)
            else:
                return self._export_json(queryset)
                
        except Exception as e:
            logger.error(f"Export error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _export_csv(self, queryset):
        """Export data as CSV file"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="kyc_spec_submissions.csv"'
        
        writer = csv.writer(response)
        
        # Write headers
        headers = [
            'ID', 'Product Type', 'Product Subtype', 'User Email', 
            'User Phone', 'Status', 'Document Count', 'Source',
            'Created At', 'Updated At', 'IP Address', 'Raw Data Keys'
        ]
        writer.writerow(headers)
        
        # Write data rows
        for submission in queryset:
            row = [
                str(submission.id),
                submission.product_type,
                submission.product_subtype or '',
                submission.user_email or '',
                submission.user_phone or '',
                submission.status,
                submission.document_count,
                submission.source,
                submission.created_at.isoformat(),
                submission.updated_at.isoformat(),
                submission.ip_address or '',
                ', '.join(submission.raw_data.keys()) if submission.raw_data else ''
            ]
            writer.writerow(row)
        
        return response
    
    def _export_json(self, queryset):
        """Export data as JSON"""
        data = []
        for submission in queryset:
            data.append({
                'id': str(submission.id),
                'product_type': submission.product_type,
                'product_subtype': submission.product_subtype,
                'user_email': submission.user_email,
                'user_phone': submission.user_phone,
                'status': submission.status,
                'document_count': submission.document_count,
                'source': submission.source,
                'created_at': submission.created_at.isoformat(),
                'updated_at': submission.updated_at.isoformat(),
                'ip_address': submission.ip_address,
                'raw_data': submission.raw_data
            })
        
        response = JsonResponse({'submissions': data}, safe=False)
        response['Content-Disposition'] = 'attachment; filename="kyc_spec_submissions.json"'
        return response


class KycSpecSearchView(APIView):
    """
    Search submissions with various criteria
    """
    permission_classes = [AllowAny]  # TEMPORARY
    
    def get(self, request):
        try:
            # Get search parameters
            query = request.GET.get('q', '').strip()
            if not query or len(query) < 2:
                return Response({
                    'success': False,
                    'error': 'Search query must be at least 2 characters'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Search in multiple fields
            queryset = KycSpecDump.objects.filter(
                Q(user_email__icontains=query) |
                Q(user_phone__icontains=query) |
                Q(product_subtype__icontains=query) |
                Q(product_type__icontains=query)
            ).order_by('-created_at')
            
            # Limit results
            limit = min(int(request.GET.get('limit', 50)), 100)
            queryset = queryset[:limit]
            
            # Prepare results
            results = []
            for submission in queryset:
                results.append({
                    'id': str(submission.id),
                    'product_type': submission.product_type,
                    'product_subtype': submission.product_subtype,
                    'user_email': submission.user_email,
                    'user_phone': submission.user_phone,
                    'status': submission.status,
                    'created_at': submission.created_at.isoformat(),
                    'match_fields': self._get_match_fields(submission, query)
                })
            
            return Response({
                'success': True,
                'query': query,
                'count': len(results),
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_match_fields(self, submission, query):
        """Determine which fields matched the search query"""
        matches = []
        query_lower = query.lower()
        
        if submission.user_email and query_lower in submission.user_email.lower():
            matches.append('email')
        if submission.user_phone and query_lower in submission.user_phone:
            matches.append('phone')
        if submission.product_subtype and query_lower in submission.product_subtype.lower():
            matches.append('product_subtype')
        if submission.product_type and query_lower in submission.product_type.lower():
            matches.append('product_type')
        
        return matches


# ========== SIMPLE FUNCTION VIEWS ==========

@api_view(['GET'])
@permission_classes([AllowAny])
def kyc_spec_summary(request):
    """Quick summary of KYC Spec submissions"""
    try:
        total = KycSpecDump.objects.count()
        today = datetime.now().date()
        
        stats = {
            'total_submissions': total,
            'today': KycSpecDump.objects.filter(created_at__date=today).count(),
            'by_product': {
                'loan': KycSpecDump.objects.filter(product_type='loan').count(),
                'insurance': KycSpecDump.objects.filter(product_type='insurance').count(),
                'escrow': KycSpecDump.objects.filter(product_type='escrow').count(),
            },
            'by_status': {
                'collected': KycSpecDump.objects.filter(status='collected').count(),
                'processed': KycSpecDump.objects.filter(status='processed').count(),
                'contacted': KycSpecDump.objects.filter(status='contacted').count(),
                'converted': KycSpecDump.objects.filter(status='converted').count(),
            }
        }
        
        return Response({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def kyc_spec_recent(request):
    """Get recent submissions (last 24 hours)"""
    try:
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        recent = KycSpecDump.objects.filter(
            created_at__gte=twenty_four_hours_ago
        ).order_by('-created_at')[:20]  # Last 20
        
        data = []
        for submission in recent:
            # Calculate time ago
            now = datetime.now(submission.created_at.tzinfo)
            diff = now - submission.created_at
            
            if diff.days > 0:
                time_ago = f"{diff.days}d ago"
            elif diff.seconds // 3600 > 0:
                time_ago = f"{diff.seconds // 3600}h ago"
            elif diff.seconds // 60 > 0:
                time_ago = f"{diff.seconds // 60}m ago"
            else:
                time_ago = "just now"
            
            data.append({
                'id': str(submission.id),
                'product_type': submission.product_type,
                'user_email': submission.user_email,
                'status': submission.status,
                'created_at': submission.created_at.isoformat(),
                'time_ago': time_ago
            })
        
        return Response({
            'success': True,
            'count': len(data),
            'recent_submissions': data
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
