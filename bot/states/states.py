"""All FSM states for multi-step dialogs."""

from aiogram.fsm.state import State, StatesGroup


class ExpenseStates(StatesGroup):
    """Expense entry dialog."""
    category = State()        # Choose category
    payment_type = State()    # Cash / Card
    from_cash = State()       # From cash register? (if cash)
    amount = State()          # Enter amount
    comment = State()         # Enter comment
    receipt_ask = State()     # Attach receipt?
    receipt_photo = State()   # Upload receipt photo


class UtilityStates(StatesGroup):
    """Utility (electricity) entry dialog."""
    t1_reading = State()      # T1 meter reading
    t2_reading = State()      # T2 meter reading
    confirm_amount = State()  # Confirm calculated or enter manual
    manual_amount = State()   # Manual amount entry
    receipt_ask = State()     # Attach receipt?
    receipt_photo = State()   # Upload receipt photo


class IncomeStates(StatesGroup):
    """Income entry dialog."""
    amount = State()          # Enter amount
    payment_type = State()    # Cash / Card
    source = State()          # Where from
    destination = State()     # Where to (cash / account / expenses)


class ReceiptStates(StatesGroup):
    """Receipt attachment to existing expense."""
    select_expense = State()  # Choose expense
    upload_photo = State()    # Upload receipt photo


class SalaryAdminStates(StatesGroup):
    """Admin salary / points evaluation."""
    select_shift = State()    # Choose shift to evaluate
    set_points = State()      # Set points -3..+3
    confirm = State()         # Confirm salary


class SalaryCleanerStates(StatesGroup):
    """Cleaner salary entry."""
    name = State()            # Cleaner name
    period_start = State()    # Period start
    period_end = State()      # Period end
    days_count = State()      # Number of days
    confirm = State()         # Confirm


class EquipmentBreakStates(StatesGroup):
    """Equipment breakdown report."""
    name = State()            # What broke
    pc_number = State()       # PC number / location
    description = State()     # Problem description


class EquipmentRepairStates(StatesGroup):
    """Equipment repair report."""
    select_item = State()     # Select broken item
    master = State()          # Repair master/shop
    cost = State()            # Repair cost
    warranty = State()        # Warranty months
    receipt_ask = State()     # Attach receipt?
    receipt_photo = State()   # Upload receipt photo


class EquipmentPurchaseStates(StatesGroup):
    """Equipment purchase."""
    name = State()            # Item name
    store = State()           # Store name
    cost = State()            # Cost
    warranty = State()        # Warranty months
    serial = State()          # Serial number
    receipt_ask = State()     # Attach receipt?
    receipt_photo = State()   # Upload receipt photo


class EquipmentDecommissionStates(StatesGroup):
    """Equipment decommission."""
    select_item = State()     # Select item
    reason = State()          # Reason


class InventoryStates(StatesGroup):
    """Inventory check."""
    conducted_by = State()    # Who conducted
    items_checked = State()   # What was checked
    notes = State()           # Notes
    result = State()          # Result


class TaskCreateStates(StatesGroup):
    """Task creation."""
    description = State()     # Task description
    deadline = State()        # Deadline
    priority = State()        # Priority


class TaskCompleteStates(StatesGroup):
    """Task completion."""
    comment = State()         # Completion comment


class TaskEditStates(StatesGroup):
    """Task editing."""
    field = State()           # Which field to edit
    value = State()           # New value


class TaskCommentStates(StatesGroup):
    """Adding comment to task."""
    text = State()            # Comment text


class SettingsStates(StatesGroup):
    """Settings editing."""
    menu = State()            # Main settings menu
    edit_value = State()      # Enter new value
