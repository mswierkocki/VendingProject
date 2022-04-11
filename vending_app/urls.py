from django.conf.urls import url, include
from django.urls import path

from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views


app_name='vending'

router = routers.DefaultRouter()
router.register(r'users', views.UserViewset,basename='user')

urlpatterns = [
    path('user/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]