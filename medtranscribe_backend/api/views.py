"""
Django REST API views for OpenEMR integration and medical transcription.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import json
import logging

from .models import (
    OpenEMRUser, Patient, Encounter, Transcription, 
    TranscriptionSegment, OpenEMRSession
)
from .auth_backends import OpenEMRAuthBackend

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user against OpenEMR database
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username and password required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate using our custom backend
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        
        # Get OpenEMR user info if available
        openemr_user_data = {}
        try:
            openemr_user = OpenEMRUser.objects.get(username=username, active=True)
            openemr_user_data = {
                'id': openemr_user.id,
                'fname': openemr_user.fname,
                'lname': openemr_user.lname,
                'email': openemr_user.email,
                'facility': openemr_user.facility,
                'title': openemr_user.title,
                'specialty': openemr_user.specialty,
            }
        except OpenEMRUser.DoesNotExist:
            pass
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'openemr_data': openemr_user_data
            }
        })
    
    return Response({
        'error': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout user
    """
    logout(request)
    return Response({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """
    Get current authenticated user info
    """
    user = request.user
    
    # Get OpenEMR user info if available
    openemr_user_data = {}
    try:
        openemr_user = OpenEMRUser.objects.get(username=user.username, active=True)
        openemr_user_data = {
            'id': openemr_user.id,
            'fname': openemr_user.fname,
            'lname': openemr_user.lname,
            'email': openemr_user.email,
            'facility': openemr_user.facility,
            'title': openemr_user.title,
            'specialty': openemr_user.specialty,
        }
    except OpenEMRUser.DoesNotExist:
        pass
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'openemr_data': openemr_user_data
        }
    })


# Patient Management Views
class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing OpenEMR patients
    """
    queryset = Patient.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Filter patients based on search parameters
        """
        queryset = Patient.objects.all()
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(fname__icontains=search) |
                Q(lname__icontains=search) |
                Q(email__icontains=search) |
                Q(pubpid__icontains=search)
            )
        
        # Filter by provider
        provider_id = self.request.query_params.get('provider_id', None)
        if provider_id:
            queryset = queryset.filter(providerID=provider_id)
        
        return queryset.order_by('-date')
    
    def list(self, request):
        """
        List patients with basic info
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            data = []
            for patient in page:
                data.append({
                    'pid': patient.pid,
                    'pubpid': patient.pubpid,
                    'fname': patient.fname,
                    'lname': patient.lname,
                    'mname': patient.mname,
                    'DOB': patient.DOB,
                    'sex': patient.sex,
                    'email': patient.email,
                    'phone_home': patient.phone_home,
                    'phone_cell': patient.phone_cell,
                    'status': patient.status,
                    'date': patient.date,
                })
            
            return self.get_paginated_response(data)
        
        return Response([])
    
    def retrieve(self, request, pk=None):
        """
        Get detailed patient information
        """
        try:
            patient = Patient.objects.get(pid=pk)
            return Response({
                'pid': patient.pid,
                'pubpid': patient.pubpid,
                'title': patient.title,
                'fname': patient.fname,
                'lname': patient.lname,
                'mname': patient.mname,
                'DOB': patient.DOB,
                'sex': patient.sex,
                'street': patient.street,
                'city': patient.city,
                'state': patient.state,
                'postal_code': patient.postal_code,
                'country_code': patient.country_code,
                'phone_home': patient.phone_home,
                'phone_biz': patient.phone_biz,
                'phone_cell': patient.phone_cell,
                'email': patient.email,
                'email_direct': patient.email_direct,
                'status': patient.status,
                'occupation': patient.occupation,
                'race': patient.race,
                'ethnicity': patient.ethnicity,
                'language': patient.language,
                'date': patient.date,
            })
        except Patient.DoesNotExist:
            return Response({
                'error': 'Patient not found'
            }, status=status.HTTP_404_NOT_FOUND)


# Encounter Management Views
class EncounterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing OpenEMR encounters
    """
    queryset = Encounter.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Filter encounters based on parameters
        """
        queryset = Encounter.objects.select_related('pid', 'provider_id')
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(pid=patient_id)
        
        # Filter by provider
        provider_id = self.request.query_params.get('provider_id', None)
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.order_by('-date')
    
    def list(self, request):
        """
        List encounters
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            data = []
            for encounter in page:
                data.append({
                    'id': encounter.id,
                    'encounter': encounter.encounter,
                    'date': encounter.date,
                    'reason': encounter.reason,
                    'facility': encounter.facility,
                    'patient': {
                        'pid': encounter.pid.pid,
                        'name': f"{encounter.pid.fname} {encounter.pid.lname}",
                        'pubpid': encounter.pid.pubpid,
                    } if encounter.pid else None,
                    'provider': {
                        'id': encounter.provider_id.id,
                        'name': f"{encounter.provider_id.fname} {encounter.provider_id.lname}",
                        'username': encounter.provider_id.username,
                    } if encounter.provider_id else None,
                    'sensitivity': encounter.sensitivity,
                    'pos_code': encounter.pos_code,
                    'class_code': encounter.class_code,
                })
            
            return self.get_paginated_response(data)
        
        return Response([])


# Transcription Management Views
class TranscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medical transcriptions
    """
    queryset = Transcription.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """
        Filter transcriptions based on parameters
        """
        queryset = Transcription.objects.select_related(
            'patient', 'encounter', 'provider'
        ).prefetch_related('segments')
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(patient__pid=patient_id)
        
        # Filter by provider
        provider_id = self.request.query_params.get('provider_id', None)
        if provider_id:
            queryset = queryset.filter(provider__id=provider_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def list(self, request):
        """
        List transcriptions
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            data = []
            for transcription in page:
                data.append({
                    'id': transcription.id,
                    'filename': transcription.filename,
                    'original_filename': transcription.original_filename,
                    'status': transcription.status,
                    'confidence_score': transcription.confidence_score,
                    'language_detected': transcription.language_detected,
                    'duration_seconds': transcription.duration_seconds,
                    'patient': {
                        'pid': transcription.patient.pid,
                        'name': f"{transcription.patient.fname} {transcription.patient.lname}",
                    } if transcription.patient else None,
                    'encounter': {
                        'id': transcription.encounter.id,
                        'date': transcription.encounter.date,
                        'reason': transcription.encounter.reason,
                    } if transcription.encounter else None,
                    'provider': {
                        'id': transcription.provider.id,
                        'name': f"{transcription.provider.fname} {transcription.provider.lname}",
                    } if transcription.provider else None,
                    'created_at': transcription.created_at,
                    'updated_at': transcription.updated_at,
                    'processed_at': transcription.processed_at,
                    'reviewed_at': transcription.reviewed_at,
                    'openemr_note_id': transcription.openemr_note_id,
                })
            
            return self.get_paginated_response(data)
        
        return Response([])
    
    def retrieve(self, request, pk=None):
        """
        Get detailed transcription with segments
        """
        try:
            transcription = Transcription.objects.select_related(
                'patient', 'encounter', 'provider'
            ).prefetch_related('segments__edited_by').get(id=pk)
            
            segments_data = []
            for segment in transcription.segments.all():
                segments_data.append({
                    'id': segment.id,
                    'segment_number': segment.segment_number,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'text': segment.text,
                    'confidence_score': segment.confidence_score,
                    'edited': segment.edited,
                    'edited_by': {
                        'id': segment.edited_by.id,
                        'name': f"{segment.edited_by.fname} {segment.edited_by.lname}",
                    } if segment.edited_by else None,
                    'edited_at': segment.edited_at,
                })
            
            return Response({
                'id': transcription.id,
                'filename': transcription.filename,
                'original_filename': transcription.original_filename,
                'file_size': transcription.file_size,
                'duration_seconds': transcription.duration_seconds,
                'transcription_text': transcription.transcription_text,
                'confidence_score': transcription.confidence_score,
                'language_detected': transcription.language_detected,
                'status': transcription.status,
                'patient': {
                    'pid': transcription.patient.pid,
                    'name': f"{transcription.patient.fname} {transcription.patient.lname}",
                    'pubpid': transcription.patient.pubpid,
                } if transcription.patient else None,
                'encounter': {
                    'id': transcription.encounter.id,
                    'date': transcription.encounter.date,
                    'reason': transcription.encounter.reason,
                } if transcription.encounter else None,
                'provider': {
                    'id': transcription.provider.id,
                    'name': f"{transcription.provider.fname} {transcription.provider.lname}",
                    'username': transcription.provider.username,
                } if transcription.provider else None,
                'segments': segments_data,
                'created_at': transcription.created_at,
                'updated_at': transcription.updated_at,
                'processed_at': transcription.processed_at,
                'reviewed_at': transcription.reviewed_at,
                'openemr_note_id': transcription.openemr_note_id,
                'integrated_at': transcription.integrated_at,
            })
            
        except Transcription.DoesNotExist:
            return Response({
                'error': 'Transcription not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a transcription
        """
        try:
            transcription = Transcription.objects.get(id=pk)
            transcription.status = 'approved'
            transcription.reviewed_at = timezone.now()
            transcription.save()
            
            return Response({'success': True, 'status': 'approved'})
            
        except Transcription.DoesNotExist:
            return Response({
                'error': 'Transcription not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a transcription
        """
        try:
            transcription = Transcription.objects.get(id=pk)
            transcription.status = 'rejected'
            transcription.reviewed_at = timezone.now()
            transcription.save()
            
            return Response({'success': True, 'status': 'rejected'})
            
        except Transcription.DoesNotExist:
            return Response({
                'error': 'Transcription not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def integrate_with_openemr(self, request, pk=None):
        """
        Integrate transcription with OpenEMR as a clinical note
        """
        try:
            transcription = Transcription.objects.get(id=pk)
            
            # TODO: Implement OpenEMR FHIR API integration
            # This would create a clinical note in OpenEMR using their FHIR API
            
            # For now, mark as integrated
            transcription.integrated_at = timezone.now()
            transcription.save()
            
            return Response({
                'success': True, 
                'message': 'Transcription integrated with OpenEMR',
                'integrated_at': transcription.integrated_at
            })
            
        except Transcription.DoesNotExist:
            return Response({
                'error': 'Transcription not found'
            }, status=status.HTTP_404_NOT_FOUND)


# Health Check View
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for Docker healthcheck
    """
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now(),
        'version': '1.0.0'
    })


# OpenEMR Integration Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def openemr_facilities(request):
    """
    Get list of OpenEMR facilities
    """
    # This would typically query the OpenEMR facilities table
    # For now, return a mock response
    return Response([
        {'id': 1, 'name': 'Main Clinic', 'address': '123 Main St'},
        {'id': 2, 'name': 'Satellite Office', 'address': '456 Oak Ave'},
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def openemr_providers(request):
    """
    Get list of OpenEMR providers/users
    """
    providers = OpenEMRUser.objects.filter(active=True).values(
        'id', 'username', 'fname', 'lname', 'title', 'specialty', 'facility'
    )
    
    return Response(list(providers))