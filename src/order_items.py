import constant
import sys

import schedule
import time

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd

import json
import os
import random
from datetime import datetime


def get_file(filename):
    return os.path.join(os.path.dirname(__file__), filename)


def load_config():
    with open(get_file('../config.json')) as f:
        return json.load(f)


def wait(max, min=1):
    random_seconds = random.uniform(min, max)
    time.sleep(random_seconds)


def current_time():
    return time.time()

def current_time_text():
    now = datetime.now()
    date_time = now.strftime("%m-%d-%Y %H-%M")
    return date_time

class InvalidItemException(Exception):
    "Item not found"
    pass

class InvalidSizeException(Exception):
    "size not found for that Item"
    pass

    
def log_item(new_data,filename):
    new_df = pd.DataFrame(new_data)
    
    try:
        existing_df = pd.read_excel(filename+".xlsx")
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    except FileNotFoundError:
        combined_df = new_df

    combined_df.to_excel(filename+".xlsx", index=False)

def block_aggressively(route):
    if (route.request.resource_type in constant.RESOURCE_EXCLUSTIONS):
        route.abort()
    else:
        route.continue_()

def set_order(page, item_code, size, qty):
    full_url = constant.get_url("search") + item_code
    page.goto(full_url)

    try:
        page.wait_for_selector('.product-item')
    except:
        raise InvalidItemException
        
    page.click('.enter-qty')
    wait(2, 3)
    
    # # Get Size
    html = page.inner_html("(//div[@class='size-table']//div)[1]")
    soup = BeautifulSoup(html, 'html.parser')
    size_elements = soup.find_all('div', class_='item')
    sizes = [size.text.strip() for size in size_elements]
    found = False

    for index, value in enumerate(sizes):
        if(float(value) == size):
            input_fields = page.locator(f"(//input[@class='el-input__inner'])[{index + 1 }]")
            input_fields.fill(str(qty))
            found = True

            try:
                qty_available = page.query_selector(f".el-loading-mask+ .product-wrap .stripe .item:nth-child({index + 1 })")
                print("qty_available", qty_available.inner_text())
            except:
                print("qty_available -")


            print(f"ordering {item_code} size: {size} ->  {qty} pcs.")

            wait(1, 2)
            break

    button = page.locator("//div[@class='header']/following-sibling::button[1]");
    button.click()
    
    if not found:
        raise InvalidSizeException

def main():
    with sync_playwright() as p:
        try:
            df = pd.read_excel(constant.EXCEL_INPUT_FILE_PATH)
            items = df.to_dict(orient='records')
            
            if (len(items) < 1):
                print("No item row in file file.")
                sys.exit()
            
        except:
            print("Please check the input excel file.")
            sys.exit()
        
        
        
        log_file = constant.EXCEL_OUTPUT_FILE_PATH + current_time_text()


        # browser = p.chromium.launch(headless=False, slow_mo=50)
        browser = p.chromium.launch()
        page = browser.new_page()
   
        page.set_viewport_size({"width": 1280, "height": 1080})
        page.route("**/*", block_aggressively)

        # # login page
        print("<" * 30)
        print("login process start")
        page.goto(constant.get_url('login'), timeout=120000)
        page.fill('input#userNameId', configs['USERNAME'])
        page.fill('input#userPasswordId', configs['PASSWORD'])
        page.click("button[type=submit]")

        page.wait_for_selector('div.ugg_message')

        print("login success")
        print(">" * 30)
        # Now logged in
        
        for item in items:
            error = ""
            try:
                set_order(page, item['SKU'], item['SIZE'], item['QTY'])
            except InvalidItemException:
                error = (f"{item['SKU']} not found.")
            except InvalidSizeException:
                error = (f"For {item['SKU']} size {item['SIZE']} not found.")
            except:
                error = (f"Exception thrown. error item {item['SKU']}.")


            data = {
                    "SKU": item['SKU'],
                    "SIZE": item['SIZE'],
                    "QTY": item['QTY'],
                    "time": current_time_text()
            }

            if error:
                data["status"] = "ERROR :" + error 
            else:
                data["status"] = "Success.."
                
            log_item([data], log_file)


        browser.close()

# ________________________________________________________________________________
configs = load_config()

def start_order():
    start_time = current_time()

    print("Starting .. ")
    print("-." * 30)

    main()

    print("-." * 30)
    print("Done .. ")

    time_difference = current_time() - start_time
    print(f'Scraping time: %.2f seconds.' % time_difference)
    
    print("\n\n\n\n")


if __name__ == "__main__":
    start_order()
    print(f"Autometically Srart ording in {configs['SCHEDULE_DELAY']} minutes")
    print("-" * 40)

    schedule.every(configs['SCHEDULE_DELAY']).minutes.do(start_order)

    while True:
        rs = schedule.idle_seconds()
        rm = rs // 60
       
        # user_input = input("\nPress 'q' and Enter to stop the process: ")
        # if user_input.strip().lower() == 'q':
        #     print("Stopping the process...")
        #     break
        
        sys.stdout.write(f"\rNext call in {int(rm)}:{int(rs-(configs['SCHEDULE_DELAY']*rm))}")
        sys.stdout.flush()
        
        schedule.run_pending()
        time.sleep(1)