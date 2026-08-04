import hashlib
import json

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.http import Http404

from .models import Category, Product

CATALOG_VERSION_KEY = "store:catalog:version"

def get_catalog_version():
    version = cache.get(CATALOG_VERSION_KEY)

    if version is None:
        cache.add(
            CATALOG_VERSION_KEY,
            1,
            timeout=None,
        )

        version = cache.get(CATALOG_VERSION_KEY)

    return version or 1

def invalidate_catalog_cache():
    if cache.get(CATALOG_VERSION_KEY) is None:
        cache.set(
            CATALOG_VERSION_KEY,
            2,
            timeout=None,
        )
        return

    try:
        cache.incr(CATALOG_VERSION_KEY)
    except ValueError:
        cache.set(
            CATALOG_VERSION_KEY,
            2,
            timeout=None,
        )

def get_cached_categories():
    version = get_catalog_version()
    key = f"store:catalog:version:{version}"

    categories = cache.get(key)

    if categories is None:
        categories = list(
            Category.objects.only(
                "id",
                "name",
                "description",
            ).order_by("name")
        )

        cache.set(
            key,
            categories,
            timeout=settings.CACHE_TTL,
        )
    return categories

def get_cached_products(
        *,
        query="",
        category_id="",
        sort="new",
):
    version = get_catalog_version()

    payload = {
        "query": query,
        "category_id": category_id,
        "sort": sort,
    }

    serialized_payload = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
    )

    digest = hashlib.sha256(
        serialized_payload.encode("utf-8")
    ).hexdigest()[:20]

    key = f"store:catalog:version:{version}:{digest}"

    products = cache.get(key)

    if products is not None:
        return products

    queryset = Product.objects.filter(
        is_available=True,
    ).select_related(
        "category",
    )

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category_id__icontains=query)
        )

    if str(category_id).isdigit():
        queryset = queryset.filter(
            category_id = category_id,
        )

    ordering = {
        "new": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "name": "name",
    }

    queryset = queryset.order_by(
        ordering.get(sort, "-created_at"),
    )

    products = list(queryset)

    cache.set(
        key,
        products,
        timeout=settings.CACHE_TTL,
    )

    return products

def get_cached_product(product_id):
    version = get_catalog_version()
    key = f"store:catalog:version:{version}:{product_id}"

    product = cache.get(key)

    if product is not None:
        return product

    try:
        product = (
            Product.objects
            .select_related("category")
            .get(
                pk=product_id,
                is_available=True,
            )
        )
    except Product.DoesNotExist as error:
        raise Http404("Товар не знайдено") from error

    cache.set(
        key,
        product,
        timeout=settings.CACHE_TTL,
    )

    return product