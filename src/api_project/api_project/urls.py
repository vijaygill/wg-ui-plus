"""
URL configuration for api_project project.

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
from django.urls import path, include
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from mcp_server.views import MCPServerStreamableHttpView

from api_app.mcp_configuration import MCPConfigurationService
from api_app.mcp_authentication import MCPTokenAuthentication


@method_decorator(csrf_exempt, name="dispatch")
class ConditionalMCPView(MCPServerStreamableHttpView):
    authentication_classes = [MCPTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        if not MCPConfigurationService.is_enabled():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api_app.urls')),
    path('mcp', ConditionalMCPView.as_view(), name='mcp_server_streamable_http_endpoint'),

]
