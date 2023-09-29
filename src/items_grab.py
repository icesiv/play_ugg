import constant
import helpers
from bs4 import BeautifulSoup
import json
import helpers

import asyncio
from playwright.async_api import async_playwright


async def main():
    async def block_aggressively(route):
        if (route.request.resource_type in constant.RESOURCE_EXCLUSTIONS):
            await route.abort()
        else:
            await route.continue_()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()

        await page.set_viewport_size({"width": 1280, "height": 1080})
        # await page.route("**/*", block_aggressively)

        # login page
        print("<" * 30)
        print("login process start")
        await page.goto(constant.get_url('login'))
        await page.fill('input#userNameId', configs['USERNAME'])
        await page.fill('input#userPasswordId', configs['PASSWORD'])
        await page.click("button[type=submit]")

        await page.wait_for_selector('div.ugg_message')

        print("login success")
        print(">" * 30)
        # Now logged in

        full_url = constant.get_url("orderCenter")

        await page.goto(full_url)

        # await page.wait_for_selector('div.ugg_message')

        await asyncio.sleep(2)

        search_icon = await page.locator(".icon-hover-shadow .nav-icon")
        await search_icon.click()

        await asyncio.sleep(30)

        # Close the browser
        await browser.close()


# ________________________________________________________________________________


configs = helpers.load_config()

if __name__ == "__main__":
    start_time = helpers.current_time()

    print("Starting .. ")
    print("-" * 50)

    asyncio.run(main())

    print("-" * 50)
    print("Done .. ")

    time_difference = helpers.current_time() - start_time
    print(f'Scraping time: %.2f seconds.' % time_difference)
