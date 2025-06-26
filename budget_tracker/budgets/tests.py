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


class MonthlyInstanceAutoPopulateTest(TestCase):
    """Test auto-population of repeating budget items in new monthly instances."""
    
    def setUp(self):
        self.test_month = date(2024, 6, 1)
        
        # Create repeating items with different scenarios
        self.active_repeating_item = BudgetItem.objects.create(
            name='Rent',
            owner='John',
            cost=Decimal('1200.00'),
            repeats=True,
            startdate=date(2024, 1, 1)  # Started before test month
        )
        
        self.future_repeating_item = BudgetItem.objects.create(
            name='Future Insurance',
            owner='Jane',
            cost=Decimal('150.00'),
            repeats=True,
            startdate=date(2024, 12, 1)  # Starts after test month
        )
        
        self.expired_repeating_item = BudgetItem.objects.create(
            name='Old Subscription',
            owner='Bob',
            cost=Decimal('50.00'),
            repeats=True,
            startdate=date(2024, 1, 1),
            end_date=date(2024, 3, 31)  # Expired before test month
        )
        
        self.non_repeating_item = BudgetItem.objects.create(
            name='One-time Payment',
            owner='Alice',
            cost=Decimal('500.00'),
            repeats=False,  # Not repeating
            startdate=date(2024, 1, 1)
        )
        
        self.active_with_future_end = BudgetItem.objects.create(
            name='Car Payment',
            owner='Charlie',
            cost=Decimal('300.00'),
            repeats=True,
            startdate=date(2024, 1, 1),
            end_date=date(2024, 12, 31)  # Ends after test month
        )
    
    def test_auto_populate_on_creation(self):
        """Test that repeating items are automatically added when creating a new monthly instance."""
        instance = MonthlyInstance.objects.create(month=self.test_month)
        
        # Should include active repeating items
        budget_items = list(instance.budget_items.all())
        budget_item_names = [item.name for item in budget_items]
        
        # Should include items that are active for this month
        self.assertIn('Rent', budget_item_names)
        self.assertIn('Car Payment', budget_item_names)
        
        # Should NOT include future, expired, or non-repeating items
        self.assertNotIn('Future Insurance', budget_item_names)
        self.assertNotIn('Old Subscription', budget_item_names)
        self.assertNotIn('One-time Payment', budget_item_names)
        
        # Should have exactly 2 items
        self.assertEqual(len(budget_items), 2)
    
    def test_auto_populate_respects_start_date(self):
        """Test that items starting after the month are not included."""
        early_month = date(2024, 1, 1)
        instance = MonthlyInstance.objects.create(month=early_month)
        
        budget_items = list(instance.budget_items.all())
        budget_item_names = [item.name for item in budget_items]
        
        # Only items that started on or before Jan 1, 2024
        self.assertIn('Rent', budget_item_names)
        self.assertIn('Car Payment', budget_item_names)
        self.assertNotIn('Future Insurance', budget_item_names)
    
    def test_auto_populate_respects_end_date(self):
        """Test that expired items are not included."""
        late_month = date(2024, 12, 1)
        instance = MonthlyInstance.objects.create(month=late_month)
        
        budget_items = list(instance.budget_items.all())
        budget_item_names = [item.name for item in budget_items]
        
        # Should include items that haven't expired by Dec 1, 2024
        self.assertIn('Rent', budget_item_names)  # No end date
        self.assertIn('Future Insurance', budget_item_names)  # Starts in Dec
        self.assertIn('Car Payment', budget_item_names)  # Ends Dec 31
        self.assertNotIn('Old Subscription', budget_item_names)  # Expired in March
    
    def test_manual_items_preserved(self):
        """Test that manually added items are preserved alongside auto-populated ones."""
        # Create instance (which auto-populates)
        instance = MonthlyInstance.objects.create(month=self.test_month)
        
        # Manually add a non-repeating item
        instance.budget_items.add(self.non_repeating_item)
        
        budget_items = list(instance.budget_items.all())
        budget_item_names = [item.name for item in budget_items]
        
        # Should have both auto-populated and manually added items
        self.assertIn('Rent', budget_item_names)  # Auto-populated
        self.assertIn('Car Payment', budget_item_names)  # Auto-populated
        self.assertIn('One-time Payment', budget_item_names)  # Manually added
        
        self.assertEqual(len(budget_items), 3)
    
    def test_no_duplicate_items(self):
        """Test that calling auto_populate_repeating_items multiple times doesn't create duplicates."""
        instance = MonthlyInstance.objects.create(month=self.test_month)
        
        # Call auto-populate again
        instance.auto_populate_repeating_items()
        
        budget_items = list(instance.budget_items.all())
        self.assertEqual(len(budget_items), 2)  # Should still be 2, not 4
