from django.contrib import admin
from .models import BudgetItem, MonthlyInstance


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'cost', 'repeats', 'startdate', 'end_date', 'created_at']
    list_filter = ['owner', 'repeats', 'created_at', 'startdate']
    search_fields = ['name', 'owner']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner')
        }),
        ('Financial Details', {
            'fields': ('cost', 'repeats')
        }),
        ('Date Information', {
            'fields': ('startdate', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MonthlyInstance)
class MonthlyInstanceAdmin(admin.ModelAdmin):
    list_display = ['month', 'total_amount', 'created_at']
    list_filter = ['month', 'created_at']
    filter_horizontal = ['budget_items']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    
    fieldsets = (
        ('Month Information', {
            'fields': ('month', 'notes')
        }),
        ('Budget Items', {
            'fields': ('budget_items',)
        }),
        ('Totals', {
            'fields': ('total_amount',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_total()
