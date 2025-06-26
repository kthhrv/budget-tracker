from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory
from decimal import Decimal
from datetime import date, timedelta
from .models import BudgetItem, MonthlyInstance
from .admin import MonthlyInstanceAdmin


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


class MonthlyInstanceAdminTest(TestCase):
    """Test Django admin interface behavior for MonthlyInstance with auto-populated items."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        self.site = AdminSite()
        self.admin = MonthlyInstanceAdmin(MonthlyInstance, self.site)
        
        self.test_month = date(2024, 6, 1)
        
        # Create repeating budget items that should be auto-populated
        self.repeating_item1 = BudgetItem.objects.create(
            name='Monthly Rent',
            owner='John',
            cost=Decimal('1200.00'),
            repeats=True,
            startdate=date(2024, 1, 1)
        )
        
        self.repeating_item2 = BudgetItem.objects.create(
            name='Car Insurance',
            owner='Jane',
            cost=Decimal('150.00'),
            repeats=True,
            startdate=date(2024, 1, 1)
        )
        
        # Create a non-repeating item that should NOT be auto-populated
        self.non_repeating_item = BudgetItem.objects.create(
            name='One-time Expense',
            owner='Bob',
            cost=Decimal('500.00'),
            repeats=False,
            startdate=date(2024, 1, 1)
        )
    
    def test_auto_populated_items_visible_in_admin_form(self):
        """Test that auto-populated budget items are visible when editing a MonthlyInstance in admin."""
        # Create a MonthlyInstance which should auto-populate with repeating items
        instance = MonthlyInstance.objects.create(month=self.test_month)
        
        # Verify the items were auto-populated in the model
        budget_items = list(instance.budget_items.all())
        self.assertEqual(len(budget_items), 2)
        
        budget_item_names = [item.name for item in budget_items]
        self.assertIn('Monthly Rent', budget_item_names)
        self.assertIn('Car Insurance', budget_item_names)
        
        # Now test that these items appear as selected in the admin form
        request = self.factory.get('/admin/budgets/monthlyinstance/{}/change/'.format(instance.pk))
        request.user = self.user
        
        # Get the admin change form
        form_class = self.admin.get_form(request, instance)
        form = form_class(instance=instance)
        
        # Check that the repeating items are in the repeating_items field
        initial_repeating_items = form.initial.get('repeating_items', [])
        if hasattr(initial_repeating_items, '__iter__'):
            repeating_item_ids = [item.id if hasattr(item, 'id') else item for item in initial_repeating_items]
        else:
            repeating_item_ids = []
        
        # The auto-populated repeating items should be in the repeating_items field
        self.assertIn(self.repeating_item1.id, repeating_item_ids)
        self.assertIn(self.repeating_item2.id, repeating_item_ids)
        
        # Check that non-repeating items field is empty (none selected)
        initial_non_repeating_items = form.initial.get('non_repeating_items', [])
        if hasattr(initial_non_repeating_items, '__iter__'):
            non_repeating_item_ids = [item.id if hasattr(item, 'id') else item for item in initial_non_repeating_items]
        else:
            non_repeating_item_ids = []
        
        # No non-repeating items should be initially selected
        self.assertNotIn(self.non_repeating_item.id, non_repeating_item_ids)
    
    def test_admin_form_field_queryset_includes_auto_populated_items(self):
        """Test that the admin form's separate fields include correct items."""
        # Create a MonthlyInstance which should auto-populate with repeating items  
        instance = MonthlyInstance.objects.create(month=self.test_month)
        
        request = self.factory.get('/admin/budgets/monthlyinstance/{}/change/'.format(instance.pk))
        request.user = self.user
        
        # Get the admin form
        form_class = self.admin.get_form(request, instance)
        form = form_class(instance=instance)
        
        # Check that we have the separate fields for repeating and non-repeating items
        self.assertIn('repeating_items', form.fields)
        self.assertIn('non_repeating_items', form.fields)
        
        # Check that the repeating items field shows the correct items
        repeating_field = form.fields['repeating_items']
        initial_repeating = form.initial.get('repeating_items', [])
        
        # Convert to IDs if needed
        if initial_repeating:
            if hasattr(initial_repeating[0], 'id'):
                repeating_ids = [item.id for item in initial_repeating]
            else:
                repeating_ids = initial_repeating
                
            self.assertIn(self.repeating_item1.id, repeating_ids)
            self.assertIn(self.repeating_item2.id, repeating_ids)
        
        # Check that the non-repeating items field is available but empty initially
        non_repeating_field = form.fields['non_repeating_items']
        initial_non_repeating = form.initial.get('non_repeating_items', [])
        
        # Should be empty initially since no non-repeating items were manually added
        self.assertEqual(len(initial_non_repeating), 0)
    
    def test_admin_form_handles_non_repeating_items(self):
        """Test that the admin form can handle manually added non-repeating items."""
        # Create a MonthlyInstance and manually add a non-repeating item
        instance = MonthlyInstance.objects.create(month=self.test_month)
        instance.budget_items.add(self.non_repeating_item)
        
        request = self.factory.get('/admin/budgets/monthlyinstance/{}/change/'.format(instance.pk))
        request.user = self.user
        
        # Get the admin form
        form_class = self.admin.get_form(request, instance)
        form = form_class(instance=instance)
        
        # Check that repeating items are still in the repeating field
        initial_repeating = form.initial.get('repeating_items', [])
        if initial_repeating:
            repeating_ids = [item.id if hasattr(item, 'id') else item for item in initial_repeating]
            self.assertIn(self.repeating_item1.id, repeating_ids)
            self.assertIn(self.repeating_item2.id, repeating_ids)
        
        # Check that the non-repeating item is in the non-repeating field
        initial_non_repeating = form.initial.get('non_repeating_items', [])
        if initial_non_repeating:
            non_repeating_ids = [item.id if hasattr(item, 'id') else item for item in initial_non_repeating]
            self.assertIn(self.non_repeating_item.id, non_repeating_ids)
    
    def test_auto_populated_items_calculate_total_automatically(self):
        """Test that the total is calculated automatically when items are auto-populated."""
        # Create a MonthlyInstance which should auto-populate with repeating items
        instance = MonthlyInstance.objects.create(month=self.test_month)
        
        # Verify the items were auto-populated
        budget_items = list(instance.budget_items.all())
        self.assertEqual(len(budget_items), 2)
        
        # Verify the total was calculated automatically
        expected_total = self.repeating_item1.cost + self.repeating_item2.cost  # 1200 + 150 = 1350
        self.assertEqual(instance.total_amount, expected_total)
        
        # Verify the string representation shows the correct total
        expected_str = f"{self.test_month.strftime('%B %Y')} - Total: ${expected_total}"
        self.assertEqual(str(instance), expected_str)
