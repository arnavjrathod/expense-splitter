## Repo Context

The repository contains a Flask application for managing groups and their expenses, with a focus on creating, editing, and deleting expenses and settlements. Following files are relevant to implement the feature to change the people inside a split after creation:

- `app/expenses.py`: Manages expenses including their creation and editing.
- `app/settlements.py`: Handles settlements between group members.
- `app/groups.py`: Contains logic for managing group-related operations.
- `tests/test_app.py`: Integration tests for the application.

## Files to Change

1. `app/expenses.py`
2. `app/groups.py`
3. `tests/test_app.py`

## Implementation Steps

1. **Update Expense Handling**
   - Modify `app/expenses.py` to allow updating the participant list for an existing expense.
   - Ensure that when an expense is edited, the shares can be updated to include or exclude group members.

2. **Update Group Details Page**
   - Adjust `app/groups.py` to incorporate changes in group details view if participant changes affect balances or other displayed information.

3. **Validation and Notifications**
   - Adjust share validation logic to handle the dynamic adjustment of group members in `app/expenses.py`.
   - Ensure appropriate notifications or warnings are shown if necessary when participants are changed.

4. **Integration Testing**
   - Define or update tests in `tests/test_app.py` to cover changing participants in an existing expense.
   - Validate that all edge cases are handled, such as a user being removed from a split and ensuring balances are correctly updated.

## Tests to Run

- Run the existing test suite in `tests/test_app.py`.
- Specifically check tests related to expense editing and group detail views to ensure they account for dynamic participant changes.

## Risks

- Modifying participant lists on existing expenses could affect settlement calculations or historical data integrity.
- Ensuring that removing members from an expense split aligns with business rules and does not lead to orphaned references or inconsistencies.
- Validating that changing participants doesn’t create or highlight unexpected settlements.

## Conclusion

The implementation requires modifications primarily in the expense and group handling logic to allow for dynamic changes in group members affecting expense splits. Comprehensive testing will be crucial to ensure that these changes do not negatively impact existing functionalities or data consistency.