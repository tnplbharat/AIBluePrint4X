package com.enterprise.framework.driver;

import com.enterprise.framework.config.ConfigReader;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.firefox.FirefoxOptions;

import java.time.Duration;

public class DriverFactory {

    private static WebDriver driver;

    private DriverFactory() {
    }

    public static synchronized WebDriver initDriver() {
        if (driver != null) {
            return driver;
        }
        String browser = ConfigReader.getBrowser();
        try {
            switch (browser.toLowerCase()) {
                case "firefox":
                    driver = new FirefoxDriver(new FirefoxOptions());
                    break;
                case "chrome":
                default:
                    driver = new ChromeDriver(new ChromeOptions());
                    break;
            }
        } catch (Exception e) {
            throw new IllegalStateException("Failed to initialize " + browser + " driver", e);
        }
        driver.manage().window().maximize();
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(ConfigReader.getWaitTimeout()));
        return driver;
    }

    public static synchronized void quitDriver() {
        if (driver != null) {
            try {
                driver.quit();
            } catch (Exception e) {
                throw new IllegalStateException("Failed to quit driver cleanly", e);
            } finally {
                driver = null;
            }
        }
    }

    public static WebDriver getDriver() {
        return driver;
    }
}
