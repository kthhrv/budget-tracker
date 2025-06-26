from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class BudgetItem(models.Model):
    """Model to store budget items like rent, insurance, etc."""
    
    name = models.CharField(
        max_length=200,
        help_text="Name of the budget item (e.g., rent, insurance)"
    )
    
    owner = models.CharField(
        max_length=100,
        help_text="Owner of this budget item"
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Amount for this budget item"
    )
    
    is_repeating = models.BooleanField(
        default=False,
        help_text="Whether this budget item repeats (e.g., monthly rent)"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional end date for this budget item"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget Item'
        verbose_name_plural = 'Budget Items'
    
    def __str__(self):
        return f"{self.name} - {self.owner} (${self.amount})"
