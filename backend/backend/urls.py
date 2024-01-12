"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from knox import views as knox_views

from api import views

admin.site.site_header = 'Keba Wallbox Admin Panel'
admin.site.site_title = 'Wallbox Admin'

# router = routers.DefaultRouter()
# router.register(r'charge_sessions/list/', views.ChargeSessionList.as_view())

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/', include(router.urls)),
    path('api/charge_sessions/list/', views.ChargeSessionList.as_view(), name='knox_login'),
    path('api/login/', views.LoginView.as_view()),
    path('api/logout/', knox_views.LogoutView.as_view(), name='knox_logout'),
    path('api/logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),
]

# urlpatterns += router.urls

# urlpatterns = format_suffix_patterns(urlpatterns)
