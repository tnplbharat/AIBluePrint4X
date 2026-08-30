package com.enterprise.tests;

import com.enterprise.framework.driver.DriverFactory;
import org.openqa.selenium.WebDriver;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;

public class BaseTest {

    protected WebDriver driver;

    @BeforeMethod
    public void setUp() {
        try {
            driver = DriverFactory.initDriver();
        } catch (Exception e) {
            throw new IllegalStateException("Test setup failed while initializing driver", e);
        }
    }

    @AfterMethod
    public void tearDown() {
        try {
            DriverFactory.quitDriver();
        } catch (Exception e) {
            throw new IllegalStateException("Test teardown failed while quitting driver", e);
        }
    }
}
