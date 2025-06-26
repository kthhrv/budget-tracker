# Budget Item Model

This Django model allows you to store and manage budget items like rent, insurance, and other expenses.

## Model Fields

### Required Fields
- **name** (CharField): Name of the budget item (e.g., "Monthly Rent", "Car Insurance")
- **owner** (CharField): Owner of this budget item
- **amount** (DecimalField): Monetary amount for the budget item (minimum $0.01)

### Optional Fields
- **is_repeating** (BooleanField): Whether this budget item repeats (default: False)
- **end_date** (DateField): Optional end date for when this budget item should stop

### Automatic Fields
- **created_at** (DateTimeField): Automatically set when the item is created
- **updated_at** (DateTimeField): Automatically updated when the item is modified

## Usage Examples

### Creating Budget Items

```python
from budget_tacker.models import BudgetItem
from decimal import Decimal
from datetime import date

# Create a recurring monthly rent payment
rent = BudgetItem.objects.create(
    name="Monthly Rent",
    owner="John Doe",
    amount=Decimal('1200.00'),
    is_repeating=True
)

# Create car insurance with an end date
insurance = BudgetItem.objects.create(
    name="Car Insurance",
    owner="Jane Smith", 
    amount=Decimal('150.00'),
    is_repeating=True,
    end_date=date(2024, 12, 31)
)

# Create a one-time expense
repair = BudgetItem.objects.create(
    name="Home Repair",
    owner="Bob Wilson",
    amount=Decimal('500.00'),
    is_repeating=False
)
```

### Querying Budget Items

```python
# Get all budget items
all_items = BudgetItem.objects.all()

# Get only repeating items
repeating_items = BudgetItem.objects.filter(is_repeating=True)

# Get items by owner
johns_items = BudgetItem.objects.filter(owner="John Doe")

# Get items that end before a certain date
from datetime import date
ending_soon = BudgetItem.objects.filter(
    end_date__lte=date(2024, 6, 30)
)
```

## Django Admin Interface

The model is registered with Django admin and includes:
- List view with all key fields
- Filtering by owner, repeating status, and creation date
- Search functionality by name and owner
- Organized fieldsets for better user experience
- Read-only timestamp fields

## Model Features

- **Validation**: Amount must be at least $0.01
- **Ordering**: Items are ordered by creation date (newest first)
- **String Representation**: Shows name, owner, and amount
- **Help Text**: Descriptive help text for all fields
- **Meta Options**: Proper verbose names for admin interface

## Testing

The model includes comprehensive tests covering:
- Basic model creation
- String representation
- Field validation
- Ordering behavior
- Optional field handling

Run tests with: `python manage.py test budget_tacker`

## Requirements Met

This implementation satisfies all the requirements from the original issue:

✅ **Budget items storage** (rent, insurance, etc.)  
✅ **Owner option** - CharField to identify the owner  
✅ **Repeating option** - Boolean field for recurring expenses  
✅ **End date option** - Optional DateField for when items should end  

Plus additional useful features:
- Amount field with validation
- Automatic timestamps
- Django admin integration
- Comprehensive test coverage
- Proper model metadata and documentation