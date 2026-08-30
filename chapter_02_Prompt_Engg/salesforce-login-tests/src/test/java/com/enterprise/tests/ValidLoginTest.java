package com.enterprise.tests;

import com.enterprise.framework.config.ConfigReader;
import com.enterprise.framework.pages.LoginPage;
import org.testng.Assert;
import org.testng.annotations.Test;

public class ValidLoginTest extends BaseTest {

    @Test
    public void verifyValidLoginNavigatesToHome() {
        try {
            LoginPage loginPage = new LoginPage(driver);
            loginPage.navigate();
            loginPage.doLogin(ConfigReader.getUsername(), ConfigReader.getPassword());
            Assert.assertTrue(loginPage.getCurrentUrl().contains("my.salesforce.com"),
                    "Expected redirection to Salesforce home, but URL was: " + loginPage.getCurrentUrl());
        } catch (Exception e) {
            throw new AssertionError("Valid login test failed", e);
        }
    }
}
