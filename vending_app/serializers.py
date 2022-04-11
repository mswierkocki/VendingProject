from rest_framework import serializers
from .models import SINGLE_PURCHASE_MAX_QUANTITY, VendingUser, Product

from django.conf import settings
ALLOW_CHANGE_DEPOSIT = getattr(settings, "ALLOW_CHANGE_DEPOSIT", False)


class VendingUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')

    class Meta:
        model = VendingUser
        fields = ['id', 'username', 'role', 'deposit']

    def update(self, instance, validated_data):
        """Handle nested update"""
        if 'user' in validated_data:
            if 'username' in validated_data['user']:
                new_username = validated_data['user']['username']
                if instance.user.username != new_username:
                    instance.user.username = new_username
                    instance.user.save()
        return instance

    def to_representation(self, instance):
        """This function convert deposit coin tab to integer value

        Args:
            instance (VendingUser): Instance of VendingUser

        Returns:
            dict: Dict what holds instance values
        """
        data = super(VendingUserSerializer, self).to_representation(instance)
        coin_tab = VendingUser.str_to_coinTab(data['deposit'])
        deposit = VendingUser.coinTab_to_total(coin_tab)
        #del data['_deposit']
        data['deposit'] = deposit
        return data

    def to_internal_value(self, data):
        """This function is designed to handle deposit property,
         as we may get here "deposit" instead of "_deposit", so we need to 
         get deposit data from database.

        Args:
            data (dict): Internal data dict with object data

        Raises:
            serializers.ValidationError: On error


        Returns:
            _type_: _description_
        """
        sup_data = super(VendingUserSerializer, self).to_internal_value(data)
        if 'deposit' in data:
            try:
                try:
                    obj_id = data['id']
                    vuser = VendingUser.objects.get(pk=obj_id)
                    deposit = vuser.deposit
                    # if  ALLOW_CHANGE_DEPOSIT:
                    #     deposit = aquire(data['deposit'])
                    # else:
                    #   sup_data['deposit'] = deposit
                    sup_data['_deposit'] = deposit
                except KeyError:
                    raise serializers.ValidationError(
                        'id is a required field.'
                    )
                except ValueError:
                    raise serializers.ValidationError(
                        'id must be an integer.'
                    )
            except VendingUser.DoesNotExist:
                raise serializers.ValidationError(
                    'Such user does not exist.'
                )
        return sup_data


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = '__all__'


class CreateVendingUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        label="Username",
        write_only=True
    )
    password = serializers.CharField(
        label="Password",
        # This will be used when the DRF browsable API is enabled
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )

    class Meta:
        model = VendingUser
        fields = ['username', 'password', 'role']

class OrderSerializer(serializers.Serializer):
    productID = serializers.IntegerField(min_value=0)
    quantity = serializers.IntegerField(
        max_value=SINGLE_PURCHASE_MAX_QUANTITY, min_value=1)
