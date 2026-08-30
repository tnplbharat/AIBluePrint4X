# Salesforce Login Tests

Enterprise-grade Selenium + Java + Maven + TestNG framework for the Salesforce login page
(`https://login.salesforce.com/?locale=in`), using Page Object Model with PageFactory and XPath-only locators.

## Requirements

- JDK 11+
- Chrome or Firefox browser
- A valid Salesforce account (for the valid-login test)

## Configuration

Edit `src/main/resources/config.properties`:

| Key | Purpose |
|-----|---------|
| `baseUrl` | Login page URL (defaults to Salesforce) |
| `username` | Valid Salesforce username (leave blank to skip valid login) |
| `password` | Valid Salesforce password |
| `browser` | `chrome` (default) or `firefox` |
| `waitTimeout` | Explicit/implicit wait timeout in seconds (default `30`) |
| `rememberMe` | `true`/`false` — whether to tick Remember Me |

## Running the tests

Use the Maven Wrapper (no local Maven install needed):

```
mvnw.cmd test          # Windows
./mvnw test            # macOS / Linux
```

Run a single test class:

```
mvnw.cmd -Dtest=ValidLoginTest test
mvnw.cmd -Dtest=InvalidLoginTest test
```

## Notes

- The current Salesforce login page uses a two-step flow: enter username, click **Log In**, then the
  password field appears. `LoginPage.doLogin` handles this automatically.
- The password field is located via `//input[@type='password']` because Salesforce does not render an
  `id="password"` element in the two-step flow.
- All locators are XPath only, per the RICE POT prompt requirements. No `Thread.sleep()` is used —
  explicit `WebDriverWait` and implicit waits handle synchronization.
