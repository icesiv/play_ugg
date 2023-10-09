import constant
import helpers

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd

class InvalidItemException(Exception):
    "Item not found"
    pass

class InvalidSizeException(Exception):
    "size not found for that Item"
    pass

def main():
    def load_items(file_name):
        try:
            df = pd.read_excel(file_name)
            dict_list = df.to_dict(orient='records')
            return(dict_list)
        except:
            print("Please check the input excel file.")
            return None
        
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
        helpers.wait(2, 3)
        
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

                helpers.wait(1, 2)
                break

        button = page.locator("//div[@class='header']/following-sibling::button[1]");
        button.click()
        
        if not found:
            raise InvalidSizeException


    with sync_playwright() as p:
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

        # load items from excel
        items = load_items(constant.EXCEL_INPUT_FILE_PATH)
        log_file = constant.EXCEL_OUTPUT_FILE_PATH + helpers.current_time_text()
        
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
                    "time": helpers.current_time_text()
            }

            if error:
                data["status"] = "ERROR :" + error 
            else:
                data["status"] = "Success.."
                
            log_item([data], log_file)


        browser.close()

# ________________________________________________________________________________
configs = helpers.load_config()

if __name__ == "__main__":
    start_time = helpers.current_time()

    print("Starting .. ")
    print("- . " * 30)

    main()

    print("- . " * 30)
    print("Done .. ")

    time_difference = helpers.current_time() - start_time
    print(f'Scraping time: %.2f seconds.' % time_difference)
