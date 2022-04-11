from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError

""" 
Handy variables
# Important! #
# change VALID_COINS array, require to do custom migration step for update
# VendingUsers deposit(perhaps including default deposit value)
# also test for this functions are designed to work with this specific coins schema
"""
VALID_COINS = [5, 10, 20, 50, 100]
COIN_CAP = 10000  # How much of same coin can be hold
SINGLE_PURCHASE_MAX_QUANTITY = 999
VALID_COINS_STR = [str(x) for x in VALID_COINS]
DEFAULT_COINS_TAB = [0 for x in VALID_COINS]
# 2 for [ and ] str(COIN_CAP)) +2 for " ,"
# additional +2 for procaution
MAX_COIN_TAB_LEN = int(2 + len(VALID_COINS)*(len(str(COIN_CAP))+2)) + 2
# Validators


def validate_min_nominal(value):
    if value % VALID_COINS[0] != 0:
        raise ValidationError(
            '%(value)s is not multiples of %(min_nom)s!',
            params={'value': value, 'min_nom': str(VALID_COINS[0])},
        )


def validate_isSeller(value):
    # value hold seller id
    # let's check if user with that id has a seller role
    usr = value  # value should be VendingUserinstance, but if its number lets search for him!
    if isinstance(value, int):
        usr = VendingUser.objects.get(pk=value)
    if not isinstance(usr, VendingUser):
        raise ValidationError(
            '%(value)s is not Vending User!',
            params={'value': value},
        )
    if not usr:
        raise ValidationError(
            '%(value)s is bad user id',
            params={'value': value},
        )
    if not usr.is_seller():
        raise ValidationError(
            '%(value)s is not Seller!',
            params={'value': usr.user.username},
        )

# Models:

class Product(models.Model):

    def __str__(self):
        return "{}".format(self.productName)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    ammountAvailable = models.PositiveIntegerField()
    cost = models.PositiveIntegerField(validators=[validate_min_nominal])
    productName = models.CharField(max_length=50, null=False, blank=False,
                                   validators=[MinLengthValidator(3)], )
    sellerId = models.ForeignKey("vending_app.VendingUser",
                                 verbose_name="Seller",
                                 on_delete=models.SET_NULL,
                                 blank=False, null=True,
                                 validators=[validate_isSeller])
