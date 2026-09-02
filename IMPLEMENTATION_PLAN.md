## Repo Context

The repository is a web application for tracking shared expenses, built using Python and Flask. The relevant files are structured within the `app` directory, containing subdirectories for `templates` and `static` assets. Key files include:

- `run.py`: Entrypoint for running the server, importing the application factory from `app`.
- `app/__init__.py`: Contains the application factory `create_app()` and configuration settings.
- `app/templates/base.html`: The base HTML template using Jinja templating, incorporating CSS and JavaScript assets.
- `app/static/style.css`: Contains the CSS definitions for the application's styles.
- `app/static/app.js`: JavaScript file for handling client-side interactions.

## Files to Change

- `app/templates/base.html`
- `app/static/style.css`
- `app/static/app.js`

## Implementation Steps

1. **Update CSS for Theme Support**
   - Modify `app/static/style.css` to define CSS custom properties for both light and dark themes. Ensure that these properties change based on a class (e.g., `dark-mode`) on the `body` element.

2. **Modify Base Template to Include Theme Switch**
   - Edit `app/templates/base.html` to include a button or a toggle switch in the navigation bar for switching themes.

3. **Add JavaScript for Theme Switching**
   - Update `app/static/app.js` to handle the theme switch. Implement logic to toggle the `dark-mode` class on the `body` element and store the user's preference in `localStorage`.

4. **Ensure Accessibility and Usability**
   - Confirm that theme switching works across different pages and that the preference persists even after page reloads.

## Tests to Run

- Manually test theme switching in a browser to ensure that the page updates properly.
- Write or update existing tests to verify that CSS classes are correctly applied for different themes.

## Risks

- **UI Disruption:** Changes to CSS could affect the layout or readability of the application.
- **JavaScript Issues:** Errors in JavaScript could prevent theme switching or cause other functionalities to break. These should be tested thoroughly.
- **Browser Compatibility:** Ensure the theme switch works across supported browsers, considering differences in handling of CSS and JavaScript.