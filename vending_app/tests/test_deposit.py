from django.test import Client, TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.models import User

from ..models import VendingUser


class DepositTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='buyer',
            email='buyer@buyer.pl', password='buyer'
        )
        self.buyer =  VendingUser.objects.create_user(
            username='buyer', password='buyer',email='buyer@buyer.pl',
             deposit=0,role=VendingUser.Role.BUYER)
        refresh = RefreshToken.for_user(self.user)
        self.token = refresh.access_token
        self.header = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
    
    def test_deposit_valid_coin(self):
        # get API response
        content={"coin":10}
        response = self.client.post(reverse('deposit'),content,content_type='application/json',**self.header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        user_response = self.client.get(reverse('user-detail',kwargs={"pk":self.user.pk}),content_type='application/json',**self.header)
        self.assertTrue(user_response.data['deposit'] == content['coin'])
        pass
