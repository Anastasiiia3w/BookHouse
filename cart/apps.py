from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'cart'

    # імпорт сигналів
    def ready(self):
        import cart.signals