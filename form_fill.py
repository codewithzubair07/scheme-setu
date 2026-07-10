from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def _set_value(driver: webdriver.Chrome, field_id: str, value: str) -> None:
    element = driver.find_element(By.ID, field_id)
    element.clear()
    element.send_keys(value)


def fill_form(user_data: dict, matched_scheme: dict, output_screenshot_path: str) -> str:
    """Opens mock_form.html locally, fills fields, takes screenshot, and returns path."""
    html_path = Path(__file__).with_name("mock_form.html").resolve()
    file_url = html_path.as_uri()

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1366,1200")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        driver.get(file_url)

        _set_value(driver, "full_name", str(user_data.get("full_name", "Applicant Name")))
        _set_value(driver, "aadhaar_number", str(user_data.get("aadhaar_number", "0000-0000-0000")))
        _set_value(driver, "category", str(user_data.get("category") or matched_scheme.get("category") or "Any"))

        income_lakh = user_data.get("income_lakh")
        annual_income = "Not Specified"
        if isinstance(income_lakh, (int, float)):
            annual_income = str(int(float(income_lakh) * 100000))
        _set_value(driver, "annual_income", annual_income)

        _set_value(driver, "state", str(user_data.get("state") or "Not Specified"))
        _set_value(driver, "scheme_name", str(matched_scheme.get("name") or "No scheme matched"))

        docs_container = driver.find_element(By.ID, "documents_container")
        for doc in matched_scheme.get("documents_required", []):
            driver.execute_script(
                """
                const parent = arguments[0];
                const docName = arguments[1];
                const wrapper = document.createElement('div');
                wrapper.className = 'doc-item';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = true;
                const label = document.createElement('label');
                label.style.display = 'inline';
                label.style.marginLeft = '8px';
                label.textContent = docName;
                wrapper.appendChild(checkbox);
                wrapper.appendChild(label);
                parent.appendChild(wrapper);
                """,
                docs_container,
                doc,
            )

        driver.save_screenshot(output_screenshot_path)
        return output_screenshot_path
    finally:
        driver.quit()