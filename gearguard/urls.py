"""
URL configuration for gearguard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include

# Import error handlers
from maintenance import error_handlers

urlpatterns = [
    path("", include("maintenance.urls")),
    path("admin/", admin.site.urls),  # Django admin - must come after maintenance URLs to avoid conflicts
]

# Custom error handlers - Django will use these for error responses
handler404 = error_handlers.handler404
handler500 = error_handlers.handler500
handler403 = error_handlers.handler403
handler400 = error_handlers.handler400
