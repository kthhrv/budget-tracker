from django.contrib import admin
from .models import BudgetItem


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'amount', 'is_repeating', 'end_date', 'created_at')
    list_filter = ('is_repeating', 'owner', 'created_at')
    search_fields = ('name', 'owner')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'owner', 'amount')
        }),
        ('Options', {
            'fields': ('is_repeating', 'end_date'),
            'description': 'Configure repeating behavior and end date for this budget item'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
