## Repo Context

Inspected files in the repository to gather requirements for adding a theme switcher feature:

- `./app/static/style.css`: Contains the CSS styles, including color variables likely to be used for theme switching.
- `./app/static/app.js`: Contains JavaScript code that likely handles client-side functionality and interactions, which will be relevant for switching themes dynamically.
- `./app/templates/base.html`: The base HTML template file, which links the CSS and JavaScript files. This file will likely need modifications to support a theme toggle UI.

## Files to Change

1. `app/templates/base.html`
2. `app/static/app.js`
3. `app/static/style.css`

## Implementation Steps

1. **Update HTML Template**
   - Modify `app/templates/base.html` to add a theme toggle UI element, such as a button or switch.

2. **Enhance JavaScript for Theme Toggling**
   - Edit `app/static/app.js` to implement JavaScript logic that changes the theme by toggling CSS classes or updating the CSS variables.

3. **Add CSS for Theme Variants**
   - Update `app/static/style.css` to define additional CSS variables or classes that represent the "light" and "neon dark" themes.

## Tests to Run

- Test switching between themes manually by interacting with the UI elements added.

## Risks

- Ensuring compatibility across different browsers.
- Preserving user-selected theme across sessions, which might require additional local storage handling.
- Potential increase in load times due to additional resources or scripts needed for theme switching.