from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import BudgetItem


class BudgetItemTestCase(TestCase):
    def setUp(self):
        """Set up test data."""
        self.budget_item = BudgetItem.objects.create(
            name="Monthly Rent",
            owner="John Doe",
            amount=Decimal('1200.00'),
            is_repeating=True
        )
    
    def test_budget_item_creation(self):
        """Test that a budget item can be created with required fields."""
        self.assertEqual(self.budget_item.name, "Monthly Rent")
        self.assertEqual(self.budget_item.owner, "John Doe")
        self.assertEqual(self.budget_item.amount, Decimal('1200.00'))
        self.assertTrue(self.budget_item.is_repeating)
        self.assertIsNone(self.budget_item.end_date)
    
    def test_budget_item_str_representation(self):
        """Test the string representation of the budget item."""
        expected = "Monthly Rent - John Doe ($1200.00)"
        self.assertEqual(str(self.budget_item), expected)
    
    def test_budget_item_with_end_date(self):
        """Test budget item creation with an end date."""
        end_date = date(2024, 12, 31)
        insurance = BudgetItem.objects.create(
            name="Car Insurance",
            owner="Jane Smith",
            amount=Decimal('150.00'),
            is_repeating=True,
            end_date=end_date
        )
        self.assertEqual(insurance.end_date, end_date)
    
    def test_non_repeating_budget_item(self):
        """Test creation of a non-repeating budget item."""
        one_time = BudgetItem.objects.create(
            name="Home Repair",
            owner="Bob Wilson",
            amount=Decimal('500.00'),
            is_repeating=False
        )
        self.assertFalse(one_time.is_repeating)
    
    def test_budget_item_ordering(self):
        """Test that budget items are ordered by creation date (newest first)."""
        newer_item = BudgetItem.objects.create(
            name="Groceries",
            owner="Alice Brown",
            amount=Decimal('200.00')
        )
        
        items = list(BudgetItem.objects.all())
        self.assertEqual(items[0], newer_item)
        self.assertEqual(items[1], self.budget_item)
