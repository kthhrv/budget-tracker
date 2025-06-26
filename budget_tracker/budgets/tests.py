from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from .models import BudgetItem, MonthlyInstance


class BudgetItemModelTest(TestCase):
    
    def setUp(self):
        self.valid_data = {
            'name': 'Monthly Rent',
            'owner': 'John Doe',
            'cost': Decimal('1200.00'),
            'repeats': True,
            'startdate': date.today()
        }
    
    def test_budget_item_creation(self):
        """Test basic budget item creation"""
        item = BudgetItem.objects.create(**self.valid_data)
        self.assertEqual(item.name, 'Monthly Rent')
        self.assertEqual(item.owner, 'John Doe')
        self.assertEqual(item.cost, Decimal('1200.00'))
        self.assertTrue(item.repeats)
        self.assertEqual(item.startdate, date.today())
        self.assertIsNone(item.end_date)
    
    def test_budget_item_string_representation(self):
        """Test the string representation of budget item"""
        item = BudgetItem.objects.create(**self.valid_data)
        expected = f"Monthly Rent - John Doe ($1200.00)"
        self.assertEqual(str(item), expected)
    
    def test_budget_item_with_end_date(self):
        """Test budget item with end date"""
        end_date = date.today() + timedelta(days=365)
        self.valid_data['end_date'] = end_date
        item = BudgetItem.objects.create(**self.valid_data)
        self.assertEqual(item.end_date, end_date)
    
    def test_cost_validation(self):
        """Test cost validation (minimum $0.01)"""
        self.valid_data['cost'] = Decimal('0.00')
        item = BudgetItem(**self.valid_data)
        with self.assertRaises(ValidationError):
            item.full_clean()


class MonthlyInstanceModelTest(TestCase):
    
    def setUp(self):
        self.month = date(2024, 1, 1)
        self.budget_item1 = BudgetItem.objects.create(
            name='Rent',
            owner='John',
            cost=Decimal('1200.00'),
            repeats=True,
            startdate=date.today()
        )
        self.budget_item2 = BudgetItem.objects.create(
            name='Insurance',
            owner='Jane',
            cost=Decimal('150.00'),
            repeats=True,
            startdate=date.today()
        )
    
    def test_monthly_instance_creation(self):
        """Test basic monthly instance creation"""
        instance = MonthlyInstance.objects.create(month=self.month)
        self.assertEqual(instance.month, self.month)
        self.assertEqual(instance.total_amount, Decimal('0.00'))
    
    def test_monthly_instance_string_representation(self):
        """Test the string representation of monthly instance"""
        instance = MonthlyInstance.objects.create(month=self.month)
        expected = "January 2024 - Total: $0.00"
        self.assertEqual(str(instance), expected)
    
    def test_monthly_instance_with_budget_items(self):
        """Test monthly instance with budget items"""
        instance = MonthlyInstance.objects.create(month=self.month)
        instance.budget_items.add(self.budget_item1, self.budget_item2)
        
        # Test calculate_total method
        total = instance.calculate_total()
        expected_total = Decimal('1350.00')  # 1200 + 150
        
        self.assertEqual(total, expected_total)
        self.assertEqual(instance.total_amount, expected_total)
    
    def test_unique_month_constraint(self):
        """Test that only one monthly instance per month is allowed"""
        MonthlyInstance.objects.create(month=self.month)
        
        # Try to create another instance for the same month
        with self.assertRaises(Exception):  # IntegrityError in real DB
            MonthlyInstance.objects.create(month=self.month)
