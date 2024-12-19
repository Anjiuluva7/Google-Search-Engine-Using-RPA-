from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from bs4 import BeautifulSoup
import json
import requests



app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'  # Set a secret key for session management
GEMINI_API_KEY = "AIzaSyBfkJtHOipUFdLt8rkY7zb6poNZSpIXFYs"

@app.route('/')
def index():
    if 'logged_in' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remember_me = 'remember_me' in request.form

        # Retrieve stored users from localStorage (saved as JSON)
        users = json.loads(request.cookies.get('users', '{}'))

        if email in users and users[email]['password'] == password:
            session['logged_in'] = True
            session['email'] = email
            if remember_me:
                session.permanent = True  # To remember the session even after the browser is closed
            return redirect(url_for('index'))

        return "Invalid email or password", 403

    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        who_are_you = request.form['who_are_you']
        gender = request.form['gender']
        email = request.form['email']
        password = request.form['password']

        # Retrieve users data from cookies (if any)
        users = json.loads(request.cookies.get('users', '{}'))

        if email in users:
            return "User already exists", 400

        users[email] = {
            'name': name,
            'age': age,
            'who_are_you': who_are_you,
            'gender': gender,
            'email': email,
            'password': password
        }

        # Save the updated users back to cookies (or session storage if you prefer)
        response = redirect(url_for('login'))
        response.set_cookie('users', json.dumps(users))
        return response

    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    # session.clear()  # Remove session data
    # return redirect(url_for('login'))
    session.pop('user', None) 
    return redirect('/login')

@app.route('/automation', methods=['GET', 'POST'])
def run_automation():
    if request.method == 'POST':
        search_key = request.form.get('search_key')  
        title = selenium_code(search_key)  
        return title 

@app.route('/extract_links', methods=['POST'])
def extract_links():
    search_key = request.form.get('search_key')   
    results = selenium_extract_links(search_key)  
    indexed_results = [(idx + 1, result) for idx, result in enumerate(results)]
    return render_template('links.html', results=indexed_results, search_query=search_key)  

def selenium_code(search_key):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.maximize_window()
    driver.get('https://www.google.com')
    driver.find_element(By.XPATH, "//textarea[@class='gLFyf']").send_keys(search_key)
    driver.find_element(By.XPATH, "//input[@name='btnK']").submit()
    title = driver.title
    driver.quit()
    return title

def selenium_extract_links(search_key):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run in headless mode (no GUI)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    query = search_key
    results = []
    n_pages = 2  

    for page in range(1, n_pages + 1):
        url = f"http://www.google.com/search?q={query}&start={(page - 1) * 10}"
        driver.get(url)
        # bs will scrape the websites
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        search_results = soup.find_all('div', class_="yuRUbf")
        for result in search_results:
            link = result.a.get('href')  
            title = result.h3.text if result.h3 else 'No title available'  
            # description = result.find_next('div', {'class': 'VwiC3b yXK7lf lVm3ye r025kc hJNv6b Hdw6tb'})
            description = result.find_next('div', {'class': 'VwiC3b yXK7lf p4wth r025kc hJNv6b Hdw6tb'})            
            # metadata is also called as description
            metadata = description.text.strip() if description else 'No description available'
            image_url = result.find('img')['src'] if result.find('img') else None
            results.append({
                'link': link,
                'title': title,
                'metadata': metadata,
                'image_url': image_url
            })

    driver.quit()
    return results  # Return the list of extracted results




@app.route('/chat')
def chat():
    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True)
