from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category
from cart.forms import CartAddProductForm
from django.views.generic import DetailView, ListView
import random
from .forms import SearchForm


from .cache import (
    get_cached_categories,
    get_cached_product,
    get_cached_products,
)



def home(request):
    featured_products = (Product.objects.filter(is_featured=True, is_available=True, stock__gt=0)
                         .select_related('category'))
    products = (Product.objects.filter(is_available = True, stock__gt = 0, is_featured = False)
                .select_related('category').all())

    categories = Category.objects.all()

    context = {
        'featured_products' : featured_products,
        'products' : products,
        'categories' : categories,
        'cart_product_form' : CartAddProductForm(),
    }

    return render(request, 'store/home.html', context)

def filter_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products_by_category = Product.objects.filter(
        is_available=True,
        stock__gt=0,
        category=category
    ).select_related('category')

    context = {
        'category' : category,
        'products' : products_by_category
    }

    return render(request, 'store/books_by_category.html', context)

# # окрема книга + історія переглядів
# def product_detail(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#
#
#
#     recently_viewed = request.session.get('recently_viewed', [])
#
#
#     if product_id in recently_viewed:
#         recently_viewed.remove(product_id)
#
#     recently_viewed.insert(0, product_id)
#
#     request.session['recently_viewed'] = recently_viewed[:10]
#
#     print('SESSION:', request.session.get('recently_viewed'))
#
#
#     context = {
#         'product' : product,
#         'cart_product_form' : CartAddProductForm(),
#
#     }
#
#
#     return render(request,'store/product_detail.html', context)


# Пошук
def search_view(request):
    search = request.GET.get('search', '').strip()

    products = Product.objects.select_related('category').all()

    if search:
        normalized_search = search.casefold()

        form = SearchForm(request.GET or None)



        products = [
            product
            for product in products
            if normalized_search in (product.name or '').casefold()
            or normalized_search in (product.description or '').casefold()
            or normalized_search in (product.author or '').casefold()
            or normalized_search in (product.genre or '').casefold()
            or (
                product.category
                and normalized_search in product.category.name.casefold()
            )
        ]

        if form.is_valid():
            sort_by = form.cleaned_data.get('sort_by')

            if sort_by:
                products = products.order_by(sort_by)

    return render(
        request,
        'store/search_results.html',
        {
            'products': products,
            'search': search,
            'form' : form,
        }
    )

class ProductListView(ListView):
    template_name = "store/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        self.query = self.request.GET.get(
            "q",
            "",
        ).strip()

        self.category_id = self.request.GET.get(
            "category",
            "",
        )

        self.sort = self.request.GET.get(
            "sort",
            "new",
        )

        return get_cached_products(
            query=self.query,
            category_id=self.category_id,
            sort=self.sort,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "categories": get_cached_categories(),
                "query": self.query,
                "selected_category": self.category_id,
                "sort": self.sort,
            }
        )

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = "store/product_detail.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        return get_cached_product(
            self.kwargs["pk"]
        )

# перенаправляє на сторінку випадкової книги
def random_product(request):
    product_ids = Product.objects.filter(is_available = True, stock__gt = 0).values_list('id', flat=True)

    if not product_ids:
        return redirect('store:home')

    random_id = random.choice(product_ids)

    return redirect('store:product_detail', product_id = random_id)

