from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date


class BudgetItem(models.Model):
    """
    Model for storing budget items like rent, insurance, and other expenses.
    """
    name = models.CharField(
        max_length=200,
        help_text="Name of the budget item (e.g., 'Monthly Rent', 'Car Insurance')"
    )
    owner = models.CharField(
        max_length=100,
        help_text="Owner of this budget item"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Monetary amount for the budget item (minimum $0.01)"
    )
    repeats = models.BooleanField(
        default=False,
        help_text="Whether this budget item repeats"
    )
    startdate = models.DateField(
        help_text="Start date for this budget item"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional end date for when this budget item should stop"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Budget Item"
        verbose_name_plural = "Budget Items"

    def __str__(self):
        return f"{self.name} - {self.owner} (${self.cost})"


class MonthlyInstance(models.Model):
    """
    Model for storing monthly budget instances with totals and item lists.
    """
    month = models.DateField(
        help_text="The month this instance represents (use first day of month)"
    )
    budget_items = models.ManyToManyField(
        BudgetItem,
        blank=True,
        help_text="Budget items included in this month"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount for all items in this month"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes for this monthly instance"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month']
        verbose_name = "Monthly Instance"
        verbose_name_plural = "Monthly Instances"
        unique_together = ['month']

    def __str__(self):
        return f"{self.month.strftime('%B %Y')} - Total: ${self.total_amount}"

    def calculate_total(self):
        """
        Calculate the total amount for all budget items in this month.
        """
        total = sum((item.cost for item in self.budget_items.all()), Decimal('0.00'))
        self.total_amount = total
        self.save()
        return total
    
    def auto_populate_repeating_items(self):
        """
        Auto-populate this monthly instance with active repeating budget items.
        
        Adds budget items that:
        - Have repeats=True
        - Have startdate <= this month
        - Have no end_date OR end_date >= this month (not expired)
        """
        # Get all repeating budget items that should be active for this month
        active_repeating_items = BudgetItem.objects.filter(
            repeats=True,
            startdate__lte=self.month
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=self.month)
        )
        
        # Add these items to this monthly instance
        self.budget_items.set(active_repeating_items)
        
        # Calculate the total amount for the auto-populated items
        self.calculate_total()
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-populate repeating items for new instances.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only auto-populate for new instances
        if is_new:
            self.auto_populate_repeating_items()
