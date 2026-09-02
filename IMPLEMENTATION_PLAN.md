# Implementation Plan: Theme Switcher

## Repo Context
1. **Files Read**: 
   - `app/static/style.css`: Contains the CSS variables for current theme styling.
   - `app/templates/base.html`: Main HTML template that includes links to stylesheets and scripts.

## Files to Change
1. `app/static/style.css`
2. `app/templates/base.html`
3. `app/static/app.js`: (to be created) Manage theme switching logic with JavaScript.
4. `app/templates/dashboard.html`: Add a button to toggle the theme.

## Implementation Steps

1. **Update Styles**
   - Edit `app/static/style.css` to organize CSS variables for both themes: light and neon dark.

2. **JavaScript for Theme Switching**
   - Create `app/static/app.js` to implement logic that toggles between light and dark mode using local storage to remember user preference.

3. **Integrate Theme Switcher in HTML**
   - Modify `app/templates/base.html` to include the JavaScript file (`app.js`).
   - Update `app/templates/dashboard.html` to add a button or toggle switch for changing themes. It should call a JavaScript function to switch themes on click.

4. **Ensure Default Theme**
   - Ensure the application loads with a default theme (e.g., light) on first load, checking local storage preferences thereafter.

5. **Test Functionality**
   - Run local server to test theme switching.
   - Ensure theme persists across page reloads and sessions.

## Tests to Run
1. Manual testing of the `dashboard.html` using different user agents and browsers to ensure the theme switcher works consistently.
2. Cross-browser testing for CSS to ensure both themes appear as expected.

## Risks
1. CSS styles may not be correctly overridden when switching themes.
2. JavaScript errors could prevent the theme switch from functioning or persisting.
3. Cross-browser inconsistencies in CSS variable support.