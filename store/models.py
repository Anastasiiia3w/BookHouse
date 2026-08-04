from django.db import models
from django.core.validators import FileExtensionValidator

class Category(models.Model):
    name = models.CharField(max_length = 100, unique = True)
    description = models.TextField(max_length=500, blank = True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='subcategories', null=True, blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_children(self):
        return self.subcategories.all()

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    genre = models.CharField(max_length=100)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    author = models.CharField(max_length=200)
    main_image = models.ImageField(
        upload_to='products/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'webp']
            )
        ],
        help_text='Дозволені формати: JPG, JPEG, PNG, WebP',
        blank=True,
        null=True
    )
    is_featured = models.BooleanField(default=False)

    def get_average_rating(self):
        avg = self.rating.aggregate(models.Avg('rating'))['rating__avg']
        if avg:
            return round(avg, 1)
        else:
            return 0

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['name' ]

    def __str__(self):
        return self.name

class BookImage(models.Model):
    book = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(
        upload_to='images/',
        blank = True,
        null = True
    )
    alt_text = models.CharField(max_length=200, blank=True, null = True)

    def __str__(self):
        return f'Image of {self.book.name}'



