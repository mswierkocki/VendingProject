from django.contrib import admin

# Register your models here.
from .models import Product,VendingUser

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass
@admin.register(VendingUser)
class VendingUserAdmin(admin.ModelAdmin):
    pass