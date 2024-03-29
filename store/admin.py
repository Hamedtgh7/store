from typing import Any
from urllib.parse import urlencode
from django.contrib import admin, messages
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.db.models.aggregates import Count
from .models import Product, Collection, Customer, Order, OrderItem


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'products_count']
    search_fields = ['title']

    @admin.display(ordering='products_count')
    def products_count(self, collection: Collection):
        url = (
            reverse('admin:store_product_changelist')
            + '?'
            + urlencode({
                'collection_id': str(collection.id)
            }))
        return format_html('<a href="{}">{}</a>', url, collection.products_count)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).annotate(
            products_count=Count('products')
        )


class InventoryFilter(admin.SimpleListFilter):
    title = 'inventory'
    parameter_name = 'inventory'

    def lookups(self, request: Any, model_admin: Any) -> list[tuple[Any, str]]:
        return [
            ('<10', 'Low')
        ]

    def queryset(self, request: Any, queryset: QuerySet[Any]) -> QuerySet[Any] | None:
        if self.value() == '<10':
            return queryset.filter(inventory__lt=10)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {
        'slug': ['title']
    }
    autocomplete_fields = ['collection']
    search_fields = ['title']
    actions = ['clear_inventory']
    list_display = ['title', 'unit_price',
                    'inventory_status', 'collection_title']
    list_editable = ['unit_price']
    list_select_related = ['collection']
    list_filter = ['collection', 'last_update', InventoryFilter]
    list_per_page = 10

    def collection_title(self, product: Product):
        return product.collection.title

    @admin.display(ordering='inventory')
    def inventory_status(self, product: Product):
        if product.inventory < 10:
            return 'Low'
        return 'OK'

    @admin.action(description='Clear Inventory')
    def clear_inventory(self, request, quaryset: QuerySet):
        updated_count = quaryset.update(inventory=0)
        self.message_user(
            request,
            f'{updated_count} products were successfully updated.',
            messages.ERROR
        )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'membership', 'orders_count']
    list_editable = ['membership']
    list_per_page = 10
    list_select_related = ['user']
    ordering = ['user__first_name', 'user__last_name']
    search_fields = ['first_name__istartswith', 'last_name__istartswith']

    @admin.display(ordering='orders_count')
    def orders_count(self, customer: Customer):
        url = (
            reverse('admin:store_order_changelist')
            + '?'
            + urlencode({
                'customer_id': str(customer.id)
            }))
        return format_html('<a href="{}">{}</a>', url, customer.orders_count)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        return super().get_queryset(request).annotate(
            orders_count=Count('order')
        )


class OrderItemInline(admin.StackedInline):
    autocomplete_fields = ['product']
    model = OrderItem
    min_num = 1
    max_num = 10
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'placed_at', 'customer']
    inlines = [OrderItemInline]
    fields = ['payment_status', 'customer']
    autocomplete_fields = ['customer']
