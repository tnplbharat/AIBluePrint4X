package com.enterprise.framework.utils;

import com.enterprise.framework.config.ConfigReader;
import org.openqa.selenium.By;
import org.openqa.selenium.NoSuchElementException;
import org.openqa.selenium.TimeoutException;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

public class WaitUtils {

    private WaitUtils() {
    }

    public static WebElement waitForVisible(WebDriver driver, By locator) {
        try {
            return new WebDriverWait(driver, Duration.ofSeconds(ConfigReader.getWaitTimeout()))
                    .until(ExpectedConditions.visibilityOfElementLocated(locator));
        } catch (TimeoutException | NoSuchElementException e) {
            throw new IllegalStateException("Element not visible within timeout: " + locator, e);
        }
    }

    public static WebElement waitForClickable(WebDriver driver, By locator) {
        try {
            return new WebDriverWait(driver, Duration.ofSeconds(ConfigReader.getWaitTimeout()))
                    .until(ExpectedConditions.elementToBeClickable(locator));
        } catch (TimeoutException | NoSuchElementException e) {
            throw new IllegalStateException("Element not clickable within timeout: " + locator, e);
        }
    }

    public static String waitForText(WebDriver driver, By locator) {
        try {
            return new WebDriverWait(driver, Duration.ofSeconds(ConfigReader.getWaitTimeout()))
                    .until(ExpectedConditions.visibilityOfElementLocated(locator)).getText();
        } catch (TimeoutException | NoSuchElementException e) {
            throw new IllegalStateException("Text not available within timeout: " + locator, e);
        }
    }
}
