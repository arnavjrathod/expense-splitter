## Repo Context

The project is a web application called "Expense Splitter" designed for tracking shared expenses among groups. It uses Python, Flask, and SQLite, with front-end templating through Jinja2 and some vanilla JavaScript. The project is laid out with a primary application directory `app` containing Python modules for different features, templates for HTML, and static files such as CSS.

Files inspected:

- `app/templates/base.html`: Defines the base HTML structure, including links to CSS and JS files.
- `app/static/style.css`: Contains all the CSS styles applied to the HTML templates including the color scheme and layout styles. 
- `app/__init__.py`: Sets up the Flask application and configurations.
- `run.py`: Entry point for running the app.
- `tests/test_app.py`: Contains integration tests for the application.

## Files to Change

- `app/templates/base.html`
- `app/static/style.css`

## Implementation Steps

1. **Update HTML Templates**
   - Edit `app/templates/base.html` to reflect changes necessary for theme modifications. Add any new CSS class hooks needed for styling UI components to look like a code editor.

2. **Modify CSS**
   - Modify `app/static/style.css` to adopt a color scheme and styling similar to popular code editors like VS Code or Sublime Text. This includes:
     - Changing background, text colors, and styles to match code editor aesthetics.
     - Implement CSS grid and flex layouts as needed for code editor style UI customization.

3. **Testing**
   - Run the existing integration tests located in `tests/test_app.py` to ensure that application functionality remains intact.
   - Manually verify that the UI changes are applied correctly by running the app and visually checking the elements.

## Risks

- Modifying the existing CSS and HTML templates could introduce styling bugs that affect usability.
- CSS changes might not replicate a code editor theme exactly due to limitations in simple HTML/CSS versus a real editor application.
- Ensuring browser compatibility remains intact after style changes.