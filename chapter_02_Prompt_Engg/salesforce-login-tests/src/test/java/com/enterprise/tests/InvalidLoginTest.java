package com.enterprise.tests;

import com.enterprise.framework.pages.LoginPage;
import org.testng.Assert;
import org.testng.annotations.Test;

public class InvalidLoginTest extends BaseTest {

    @Test
    public void verifyInvalidLoginShowsErrorMessage() {
        try {
            LoginPage loginPage = new LoginPage(driver);
            loginPage.navigate();
            loginPage.doLogin("invalid.user@example.com", "invalidPassword123!");
            String errorText = loginPage.getErrorMessage();
            Assert.assertFalse(errorText.isEmpty(),
                    "Expected a non-empty error message on invalid login");
        } catch (Exception e) {
            throw new AssertionError("Invalid login test failed", e);
        }
    }
}
