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
        
def validate_coin_tab(value):
    """Validates wherher value is correct string representation of coin tab

    Args:
        value (string): hold string repr of tab ex. "[1,1,2,1,1]"

    Raises:
        ValidationError: With message whats wrong
    """
    params = {'value': value}
    #(sfm, ) = ('%(value)s is not multiples of 5!',)
    try:
        coin_tab = VendingUser.str_to_coinTab(value)   
        params['coin_tab'] = coin_tab
        if len(coin_tab) != len(VALID_COINS):
            raise Exception("%(coin_tab)s has bad size!")
        for idx in range(0,len(coin_tab)):
            if coin_tab[idx] < 0:
                raise Exception("Nominal %(value)s counter <0 ")
            if coin_tab[idx] >= COIN_CAP:
                raise Exception("Nominal %(value)s counter >COIN_CAP")
    except Exception as e:
         raise ValidationError(str(e),params=params)
     
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
class VendingUser(models.Model):
    """
        User model with username, password deposit and role fields
    """
    class Role(models.TextChoices):
        BUYER = 'b','Buyer'
        SELLER = 's','Seller'
    class Meta:
        verbose_name = 'VendingUser'
        verbose_name_plural = 'VendingUser'
    def __str__(self):
        return "{} is {}".format(self.user.username, VendingUser.Role(self.role).label)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    #deposit = models.PositiveIntegerField(default=0,validators=[validate_5])
    _deposit = models.CharField(default=str(DEFAULT_COINS_TAB[:]),validators=[validate_coin_tab],max_length=MAX_COIN_TAB_LEN)
    role = models.CharField(
        max_length=1,
        choices=Role.choices,
        default=Role.BUYER
    )
    @property
    def deposit(self):
        if self._deposit:
            return VendingUser.str_to_coinTab(self._deposit)
        return DEFAULT_COINS_TAB
        
    @deposit.setter
    def deposit(self,value):
        self._deposit = VendingUser.coinTab_to_str(value)
        
    def is_seller(self):
        return self.role == VendingUser.Role.SELLER
    def is_buyer(self):
        return self.role == VendingUser.Role.BUYER
    
    @classmethod
    def coinTab_to_str(cls,coin_tab):
        return str(coin_tab)
    @classmethod
    def str_to_coinTab(cls,coin_str: str):
        return [int(x) for x in str(coin_str)[1:-1].split(",")]
    @classmethod
    def coinTab_to_total(cls,coin_tab):
        total = 0
        tab = coin_tab[:]
        for idx in range(0,len(VALID_COINS)):
            total+=tab[idx]*VALID_COINS[idx]
        return total

    def reset_deposit(self,force_save=True):
        #default_value = VendingUser._meta.get_field('deposit').get_default()
        self.deposit = DEFAULT_COINS_TAB[:]
        if force_save:
            self.save()

    def total_deposit(self):
        return VendingUser.coinTab_to_total(self.deposit)

    def add_coin(self,coin,force_save=True):
        """
        Deposit coin to the buyer. 
        This function throws exception on errors!

        Args:
            coin int: Integer coin value
            force_save (bool, optional): Wheter perform save after add. Defaults to True.

        Raises:
            Exception: _description_
        """
        # additional check
        if not coin in VALID_COINS:
            raise Exception("Unresolved coin")
        if not isinstance(coin,int):
            raise Exception("Coin is not ingeger")
        if not self.is_buyer():
            raise Exception("User is not buyer")
        for idx in range(0,len(VALID_COINS)):
            if VALID_COINS[idx] == coin:
                tab = self.deposit
                tab[idx]+=1
                self.deposit = tab
        if force_save:
            self.save()
    def delete(self, *args, **kwargs):
        self.user.delete()
        return super(self.__class__, self).delete(*args, **kwargs)
    @classmethod
    def create_user(cls,username, password,email='any@email.com',
                role=Role.BUYER,deposit=None,**extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        if deposit is None:
            deposit = DEFAULT_COINS_TAB[:]
        elif isinstance(deposit,int):
            # Avoid cyclic import, and we can do so,
            # because this functions is designed for testing purpose
            from .coins import aquire
            deposit = aquire(deposit)
        
        user = User.objects.create_user(username=username,password=password,email=email,**extra_fields)
        vending_user = VendingUser(user=user, role=role, deposit=deposit)
        vending_user.save()
        
        return vending_user 
