# Implementation Plan

## Objective
Add the ability to change the people inside a split after it has been created.

## Steps

1. **Understand the Current Codebase**
   - Review the existing data model for a split and determine how people are currently associated with it.
   - Identify where the creation of a split is handled in the codebase.

2. **Database Changes (if necessary)**
   - If the list of people in a split is stored in a way that makes modification difficult, modify the database schema as needed to support updates.
   - Ensure that these changes are backward compatible or include a migration script if necessary.

3. **API/Service Layer Updates**
   - Implement an API endpoint or extend an existing one to support updating the people in a split.
   - Ensure that the endpoint validates input, including checking that the people to be added or removed are valid users in the system.

4. **Business Logic**
   - Update or add business logic to handle adding, removing, or updating people in a split.
   - Take into account any business rules about who can be part of a split.

5. **UI/UX Design**
   - If applicable, modify the UI to allow users to change the people in a split.
   - Consider user experience best practices to ensure the interface is intuitive.

6. **Testing**
   - Write unit tests for backend changes.
   - Write integration tests for the API to ensure that changes are working as expected.
   - If the UI has been modified, conduct user testing to ensure the feature works well for end users.

7. **Documentation**
   - Update or create documentation for the new functionality.
   - Ensure that any necessary guides or help documents are updated to include how users can change the people in a split.

## Final Steps
- Conduct a code review with team members to ensure quality and adherence to the codebase standards.
- Deploy the changes to a staging environment for further testing.
- Prepare a rollout plan for deploying to production.