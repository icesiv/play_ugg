import os
import sys
import json
import time
import random

import schedule
import constant

import pandas as pd

from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


class InvalidItemException(Exception):
    "Item not found"
    pass

class InvalidSizeException(Exception):
    "size not found for that Item"
    pass


def load_config():
    with open(get_file('../config.json')) as f:
        return json.load(f)

def load_items_list():
    try:
        df = pd.read_excel(constant.EXCEL_INPUT_FILE_PATH)
        items = df.to_dict(orient='records')
        
        if (len(items) < 1):
            print("No item row in file file.")
            raise Exception
        
    except:
        print("Please check the input excel file.")
        sys.exit()

    return items

def get_file(filename):
    return os.path.join(os.path.dirname(__file__), filename)

def wait(max, min=1):
    random_seconds = random.uniform(min, max)
    time.sleep(random_seconds)

def current_time_text():
    now = datetime.now()
    date_time = now.strftime("%m-%d-%Y %H-%M")
    return date_time
    
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

# -----------------------------------------------------
# set_order Function
# -----------------------------------------------------

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

    button = page.locator("//div[@class='header']/following-sibling::button[1]")
    button.click()
    
    if not found:
        raise InvalidSizeException

# -----------------------------------------------------
# login Function
# -----------------------------------------------------

def login(playwright):
    # browser = playwright.chromium.launch(headless=False, slow_mo=50)
    browser = playwright.chromium.launch()
    page = browser.new_page()
    # page.set_viewport_size({"width": 1280, "height": 1080})
    page.route("**/*", block_aggressively)

    while True:
        ## login page
        print("<" * 30)
        print("login process start")
        
        try:
            page.goto(constant.get_url('login'))
            page.fill('input#userNameId', configs['USERNAME'])
            page.fill('input#userPasswordId', configs['PASSWORD'])
            page.click("button[type=submit]")
            page.wait_for_selector('div.ugg_message')
            
            print("login success")
            print(">" * 30)
            
            return page
        except:
            print("login timeout..")

        print("trying to login again")

# -----------------------------------------------------
# Main Function
# -----------------------------------------------------

def main():
    with sync_playwright() as p:
        items = load_items_list()
        
        log_file = constant.EXCEL_OUTPUT_FILE_PATH + current_time_text()
        
        # page = login(p)
        # Now logged in

        cur_order_id = configs['ORDER_QUEUE'] 


        print(cur_order_id)

        print("Test End")
        sys.exit()
        
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

def start_order():
    start_time = time.time()

    print("Starting .. ")
    print("-." * 30)

    main()

    print("-." * 30)
    print("Done .. ")

    time_difference = time.time() - start_time
    print(f'Scraping time: %.2f seconds.' % time_difference)
    
    print("\n\n\n\n")

# ________________________________________________________________________________
configs = load_config()

if __name__ == "__main__":
    start_order()
    print(f"Automatically Start Ordering in {configs['SCHEDULE_DELAY']} minutes")
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