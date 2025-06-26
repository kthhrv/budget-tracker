from django.contrib import admin
from django import forms
from .models import BudgetItem, MonthlyInstance


class MonthlyInstanceAdminForm(forms.ModelForm):
    """Custom form for MonthlyInstance admin to separate repeating and non-repeating items."""
    
    repeating_items = forms.ModelMultipleChoiceField(
        queryset=BudgetItem.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="These are automatically included repeating budget items for this month"
    )
    
    non_repeating_items = forms.ModelMultipleChoiceField(
        queryset=BudgetItem.objects.none(),
        widget=admin.widgets.FilteredSelectMultiple("Budget Items", is_stacked=False),
        required=False,
        help_text="Select additional non-repeating budget items to include in this month"
    )
    
    class Meta:
        model = MonthlyInstance
        fields = ['month', 'notes', 'repeating_items', 'non_repeating_items']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up the querysets for repeating and non-repeating items
        self.fields['repeating_items'].queryset = BudgetItem.objects.filter(repeats=True)
        self.fields['non_repeating_items'].queryset = BudgetItem.objects.filter(repeats=False)
        
        # If we have an instance, populate the fields with current selections
        if self.instance and self.instance.pk:
            current_items = self.instance.budget_items.all()
            repeating_current = current_items.filter(repeats=True)
            non_repeating_current = current_items.filter(repeats=False)
            
            # Set initial values for the fields
            if 'initial' not in kwargs:
                self.initial = {}
            self.initial['repeating_items'] = list(repeating_current)
            self.initial['non_repeating_items'] = list(non_repeating_current)
    
    def save(self, commit=True):
        instance = super().save(commit=commit)
        
        if commit:
            # Clear existing items and set the new ones
            selected_repeating = self.cleaned_data.get('repeating_items', [])
            selected_non_repeating = self.cleaned_data.get('non_repeating_items', [])
            
            # Combine both sets of items
            all_selected_items = list(selected_repeating) + list(selected_non_repeating)
            instance.budget_items.set(all_selected_items)
            
            # Recalculate total
            instance.calculate_total()
        
        return instance


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
    form = MonthlyInstanceAdminForm
    list_display = ['month', 'total_amount', 'created_at']
    list_filter = ['month', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    
    fieldsets = (
        ('Month Information', {
            'fields': ('month', 'notes')
        }),
        ('Repeating Budget Items', {
            'fields': ('repeating_items',),
            'description': 'These items are automatically included based on their repeating schedule.'
        }),
        ('Additional Budget Items', {
            'fields': ('non_repeating_items',),
            'description': 'Select additional non-repeating items to include in this month.'
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
