## Repo context

In this repository, the primary files of interest for implementing a theme switcher (light/neon dark mode) in the Expense Splitter application are:

- `app/static/style.css`: Contains the CSS styles that will need to adapt to theme switching.
- `app/static/app.js`: Requires modifications to include theme switching logic with JavaScript.
- `app/templates/base.html`: The main layout template where the theme switcher control will be integrated.
- `app/__init__.py`: Application setup and configuration which may need adjustment depending on the theme switcher implementation.
- Several HTML templates in `app/templates/`: Dashboard, groups, etc., which will indirectly reflect theme changes.

## Files to change

- `app/static/style.css`
- `app/static/app.js`
- `app/templates/base.html`
- `tests/test_app.py`

## Implementation Steps

1. **Define CSS Variables for Neon Dark Mode**: Extend `app/static/style.css` to include new CSS variables for neon-themed dark mode.
2. **JavaScript Logic for Theme Switching**: Implement functionality in `app/static/app.js` to manage theme state (light or neon dark) and apply the corresponding CSS class to the HTML root or body.
3. **Add Theme Switcher Control**: Integrate a toggle switch in `app/templates/base.html` for users to switch between themes, utilizing a simple button or slider.
4. **Persist Theme Preference**: Store user theme preference using `localStorage` so that theme choice persists across page reloads.
5. **Adjust Flask Application Setup**: Verify and adjust if necessary `app/__init__.py` for the correct serving of static assets associated with themes.
6. **Update Tests**: Write unit and integration tests in `tests/test_app.py` to cover the new theme switcher functionality, ensuring it behaves correctly under various scenarios.

## Tests to Run

- Run existing tests using `pytest` to ensure no regressions have occurred.
- Add new tests specifically for theme switching and verify that both themes apply styles correctly.

## Risks

- Challenging to ensure CSS styles look good and are readable in both themes.
- User interface interrupts if JavaScript fails to correctly toggle themes.
- Possible discrepancies in how CSS is applied across different web browsers in neon theme.
