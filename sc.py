from multiprocessing import Process, Manager
import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import re
import random
import time
import undetected_chromedriver as uc

class ChromeDriverManager:
    @staticmethod
    def create_chrome_driver():
        chrome_options = Options()
        service=Service()
        #chrome_options.add_argument("--disable-gpu")
        #chrome_options.add_argument("--disable-extensions")
        #chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        path="C:/Users/yosri/Desktop/scrapper"
        return uc.Chrome(service=service,options=chrome_options)

class MyUDC(uc.Chrome):
    def __del__(self):
        try:
            self.service.process.kill()
        except:  # noqa
            pass
        # self.quit()

class ProxyManager:
    @staticmethod
    def scrape_proxies(url='https://free-proxy-list.net/'):
        driver = ChromeDriverManager.create_chrome_driver()
        driver.get(url)
        time.sleep(random.uniform(3, 7))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the table containing proxies using the class name
        proxy_table = soup.find('table', {'class': 'table table-striped table-bordered'})
        
        if proxy_table is None:
            print("Error: Unable to find the proxy table.")
            driver.quit()
            return []

        # Extract proxies from the table
        proxies = []
        for row in proxy_table.find_all('tr')[1:]:
            columns = row.find_all('td')
            if len(columns) >= 2:
                ip = columns[0].text.strip()
                port = columns[1].text.strip()
                proxies.append(f'http://{ip}:{port}')

        driver.quit()
        return proxies

class WebManipulator:
    def __init__(self, url, iterations, refresh_interval, proxies_manager):
        self.url = url
        self.iterations = iterations
        self.refresh_interval = refresh_interval
        self.proxies_manager = proxies_manager
        self.cycle_count = 0
        self.last_refresh_time = time.time()

    def rotate_ip(self):
        if self.proxies_manager.proxies:
            proxy = random.choice(self.proxies_manager.proxies)
            uc.proxy.add_to_capabilities(uc.DesiredCapabilities.CHROME, proxy)
        else:
            raise Exception("No proxies available")

    def generate_user_agent(self):
        ua = UserAgent()
        return ua.random

    def move_cursor_randomly(self, element):
        speed_x = random.uniform(0.5, 1.5)
        speed_y = random.uniform(0.5, 1.5)
        action = ActionChains(self.driver)
        action.move_to_element_with_offset(element, speed_x, speed_y).perform()

    def scrape_data(self, url):
        self.driver.get(url)
        time.sleep(random.uniform(1, 3))
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', str(soup))
        phone_numbers = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', str(soup))
        return emails, phone_numbers


    def web_manipulation_iteration(self):
        try:
            self.rotate_ip()
            headers = {'User-Agent': self.generate_user_agent()}
            response = requests.get(self.url, headers=headers)
            time.sleep(random.uniform(1, 3))
            soup = BeautifulSoup(response.content, 'html.parser')
            external_links = [link.get('href') for link in soup.find_all('a', href=True) if 'http' in link.get('href')]

            for link in external_links:
                self.move_cursor_randomly(link)
                scraped_emails, scraped_phone_numbers = self.scrape_data(link)
                with open("results.txt", "a") as results_file:
                    results_file.write(f"Scraped Emails: {scraped_emails}\n")
                    results_file.write(f"Scraped Phone Numbers: {scraped_phone_numbers}\n")

            self.cycle_count += 1

            # Stop and close the process after every three cycles
            if self.cycle_count == 3:
                self.driver.quit()
                self.cycle_count = 0

            # Update last_refresh_time
            self.last_refresh_time = time.time()

        except Exception as e:
            pass
        finally:
            if self.driver:
                self.driver.quit()

    def run(self):
        for _ in range(self.iterations):
            if time.time() - self.last_refresh_time > self.refresh_interval:
                self.proxies_manager.proxies = ProxyManager.scrape_proxies()
                self.last_refresh_time = time.time()

            self.driver = ChromeDriverManager.create_chrome_driver()
            self.web_manipulation_iteration()

if __name__ == '__main__':
    with Manager() as manager:
        proxies_manager = manager.Namespace()
        proxies_manager.proxies = ProxyManager.scrape_proxies()

        # Example usage with 5 iterations
        web_manipulator = WebManipulator("https://toscrape.com/", 5, 9 * 60, proxies_manager)
        processes = []

        for _ in range(5):  # Change 5 to the desired number of processes
            process = Process(target=web_manipulator.run)
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
