import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

#Cambridge IGCSE Subject List URL
CAMBRIDGE_IGCSE_URL = "https://www.cambridgeinternational.org/programmes-and-qualifications/cambridge-upper-secondary/cambridge-igcse/subjects/"

def fetch_cambridge_subjects():
    """Fetches IGCSE subject list from Cambridge International's website using Selenium."""

    #Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    #Load the Cambridge IGCSE page
    driver.get(CAMBRIDGE_IGCSE_URL)
    time.sleep(5)  # Wait for JavaScript to load

    subjects = []
    try:
        #Find all <a> tags containing subject links
        subject_links = driver.find_elements(By.TAG_NAME, "a")

        for link in subject_links:
            href = link.get_attribute("href")  # Get the href attribute
            text = link.text.strip()  # Get the visible text
            
            #Filter only valid subject links (href should contain "cambridge-igcse-")
            if href and "cambridge-igcse-" in href and text:
                subjects.append(text)

    except Exception as e:
        subjects = [f"Error extracting subjects: {str(e)}"]

    #Close the browser
    driver.quit()

    return {"subjects": subjects if subjects else ["No subjects found"]}

@app.route("/get_subjects", methods=["GET"])
def get_subjects():
    """API endpoint to return Cambridge IGCSE subjects."""
    return jsonify(fetch_cambridge_subjects())

if __name__ == "__main__":
    app.run(debug=True)








