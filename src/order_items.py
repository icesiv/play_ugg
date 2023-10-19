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
    try:
        with open(get_file(constant.CONFIG_PATH)) as f:
            config = json.load(f)
        
    except:
        print("Please create the config.json file.")
        sys.exit()

    return config

def new_order_queue():
    configs['ORDER_QUEUE'] = int(configs['ORDER_QUEUE']) + 1
    json_object = json.dumps(configs, indent=4)
 
    with open((get_file(constant.CONFIG_PATH)), 'w') as outfile:
        outfile.write(json_object)

    return configs['ORDER_QUEUE']

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

def wait(min , max =-1):
    if max == -1:
        max = min
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

    if not os.path.exists(constant.EXCEL_OUTPUT_FILE_PATH):
        try:
            os.makedirs(constant.EXCEL_OUTPUT_FILE_PATH)
            combined_df.to_excel(filename+".xlsx", index=False)
        except OSError as e:
            print(f"Error creating folder: {e}")
    else:
        combined_df.to_excel(filename+".xlsx", index=False)

def block_aggressively(route):
    RESOURCE_EXCLUSTIONS = ['image', 'font']
    
    if (route.request.resource_type in RESOURCE_EXCLUSTIONS):
        route.abort()
    else:
        route.continue_()

def format_float_string(value):
  value = float(value)
  if value < 10:
    return f"0{value:.1f}"
  else:
    return f"{value:.1f}"

def format_int_string(value):
  value = int(value)
  if value < 10:
    return f"0{value}"
  else:
    return f"{value}"

def is_float(string):
  try:
    float(string)
    return True
  except ValueError:
    return False

def is_int(string):
  return string.isdigit()

# -----------------------------------------------------
# confirm_order Function
# -----------------------------------------------------

def confirm_order(page,cur_order_id):
    page.goto(constant.get_url("cart"))

    try:
        page.wait_for_selector("(//header[@class='section-title'])[3]")
    except:
        print("Time out on cart page")
        raise Exception
            
    try:
        page.wait_for_selector(".products-wrap", timeout=2000 )
        print("Products are added to cart")
    except:
        print("============================ logs ===========================")
        print("Error: No product added to cart")
        print("============================================================")
        sys.exit()
     
    if(page.locator("//input[@value='IMMED']").is_checked()):
        print("Schedule for immediate delivery")
    else:
        print("Setting for immediate delivery")        
        page.click("(//label[@role='radio'])[1]")

        wait(2, 3)
        btns = page.locator(".el-message-box__btns")
        
        yes_button = btns.locator('button:has-text("Yes")')
        yes_button.click()
        wait(3, 4)   
    
    page.fill("//input[@placeholder='PO# Required']", configs["ORDER_KEY"] + str(cur_order_id))
    
    # REVIEW ORDER
    button_review = page.locator("(//span[text()='Review Order'])[1]")
    button_review.click()
    wait(3, 4)
    
    selector = '.dialog-header'
    
    try:
        element = page.wait_for_selector(selector, timeout=10000)
        inner_text = element.inner_text()
        if(inner_text=="Review Order"):
            print("All item avlable")
    except:
        print("Some item QTY not avlable")
        btns = page.locator("//div[@class='product-container']/following-sibling::div[1]")
        yes_button = btns.locator('button:has-text("Continue")')
        yes_button.click()
        wait(3, 4)
        
    #  CONFIRM ORDER
    try:
        btns = page.locator("//div[@class='order-notes']/following-sibling::div[1]")
        Place_button = btns.locator('button:has-text("Place Order")')
        Place_button.click()
        
        print("Waiting 15s for safty. DO NOT CLOSE")
        wait(15)
        print("================= Order Complete =================")
    except:
        print("============================= x =============================")
        print("Items in cart are not available. Will try to order next time.")
        print("============================= x =============================")
    
    #  ToDO Get Order ID
    
# -----------------------------------------------------
# prepare_order Function
# -----------------------------------------------------

def prepare_order(page, items, cur_order_id, log_file):
    for item in items:
        error = ""
        try:
          set_order(page, item['SKU'], str(item['SIZE']), int(item['QTY']))
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
                "ORDER_ID": configs["ORDER_KEY"] + str(cur_order_id),
                "time": current_time_text()
        }

        if error:
            data["status"] = "ERROR :" + error 
            print("\n" + "x" * 30)
            print(data["status"])
            print("x" * 30 + "\n" )
        else:
            data["status"] = f"Success.. {data['ORDER_ID']}"
            
        log_item([data], log_file)

# -----------------------------------------------------
# set_order Function
# -----------------------------------------------------
def clean_size_txt(s):
    if is_int(s):
        return format_int_string(s)
    if is_float(s):
        return format_float_string(s)
    return s

def set_order(page, item_code, size, qty):
    try:
        code_part = item_code.split("_")
        if(len(code_part) > 1):
            item_code = code_part[0]
            size = code_part[1]
    except:
        print(f"Invalid format SKU: {item_code}")
        raise InvalidItemException
    
    size = clean_size_txt(size)
    
    full_url = constant.get_url("search") + item_code
    page.goto(full_url)
    
    # wait(4,6)
    wait(2)
    
    try:
        page.wait_for_selector("(//span[@class='nav-item__title pointer']//span)[2]", timeout=220000)
    except:
        print(f"Time Out on search item {item_code}")
        raise InvalidItemException

    try:
        page.wait_for_selector('.product-item', timeout=10000)
    except:
        raise InvalidItemException
        
    page.click("//div[@class='el-tooltip enter-qty']")
    
    wait(3)
    # wait(6)
    
    # Get Size
    html = page.inner_html("(//div[@class='size-table']//div)[1]")
    soup = BeautifulSoup(html, 'html.parser')
    size_elements = soup.find_all('div', class_='item')
    sizes = [s.text.strip() for s in size_elements]
   
    found = False
    
    # Enter QTY
    for index, value in enumerate(sizes):
        if(value == size):
            input_fields = page.locator(f"(//input[@class='el-input__inner'])[{index + 1 }]")
            current_qty  = input_fields.input_value()
            found = True
            
            input_fields.fill(str(qty + int(current_qty)))
            page.keyboard.press("Tab")
            wait(1)
            cloce_btn = page.locator("//div[@class='header']/following-sibling::button[1]")
            cloce_btn.click()
              
            print(f"Adding to cart {item_code} size: {size}")
            print(f"{current_qty}(prv) + {qty}(new) = total {int(current_qty) + qty} pcs")
            break
        
    if not found:
        raise InvalidSizeException

    wait(1)
    print("-" * 30)

# -----------------------------------------------------
# login Function
# -----------------------------------------------------

def login(page):
    while True:
        ## login page
        print("<" * 30)
        print("login process start")
        
        try:
            page.goto(constant.get_url('login'), timeout=280000)
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

def clear_cart(page):
    print("Checking Cart...")
    page.goto(constant.get_url("cart"))

    try:
        page.wait_for_selector("(//header[@class='section-title'])[3]")
    except:
        print("Time out on cart page")
            
    try:
        page.wait_for_selector(".products-wrap", timeout=2000 )
        print("Products are added to cart")
    except:
        print("No product added to cart")
        print("-" * 20)
        return True
     
   
    print("Clearing Cart")        
    page.click(" (//button[contains(@class,'el-button title-font')])[2]")

    wait(2)
    btns = page.locator(".el-message-box__btns")
    
    yes_button = btns.locator('button:has-text("Yes")')
    yes_button.click()
    wait(3)   
     
    print("Cart Empty")  
    print("-" * 20)
    
# -----------------------------------------------------
# Main Function
# -----------------------------------------------------

def start_order():
    start_time = time.time()
    print("Starting .. ")
    
    try:
        with sync_playwright() as p:
            # browser = p.chromium.launch(headless=False)
            # browser = p.chromium.launch(headless=False, slow_mo=50)
            browser = p.chromium.launch()
        
            page = browser.new_page()
            page.set_viewport_size({"width": 1280, "height": 800})
            # # page.route("**/*", block_aggressively)
            
            page = login(page)
            
            items = load_items_list()
            log_file = constant.EXCEL_OUTPUT_FILE_PATH + "log_" + current_time_text()
           
            clear_cart(page)

            cur_order_id = new_order_queue() 
            prepare_order(page, items, cur_order_id, log_file)
            
            print(f"Placing order : {configs['ORDER_KEY']}{cur_order_id}")
            confirm_order(page,cur_order_id)

            browser.close()
    except Exception as e:
        print(e)
        print("Error logged.")
        
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
        
        sys.stdout.write(f"\rNext call in {int(rm)}:{int(rs-(configs['SCHEDULE_DELAY']*rm))}")
        sys.stdout.flush()
        
        schedule.run_pending()
        time.sleep(1)