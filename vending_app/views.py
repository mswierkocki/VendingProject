from django.db import transaction, IntegrityError
from django.conf import settings
from django.core.validators import ValidationError
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.http import Http404,HttpResponse

from rest_framework import viewsets,status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS,AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import VendingUser,Product, VALID_COINS,VALID_COINS_STR
from .serializers import VendingUserSerializer,CreateVendingUserSerializer,ProductSerializer,OrderSerializer
from .coins import pay,aquire

ALLOW_CHANGE_DEPOSIT = getattr(settings, "ALLOW_CHANGE_DEPOSIT", False)


# Permissions:

class AllowGET(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS # or just ["GET"]
class AllowPOST(BasePermission):
    def has_permission(self, request, view):
        return request.method in ["POST"]
class AllowBUYER(BasePermission):
    def has_permission(self, request, view):
        if hasattr(request.user,'vendinguser'):
            return request.user.vendinguser.is_buyer()
        return False

# Views:   
class UserViewset(viewsets.ModelViewSet):
    """View Set Class designed for CRUD for /user"""
    permission_classes = [IsAuthenticated|AllowPOST]
    queryset = VendingUser.objects.all()
    serializer_class = VendingUserSerializer
   
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateVendingUserSerializer
        return VendingUserSerializer

    def create(self,request,*args,**kwargs):
        user_data = request.data
        serializer = CreateVendingUserSerializer(data=user_data)
        #if request user is not seller, then role is forced to be buyer
        serializer.role=VendingUser.Role.BUYER
        if request.user:
            if hasattr(request.user,'vendinguser'):
                if request.user.vendinguser.is_seller():
                    if user_data['role'] == VendingUser.Role.SELLER:
                      serializer.role = VendingUser.Role.SELLER
        if serializer.is_valid():
            # I could use serializer.save() but it lacks of transactions and handle nested object functionality
            uname = serializer.validated_data['username']
            password = serializer.validated_data['password']
            try:
                with transaction.atomic():
                    usr = User.objects.create_user(
                        username=uname, email='any@email.com', password=password)
                    vuser = VendingUser.objects.create(user = usr, role=serializer.role)
                    vuser.save()
                    user_serializer = VendingUserSerializer(instance=vuser)
                return Response(user_serializer.data,status=status.HTTP_200_OK)
            except Exception:
                return Response({"message":"Cannot register with such credentials"},status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
     
    def update(self, request, pk=None,*args,**kwargs):
        # since we dont use nested serializer library, and our user need aditional checks we perform update manualy
        partial = kwargs.pop('partial', False)
        #instance = VendingUser.objects.filter(pk=pk).first()
        instance = self.get_object()
        #disallow update users others than yourself
        if request.user != instance.user:
            return Response({"message":"You can only edit Yourself!"},status=status.HTTP_400_BAD_REQUEST)
        if str(instance.pk) != pk:
            return Response({"message":"Cannot update ID!"},status=status.HTTP_400_BAD_REQUEST)
        if partial and 'deposit' in request.data and not 'id' in request.data:
            request.data['id'] = pk
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            with transaction.atomic():
                serializer.is_valid(raise_exception=True)
                obj = serializer.save()
                changed = False
                total_deposit = obj.total_deposit
                if 'deposit' in request.data and ALLOW_CHANGE_DEPOSIT:
                    new_deposit = int(request.data['deposit'])
                    if total_deposit != new_deposit:
                        obj.deposit = aquire(new_deposit)
                        changed = True
                if 'role' in request.data:
                    #Update role means only seller can become buyer
                    new_role = request.data['role']
                    if new_role != obj.role:
                        if new_role ==VendingUser.Role.BUYER: # this means seller is now buyer, must update products
                            obj.role=new_role
                            changed = True
                            Product.objects.filter(sellerId=obj).update(sellerId=None)
                        else:
                            raise ValidationError("Only seller can downgrade it's role to buyer!")
                if changed:
                    obj.save()
                serializer = self.get_serializer(obj)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if request.user != instance.user.user:
                return Response({'details':"You are not allowed to do so!"}, status=status.HTTP_400_BAD_REQUEST)
            self.perform_destroy(instance)
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ProductDetail(APIView):
    """
    Retrieve, update or delete a Product instance.
    """
    permission_classes = [IsAuthenticated|AllowGET]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    allowed_methods = ['put','get','delete']
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise Http404
    
    @classmethod
    def check_owner(cls,request,product):
        if product.sellerId.user.pk is not request.user.pk:
                return False, Response({"message":"You are not the owner"},status=status.HTTP_403_FORBIDDEN)
        return True, None
    
    def get(self, request, pk, format=None):
        product = self.get_object(pk)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk, partial=False, format=None):
        product = self.get_object(pk)
        #checking wheter we are owner user by User id
        is_owner, ret = ProductDetail.check_owner(request,product)
        if not is_owner:
            return ret
        data=request.data
        #Allow Product ownership transfer
        data["sellerId"]=int(request.data.get('sellerId')) if "sellerId" in request.data.keys() else product.sellerId.pk
            
        serializer = ProductSerializer(product, data=request.data,partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, pk, format=None):
        return self.put(request,pk,True,format)
    def delete(self, request, pk, format=None):
        product = self.get_object(pk)
        is_owner, ret = ProductDetail.check_owner(request,product)
        if not is_owner:
            return ret
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
       
@api_view(['GET','POST'])
@permission_classes([AllowAny])
def product(request):
    """ 
    Get all products

    get: List all products.
    post: Create a new product.

    """
    # get all products
    if request.method == 'GET':
        try:
            products = Product.objects.all()
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    # Create new        
    elif request.method == 'POST':
        if not request.user or request.user.is_anonymous:
            return Response({"message":
                            "Unautorized"},
                            status=status.HTTP_401_UNAUTHORIZED)
        if not hasattr(request.user, 'vendinguser'):
            return Response({"message":
                            "User {} is not VendingUser".format(request.user.username)},
                            status=status.HTTP_403_FORBIDDEN)
        vuser = request.user.vendinguser
        if not vuser.is_seller():
            return Response({"message":
                            "User {} is not seller".format(vuser.user.username)},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        try:
            data = {
                'ammountAvailable': request.data.get('ammountAvailable'),
                'cost': int(request.data.get('cost')),
                'productName': request.data.get('productName'),
                'sellerId': vuser.pk,
            }
            serializer = ProductSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"description":"Bad data or content type, expected JSON with 'ammountAvailable','cost','productName'"},status=status.HTTP_400_BAD_REQUEST)    

    return Response({}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET', 'POST'])
@permission_classes([AllowBUYER])
def deposit(request):
    coin = request.data.get("coin")
    if coin is None: # check in querry data
        coin = request.query_params.get('coin')
        if coin is None:
            return Response({"description":"Could not find coin in data"}, status=status.HTTP_400_BAD_REQUEST)            
    try:
        if isinstance(coin,str):
            if coin in VALID_COINS_STR:    
                coin = int(coin) # change it to int, it should no throw, because VALID tab contains int's
        if isinstance(coin,int):
            if coin not in VALID_COINS:
                raise Exception("Invalid Coin")
            #since we know here our user is buyer and coin is in int format:
            vuser = request.user.vendinguser
            with transaction.atomic():
                usr = VendingUser.objects.select_for_update().get(pk=vuser.pk)
                usr.add_coin(coin,force_save=False)
                usr.save()
    except Exception as e:
        return Response({"description":str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({}, status=status.HTTP_204_NO_CONTENT)
@api_view(['GET', 'POST'])
@permission_classes([AllowBUYER])
def reset(request):
    vuser = request.user.vendinguser
    with transaction.atomic():
        usr = VendingUser.objects.select_for_update().get(pk=vuser.pk)
        usr.reset_deposit()
        usr.save()
    # we must take user from db id order to get current values.    
    serializer = VendingUserSerializer(VendingUser.objects.get(pk=vuser.pk))
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([AllowBUYER])
def buy(request):
    data = request.data
    if data is None: # check for query params
        data = request.query_params
    serializer = OrderSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #check avaiable
    productID = serializer.data['productID']
    product = Product.objects.filter(pk=productID).first()
    if product is None:
        return Response({"message":"Invalid product id!"}, status=status.HTTP_400_BAD_REQUEST)
    quantity = serializer.data['quantity']
    if product.ammountAvailable < quantity:
        return Response({"message":"Insufficient product quantity!"}, status=status.HTTP_400_BAD_REQUEST)
    #for currency we should using specialized class with fixed decimal places, however we use here simple ints
    order_cost = product.cost * quantity
    #since cost is assured to be divisable buy 5's so order cos is also
    assert order_cost % VALID_COINS[0] == 0
    #quick check if buyer has funds
    funds = request.user.vendinguser.total_deposit()
    if funds<order_cost:
        return Response({"message":"Insufficient funds!"}, status=status.HTTP_400_BAD_REQUEST)
    new_deposit = request.user.vendinguser.deposit[:]
    if pay(new_deposit,order_cost) != 0:
        return Response({"message":"Insufficient funds!"}, status=status.HTTP_400_BAD_REQUEST)
    #since product is avaiable and user has funds we may now perform buy operation
    try:
      with transaction.atomic():
        usr = VendingUser.objects.select_for_update().get(pk=request.user.vendinguser.pk)
        #check deposit is same here, if not rise
        #we update daposit table only if it has not change sice beggining of this request
        prod = Product.objects.select_for_update().get(pk=productID)
        if prod.ammountAvailable != product.ammountAvailable:
            raise IntegrityError("Ammount has changed")
        if usr.deposit != request.user.vendinguser.deposit:
            raise IntegrityError("deposit has changed")
        usr.deposit = new_deposit
        usr.save()
        prod.ammountAvailable -= quantity
        prod.save()
    except Exception as e:
        return Response({},status=status.HTTP_412_PRECONDITION_FAILED)    
    return Response({'total':order_cost,'change':new_deposit})

def logout_all(request):
# grab the user in question 
    #user = User.objects.get(username='johndoe')
    html = '<html><body>{"message":"User is not logged in"}</body></html>'
    user = request.user
    found = False
    if user.is_authenticated:
        for s in Session.objects.all():
            deco =s.get_decoded()
            if deco.get('_auth_user_id') == str(user.id): 
                found = True
                s.delete()
    else:
        return HttpResponse(html)
        # [s.delete() for s in Session.objects.all() if s.get_decoded().get('_auth_user_id') == user.id] 
    if found:
       html = '<html><body>{"message":"Logout all succesfull!"}</body></html>' 
    else:
        html = '<html><body>{"message":"Could not find session"}</body></html>' 
        
    return HttpResponse(html)
