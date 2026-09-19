from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.views.static import serve as static_serve
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from store import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Main pages
    path('', TemplateView.as_view(template_name='index.html'), name='calendar'),
    path('admin-panel/', views.admin_panel, name='admin-panel'),
    
    # API endpoints
    path('api/calendar/bootstrap/', views.bootstrap, name='bootstrap'),
    path('api/calendar/month/', views.calendar_month, name='calendar_month'),
    path('api/calendar/data/<str:kind>/', views.data_api, name='data_api'),
    path('api/calendar/import/<str:kind>/', views.import_csv, name='import_csv'),
    path('api/calendar/export/<str:kind>/', views.export_csv, name='export_csv'),
    path('api/calendar/upload-image/', views.upload_image, name='upload_image'),
]

# ============================================================
# ✅ MEDIA FILES SERVE — Production-এও কাজ করবে
# (DEBUG setting পুরোপুরি ignore করে)
# ============================================================
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

# ============================================================
# STATIC FILES SERVE — শুধু development-এ
# (Production-এ Whitenoise serve করবে)
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)