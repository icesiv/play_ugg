# HOW TO RUN THIS SCRAPER

1. Download Python 3.6+ from [here](https://www.python.org/downloads/) and install [pip](https://www.geeksforgeeks.org/how-to-install-pip-on-windows/) and [virtualenv](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/).

2. Run the file `setup.bat` by double clicking it.

3. Copy the contents of `config_template.json` into a new file called `config.json` (must be on the same level as `config_template.json`). Input the corresponding values in this file. More info [below](#config-file-settings-explained).

4. Edit `excel_files/input.xlsx` and set your desired SKU, size and quantity.

5. Run the file `run_scraper.bat` by double clicking it to start the scraper.

6. Program outputs will be generated in `excel_files/logs`


# Config File Contents Explained

- `USERNAME` - Username used for login on the website
- `PASSWORD` - Password used for login on the website
