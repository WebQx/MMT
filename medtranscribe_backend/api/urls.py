"""
URL configuration for MMT API endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'patients', views.PatientViewSet)
router.register(r'encounters', views.EncounterViewSet)
router.register(r'transcriptions', views.TranscriptionViewSet)

app_name = 'api'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/user/', views.current_user_view, name='current_user'),
    
    # Health check
    path('health/', views.health_check, name='health_check'),
    
    # OpenEMR integration endpoints
    path('openemr/facilities/', views.openemr_facilities, name='openemr_facilities'),
    path('openemr/providers/', views.openemr_providers, name='openemr_providers'),
    
    # Include router URLs for viewsets
    path('', include(router.urls)),
]
