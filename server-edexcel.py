from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

@app.route('/get_edexcel_subjects', methods=['GET'])
def get_edexcel_subjects():
    # Set up Selenium options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://qualifications.pearson.com/en/qualifications/edexcel-international-gcses.html")
        time.sleep(5)  # Wait for JavaScript to render content

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_elements = soup.find_all(['a', 'h3'])

        raw_subjects = [el.get_text(strip=True) for el in all_elements]
        seen = set()
        unique_subjects = []

        # Define desired subjects
        desired_subjects = {
            "Accounting",
            "Arabic as a first language",
            "Art and Design",
            "Bangla",
            "Bangladesh Studies",
            "Biology",
            "Business",
            "Chemistry",
            "Chinese",
            "Commerce",
            "Computer Science",
            "Economics",
            "English (as 2nd language)",
            "English Language A",
            "English Language B",
            "English Literature",
            "French",
            "Further Pure Mathematics",
            "Geography",
            "German",
            "Global Citizenship",
            "Greek as a first language",
            "History",
            "Human Biology",
            "Information and Communication Technology",
            "Islamic Studies",
            "Mathematics A",
            "Mathematics B",
            "Pakistan Studies",
            "Physics",
            "Religious Studies",
            "Sinhala",
            "Spanish",
            "Swahili",
            "Tamil"
        }

        for subject in raw_subjects:
            cleaned = subject.strip()
            if cleaned in desired_subjects and cleaned not in seen:
                unique_subjects.append(cleaned)
                seen.add(cleaned)

        # Sort alphabetically
        sorted_subjects = sorted(unique_subjects)

        return jsonify({"subjects": sorted_subjects})

    except Exception as e:
        return jsonify({"subjects": [f"Error extracting subjects: {str(e)}"]})
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(port=5001, debug=True)












