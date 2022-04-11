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
    path('product/<int:pk>/',views.ProductDetail.as_view(),name='product'),
    url(r'^product/',views.product,name='product'),
    url(r'^deposit/',views.deposit,name='deposit'),
    url(r'^buy/',views.buy,name='buy'),
    url(r'^reset/',views.reset,name='reset'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]