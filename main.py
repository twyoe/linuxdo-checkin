import os
import time
import random
import json
from tabulate import tabulate
from playwright.sync_api import sync_playwright

# 从环境变量中获取账号信息
ACCOUNTS_JSON = os.environ.get("LINUX_DO_ACCOUNTS")
if not ACCOUNTS_JSON:
    raise ValueError("LINUX_DO_ACCOUNTS environment variable is not set")

try:
    ACCOUNTS = json.loads(ACCOUNTS_JSON)
except json.JSONDecodeError:
    raise ValueError("LINUX_DO_ACCOUNTS is not a valid JSON string")

if not isinstance(ACCOUNTS, list) or not all(isinstance(account, dict) for account in ACCOUNTS):
    raise ValueError("LINUX_DO_ACCOUNTS should be a list of dictionaries")

HOME_URL = "https://linux.do/"

class LinuxDoBrowser:
    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.pw = sync_playwright().start()
        self.browser = self.pw.firefox.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def login(self):
        self.page.goto(HOME_URL)
        self.page.click(".login-button .d-button-label")
        self.page.fill("#login-account-name", self.username)
        self.page.fill("#login-account-password", self.password)
        self.page.click("#login-button")
        self.page.wait_for_selector("#current-user", timeout=10000)
        print(f"Check in success for {self.username}")
        return True

    def click_topic(self):
        topics = self.page.query_selector_all("#list-area .title")
        for topic in random.sample(topics, min(30, len(topics))):
            with self.context.new_page() as page:
                page.goto(HOME_URL + topic.get_attribute("href"))
                if random.random() < 0.02:
                    self.click_like(page)
                time.sleep(random.uniform(5, 15))

    def run(self):
        if not self.login():
            return
        for _ in range(3):
            self.click_topic()
            time.sleep(random.uniform(30, 60))
        self.print_connect_info()

    def click_like(self, page):
        page.locator(".discourse-reactions-reaction-button").first.click()
        print(f"Like success for {self.username}")

    def print_connect_info(self):
        with self.context.new_page() as page:
            page.goto("https://connect.linux.do/")
            rows = page.query_selector_all("table tr")
            info = [
                [cells[0].text_content().strip(), cells[1].text_content().strip(), cells[2].text_content().strip()]
                for cells in (row.query_selector_all("td") for row in rows[1:])
                if len(cells) >= 3
            ]
            print(f"--------------Connect Info for {self.username}-----------------")
            print(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))

    def close(self):
        self.context.close()
        self.browser.close()
        self.pw.stop()

def run_for_all_accounts():
    for account in ACCOUNTS:
        username = account.get("username")
        password = account.get("password")
        if not username or not password:
            print(f"Skipping account due to missing username or password: {account}")
            continue
        print(f"Starting process for {username}")
        with LinuxDoBrowser(username, password) as browser:
            browser.run()
        print(f"Finished process for {username}")
        time.sleep(random.uniform(60, 180))  # 在账号之间随机等待1-3分钟

if __name__ == "__main__":
    run_for_all_accounts()