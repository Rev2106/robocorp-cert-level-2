from robocorp.tasks import task
from robocorp import browser
from robocorp import log
from RPA.Tables import Tables
from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.FileSystem import FileSystem
from RPA.Assistant import Assistant

#unattended = False
#testmode = False
website_url = "https://robotsparebinindustries.com/#/robot-order"
receipts_dir = "output/receipts"
receipts_zip = "output/receipts.zip"

@task()
def order_robots_from_RobotSpareBin_unattended():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Runs in unattended mode, which assumes the order site URL.
    """
    url = website_url
    main(url, False)

@task()
def order_robots_from_RobotSpareBin_attended():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Runs in attended mode, which asks for the URL.
    """
    url = user_input_task()
    main(url, True)

def user_input_task():
    assistant = Assistant()
    assistant.add_heading("Input from user")
    assistant.add_text("Enter URL for robot ordering website")
    assistant.add_text_input("text_input", placeholder="Please enter URL", default=website_url)
    assistant.add_submit_buttons("Submit", default="Submit")
    result = assistant.run_dialog()
    url = result.text_input
    return url

def main(url, attended):
    """
    Clears old receipts from previous run.
    Opens website to order the bots.
    Downloads Excel list containing the orders.
    Loops through each order in the list and uses the site to submit the order.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    delete_old_receipts()
    open_robot_order_website(url, attended)
    orders = get_orders()
    for order in orders:
        print(order)
        #log.debug(order)
        close_annoying_modal()
        fill_the_form(order)
    archive_receipts()

def delete_old_receipts():
    """ deletes the receipts folder if existing """
    lib = FileSystem()
    if lib.does_directory_exist(receipts_dir):
        lib.remove_directory(receipts_dir, True)
    lib.create_directory(receipts_dir)
    if lib.does_file_exist(receipts_zip):
        lib.remove_file(receipts_zip)

def open_robot_order_website(url, testmode=False):
    """ Opens the ordering website """
    if testmode:
        browser.configure(
            slowmo=100,
        )
    browser.goto(url)

def get_orders():
    """ Gets the CSV file with order information and returns it as a table """
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", target_file="output/orders.csv", overwrite=True)
    library = Tables()
    orders = library.read_table_from_csv("output/orders.csv")
    return orders

def close_annoying_modal():
    """ Closes the initial modal when loading the website """
    page = browser.page()
    page.wait_for_selector("#root")
    if page.get_by_role("button", name="OK").is_visible():
        page.get_by_role("button", name="OK").click()
    #page.click("text=Yep")
    #page.click("text=I guess so...")

def fill_the_form(order):
    """ Fills the form with order info """
    page = browser.page()
    """
    page.pause()
    page.get_by_label("Head:").select_option("1")
    page.get_by_label("Roll-a-thor body").check()
    page.get_by_placeholder("Enter the part number for the").fill("2")
    page.get_by_placeholder("Shipping address").fill("123 main st")
    page.get_by_role("button", name="Preview").click()
    page.get_by_role("button", name="Order").click()
    page.get_by_role("button", name="Order another robot").click()
    """
    page.locator("#head").select_option(order['Head'])
    page.locator("input[name=\"body\"][value=\""+order['Body']+"\"]").check()
    page.locator("input[type=number]").fill(order['Legs'])
    page.locator("#address").fill(order['Address'])
    page.locator("#preview").click()
    while page.locator("#order").is_visible():
        page.locator("#order").click()
    receipt_file = store_receipt_as_pdf(order['Order number'])
    image_file = screenshot_robot(order['Order number'])
    embed_screenshot_to_receipt(image_file, receipt_file)
    if page.locator("#order-another").is_visible():
        page.locator("#order-another").click()
    else:
        log.critical("failed to find Order Another button")
        raise "failed to find Order Another button"
    
def store_receipt_as_pdf(order_number):
    """ converts receipt to pdf """
    filename = receipts_dir + "/order-"+order_number+".pdf"
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    pdf = PDF()
    pdf.html_to_pdf(receipt_html, filename)
    return filename

def screenshot_robot(order_number):
    """ takes screenshot of receipt """
    filename = receipts_dir + "/order-"+order_number+".png"
    page = browser.page()
    page.locator("#robot-preview").screenshot(path=filename)
    return filename

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """ embeds screenshot in receipt pdf """
    pdf = PDF()
    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True
    )

def archive_receipts():
    """ archives the PDF files into a single zip file """
    lib = Archive()
    lib.archive_folder_with_zip(receipts_dir, receipts_zip, include='*.pdf')
