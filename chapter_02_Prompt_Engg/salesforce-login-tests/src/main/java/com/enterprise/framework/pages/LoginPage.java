package com.enterprise.framework.pages;

import com.enterprise.framework.config.ConfigReader;
import com.enterprise.framework.utils.WaitUtils;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;

public class LoginPage {

    private static final By USERNAME_FIELD = By.xpath("//input[@id='username']");
    private static final By PASSWORD_FIELD = By.xpath("//input[@type='password']");
    private static final By LOGIN_BUTTON = By.xpath("//input[@id='Login']");
    private static final By REMEMBER_ME_CHECKBOX = By.xpath("//input[@id='rememberUn']");
    private static final By ERROR_MESSAGE = By.xpath("//div[@id='error']");

    private final WebDriver driver;

    @FindBy(xpath = "//input[@id='username']")
    private WebElement usernameField;

    @FindBy(xpath = "//input[@type='password']")
    private WebElement passwordField;

    @FindBy(xpath = "//input[@id='Login']")
    private WebElement loginButton;

    @FindBy(xpath = "//input[@id='rememberUn']")
    private WebElement rememberMeCheckbox;

    public LoginPage(WebDriver driver) {
        this.driver = driver;
        PageFactory.initElements(driver, this);
    }

    public void navigate() {
        try {
            driver.get(ConfigReader.getBaseUrl());
            WaitUtils.waitForVisible(driver, USERNAME_FIELD);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to navigate to login page", e);
        }
    }

    public void enterUsername(String username) {
        try {
            WaitUtils.waitForClickable(driver, USERNAME_FIELD);
            usernameField.clear();
            usernameField.sendKeys(username);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to enter username", e);
        }
    }

    public void clickLogin() {
        try {
            WaitUtils.waitForClickable(driver, LOGIN_BUTTON);
            loginButton.click();
        } catch (Exception e) {
            throw new IllegalStateException("Failed to click login button", e);
        }
    }

    public void enterPassword(String password) {
        try {
            WaitUtils.waitForClickable(driver, PASSWORD_FIELD);
            passwordField.clear();
            passwordField.sendKeys(password);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to enter password", e);
        }
    }

    public void clickRememberMe() {
        try {
            if (ConfigReader.isRememberMe()) {
                WaitUtils.waitForClickable(driver, REMEMBER_ME_CHECKBOX);
                if (!rememberMeCheckbox.isSelected()) {
                    rememberMeCheckbox.click();
                }
            }
        } catch (Exception e) {
            throw new IllegalStateException("Failed to interact with remember me checkbox", e);
        }
    }

    public void doLogin(String username, String password) {
        enterUsername(username);
        clickLogin();
        enterPassword(password);
        clickRememberMe();
        clickLogin();
    }

    public String getErrorMessage() {
        try {
            return WaitUtils.waitForText(driver, ERROR_MESSAGE);
        } catch (Exception e) {
            throw new IllegalStateException("Failed to read login error message", e);
        }
    }

    public String getCurrentUrl() {
        return driver.getCurrentUrl();
    }
}
