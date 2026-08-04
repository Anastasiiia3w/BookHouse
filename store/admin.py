from django.contrib import admin
from .models import *

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'author', 'price', 'genre', 'stock', 'is_available', 'is_featured', 'created_at',)
    search_fields = ('name', 'description', 'author', 'genre',)
    list_filter = ('category', 'genre', 'is_available', 'created_at','is_featured',)
    list_editable = ('price', 'stock', 'is_available', 'is_featured',)
    readonly_fields = ('created_at',)
    


