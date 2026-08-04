from django.urls import path
from . import views
from review.views import product_detail_view


app_name = 'store'

urlpatterns = [
    path('search/', views.search_view, name='search'),
    path('', views.home, name='home'),
    path(
        'product/<int:product_id>/',
        product_detail_view,
        name='product_detail',
    ),
    path('by_category/<int:category_id>', views.filter_by_category, name='filter_by_category'),
    path('random/', views.random_product, name='random_product')
]