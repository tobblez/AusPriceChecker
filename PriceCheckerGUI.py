from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
from pathlib import Path
import os
import sys
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QApplication
from PyQt5.QtCore import *
import pyshortcuts
from PyQt5 import QtWidgets
from PyQt5 import QtCore
import traceback

version = "1.10"
startUpDir = "{}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\".format(Path.home())
configFolder = "{}\\AppData\\Roaming\\PriceChecker\\".format(Path.home())
scriptFolder = "{}\\".format(os.getcwd())
scriptLocation = "{}\\PriceCheckerGUI.exe".format(scriptFolder)
historyFile = configFolder + "history.txt"
websiteFile = configFolder + "websites.txt"
finishedLoading = False
allowedSites = ("bunnings.com.au",
                "jbhifi.com.au",
                "supercheapauto.com.au",
                "spearfishing.com.au",
                "msy.com.au",
                "review-australia.com",
                "woolworths.com.au",
                "umart.com.au",
                "scubadiving.com.au",
                "fantasticfurniture.com.au",
                "harveynorman.com.au",
                "amartfurniture.com.au",
                "rebelsport.com.au",
                "kogan.com",
                "anacondastores.com",
                "bigw.com.au",
                "amanstoyshop.com.au",
                "amazon.com.au",
                "kathmandu.com.au",
                "chemistwarehouse.com.au")


class Gui(QtWidgets.QMainWindow):

    listUpdating = False

    def __init__(self):
        super(Gui, self).__init__()

        try:
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)
            self.setTable()
            self.setInfoPage()
            self.ui.saveStatusLabel.setText("")
            self.ui.statusLabel.setText("")
            self.setWindowTitle("Aus Price Checker {}".format(version))
            self.ui.tabWidget.setCurrentIndex(0)
            self.loadHistory()
            self.setWindowIcon(QIcon(scriptFolder + 'australiaflag_icon.ico'))
            with open("{}stylesheet.css".format(scriptFolder), 'r') as f:
                stylesheet = f.read()

                self.setStyleSheet(stylesheet)
            self.show()

            self.checkprice = CheckPrice()
            self.checkprice.start()

            self.checkprice.priceSignal.connect(self.updateList)
            self.checkprice.statusUpdateSignal.connect(self.updateStatus)
            self.checkprice.websiteListSignal.connect(self.updateWebsites)
            self.ui.saveButton.clicked.connect(self.saveWebsites)
            self.ui.refreshButton.clicked.connect(self.restart)
            self.ui.autostartBox.stateChanged.connect(self.setAutostart)
            self.ui.openAppDataButton.clicked.connect(self.openConfigFolder)
            self.ui.openStartupFolderButton.clicked.connect(self.openStartUpFolder)
            self.ui.tableWidget.clicked.connect(self.resetHistory)

        except Exception as e:
            print(f"###01 {e}")

    def setInfoPage(self):
        """
        Function used to add the allowed sites to the text box on the info page with some formatting
        :return:
        """

        try:
            infoString = ""

            for i, site in enumerate(allowedSites, 1):
                infoString += "{}. www.{}\n".format(i, site)

            self.ui.plainTextEdit.setPlainText(infoString)
        except Exception as e:
            print("###2 " + e)


    def resetHistory(self, item):
        """
        Function used to reset the price history for a selected item in the list. When user clicks on 'Reset Price'
        in the table, a popup will appear asking to confirm, if yes is selected the history file is loaded, and the
        history under the selected item name is cleared.
        :param item:
        :return:
        """
        # Reset column = 5

        try:
            cellContent = item.data()
            cellColumn = item.column()
            cellRow = item.row()
            selectedName = self.ui.tableWidget.item(cellRow, 1).text()
            selectedBrand = self.ui.tableWidget.item(cellRow, 0).text()
            historyReference = "{} ### {}".format(selectedBrand, selectedName)

            popUp = QMessageBox()
            popUp.setWindowTitle("Reset Price History")
            popUp.setText("Are you sure you want to reset the price history for\n{}?".format(selectedName))
            popUp.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            historyData = {}

            global finishedLoading

            if cellColumn == 5 and finishedLoading is True:
                popUp.exec()

            else:
                return

            if popUp.clickedButton().text() == "&Yes":
                with open(historyFile, 'r') as f:
                    historyData = json.loads(f.read())

                    historyData['products'][historyReference] = []

                # Save data to file
                with open(historyFile, 'w') as f:
                    f.write(json.dumps(historyData, indent=4))

                self.restart()

        except Exception as e:
            print(f"###01 {e}")

    def openStartUpFolder(self):
        """
        Simple function to open up the folder where the AutoStart link file is located when the "Open Startup Folder"
        button is clicked.
        :return:
        """
        try:
            os.startfile(startUpDir)
        except Exception as e:
            print(f"###02 {e}")

    def openConfigFolder(self):
        """
        Simple function to open up the folder where the website.txt and history.txt files are located when the
        "Open Config Folder" button is clicked.
        :return:
        """
        try:
            os.startfile(configFolder)
        except Exception as e:
            print(f"###03 {e}")

    def setAutostart(self):
        """
        Function used to set/unset the application autostarting on Windows login. If the checkbox is ticked, a link
        to the program is created in the %AppData%\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\, if unselected
        any link files in the folder for the program are deleted.
        :return:
        """

        try:
            if self.ui.autostartBox.isChecked():
                pyshortcuts.make_shortcut(script=scriptLocation, name="PriceChecker", desktop=False,
                                          icon=scriptFolder + 'australiaflag_icon.ico', folder=startUpDir)
                self.ui.autostartBox.setDisabled(True)
                self.checkprice.sleepfunc(1)
                self.ui.autostartBox.setDisabled(False)

                if "PriceChecker.lnk" in os.listdir(startUpDir):
                    self.updateStatus("Startup shortcut created successfully")
                else:
                    self.updateStatus("Issue creating: {}PriceChecker.lnk".format(startUpDir))

            if self.ui.autostartBox.isChecked() is False:
                os.remove("{}PriceChecker.lnk".format(startUpDir))
                self.ui.autostartBox.setDisabled(True)
                self.checkprice.sleepfunc(1)
                self.ui.autostartBox.setDisabled(False)
                if "PriceChecker" not in os.listdir(startUpDir):
                    self.updateStatus("Startup shortcut deleted successfully")
                else:
                    self.updateStatus("Issue deleting: {}PriceChecker.lnk".format(startUpDir))
        except Exception as e:
            print(f"###04 {e}")

    def restart(self):
        """
        Function used to clear the table of loaded prices and reload the information.
        :return:
        """
        try:
            self.ui.refreshButton.setDisabled(True)
            self.ui.tableWidget.clearContents()
            self.ui.tableWidget.setRowCount(0)
            self.checkprice.start()
            self.checkprice.sleepfunc(2)
            self.ui.refreshButton.setDisabled(False)
        except Exception as e:
            print(f"###05 {e}")

    def updateWebsites(self, siteList):
        """
        Function used to add the list of websites from the websites.txt file to the GUI website textbox.
        :param siteList:
        :return:
        """
        try:
            text = ""
            for site in siteList:
                text += site

            self.ui.websiteList.setText(text)
        except Exception as e:
            print(f"###06 {e}")

    def loadHistory(self):
        """
        Function used to load the history file outside the initial loading.
        :return:
        """
        try:
            global scriptFolder

            if os.path.exists(configFolder) is False:
                os.mkdir(configFolder)
                self.updateStatus("Creating folder - {}".format(configFolder))

            if "PriceChecker.lnk" in os.listdir(startUpDir):
                self.ui.autostartBox.setChecked(True)
            else:
                self.ui.autostartBox.setChecked(False)

            try:
                with open(historyFile, 'r') as f:
                    try:
                        tempDict = json.load(f)
                        doInitialSetup = tempDict['config']['autoStartConfigured']
                        scriptFolder = tempDict['config']['installationDirectory']
                    except json.decoder.JSONDecodeError:
                        print("Error loading config file")

            except FileNotFoundError:
                print("Error loading config file")
        except Exception as e:
            print(f"###07 {e}")

    def setTable(self):
        """
        Function used to setup the table on the main page.
        :return:
        """
        try:
            table = self.ui.tableWidget
            windowWidth = table.width()

            table.setHorizontalHeaderLabels(['Source', 'Name', 'Current\nPrice', 'Highest\nPrice', 'Change', 'Price Reset'])

            table.setColumnWidth(0, int(windowWidth * 0.12))
            table.setColumnWidth(1, int(windowWidth * 0.50))
            table.setColumnWidth(2, int(windowWidth * 0.09))
            table.setColumnWidth(3, int(windowWidth * 0.09))
            table.setColumnWidth(4, int(windowWidth * 0.09))
            table.setColumnWidth(5, int(windowWidth * 0.09))
            table.setColumnWidth(6, int(windowWidth * 0.05))

        except Exception as e:
            print(f"###08 {e}")

    def updateList(self, data):
        """
        Function used to update the table with a new row of data containing item information.
        :param data:
        :return:
        """

        # emitInfo = [brand, item, currentPrice, maxPrice, change]

        try:
            table = self.ui.tableWidget
            rowPos = table.rowCount()
            table.insertRow(rowPos)

            changecheck = float(data[4][1:])

            if ("No websites detected" not in str(data[1])) or ("Error" not in str(data[0])):
                data.append('Reset')

            for i, info in enumerate(data):
                table.setItem(rowPos, i, QTableWidgetItem(info))
                if i != 1:
                    table.item(rowPos, i).setTextAlignment(Qt.AlignCenter)

                if changecheck < 0:
                    table.item(rowPos, i).setBackground(QColor('#76EE00'))
                    table.item(rowPos, i).setForeground(QColor(Qt.black))

                if "Error" in str(data[0]) or changecheck > 0:
                    table.item(rowPos, i).setBackground(QColor('#FA8072'))
                    table.item(rowPos, i).setForeground(QColor(Qt.black))
        except Exception as e:
            print(f"###09 {e}")

    def updateStatus(self, website):
        """
        Function used to update the status label at the bottom of the main page.
        :param website:
        :return:
        """
        try:
            self.ui.statusLabel.setText(website)
        except Exception as e:
            print(f"###10 {e}")

    def saveWebsites(self):
        """
        Function used to save websites entered in the website tab.
        :return:
        """
        try:
            data = self.ui.websiteList.toPlainText()
            with open(websiteFile, 'w') as f:
                f.write(data)

            self.ui.saveStatusLabel.setText("Changes saved!")
            self.checkprice.sleepfunc(1)
            self.ui.saveStatusLabel.setText("")
        except Exception as e:
            print(f"###11 {e}")


class CheckPrice(QThread):

    try:
        priceSignal = pyqtSignal(list)
        websiteListSignal = pyqtSignal(list)
        popupSignal = pyqtSignal(str)
        statusUpdateSignal = pyqtSignal(str)

        productHistory = {}
        today = datetime.now()
        todayDate = today.strftime('%d%b%y').upper()
        currentProducts = []
    except Exception as e:
        print(f"###12 {e}")

    def __init__(self):
        try:
            super(CheckPrice, self).__init__()

            self.start()
        except Exception as e:
            print(f"###13 {e}")

    def run(self):
        try:
            self.loadhistory()
            self.getproducts()
            self.savehistory()
        except Exception as e:
            print(f"###14 {e}")

    def sleepfunc(self, secs):
        try:
            """
            Function used as a thread-safe sleep function, can be called from anywhere in the program to sleep functions
            that won't freeze the GUI as a whole.
    
            :param secs:
            :return:
            """

            loop = QEventLoop()
            QTimer.singleShot(secs*1000, loop.quit)
            loop.exec()
        except Exception as e:
            print(f"###15 {e}")

    def loadhistory(self):
        """
        This function attempts to open the history file, if it does not exist it will create a blank file with
        the default dictionary for saving data. If the history file already exists, it will load the history from the
        file into the GLOBAL productHistory{} dictionary for use throughout the program.

        :return:
        """
        try:
            try:
                open(historyFile, 'r')
            except FileNotFoundError:
                open(historyFile, 'w')

            with open(historyFile, 'r') as f:
                try:
                    tempDict = json.load(f)
                except json.decoder.JSONDecodeError:
                    tempDict = {'config': {'autoStartConfigured': True, 'installationDirectory': scriptFolder}, 'products': {}}

                self.productHistory.update(tempDict)
        except Exception as e:
            print(f"###16 {e}")

    def getproducts(self):
        """
        This function reads the websites.txt file and passes each URL to the loadsite() function with the current
        loaded website increment number and total number of websites in the file.

        :return:
        """
        try:
            siteCount = 0
            incCount = 0
            validSites = []

            try:
                open(websiteFile, 'r')
            except FileNotFoundError:
                with open(websiteFile, 'w') as f:
                    f.write("")

            with open(websiteFile, 'r') as f:

                for url in f:
                    if url[0] != '#' and len(url) > 10:
                        for validUrl in allowedSites:
                            if validUrl in url:
                                validSites.append(str(url))
                                siteCount += 1

                if siteCount == 0:
                    emitInfo = ["", "No websites detected - click \'Websites\' tab to add more", "", "", ""]

                    self.priceSignal.emit(emitInfo)

                    print("No websites detected in websites.txt")
                    return

            self.websiteListSignal.emit(validSites)

            global finishedLoading
            finishedLoading = False
            for incCount, url in enumerate(validSites, 1):

                url = url.strip()
                webStatus = "{}/{}. Loading: {:.100}...".format(incCount-1, siteCount, url)
                self.statusUpdateSignal.emit(webStatus)
                self.loadsite(url, incCount, siteCount)

            self.statusUpdateSignal.emit("{}/{} Websites loaded successfully".format(incCount, len(validSites)))
            finishedLoading = True

        except Exception as e:
            print(f"###17 {e}")

    def loadsite(self, url, incCount, siteCount):
        """
        This function takes the URL, increment count and total website count from getproducts() and loads the URL
        using the requests module with the predefined User-Agent. The content from the site is then parsed into a
        Soup module object and the URL is used to determine which individual website function to use to extract the
        item name and item price.

        :param url:
        :param incCount:
        :param siteCount:
        :return:
        """

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
            }

            try:
                page = requests.get(url, headers=headers, timeout=20)

                if page.status_code != 200:
                    error = "{}/{} Error loading website: {}".format(incCount, siteCount, url)
                    self.statusUpdateSignal.emit(error)
                    emitInfo = ["Error - HTTP {}".format(page.status_code), str(url), "", "", ""]
                    self.priceSignal.emit(emitInfo)
                    return

                soup = BeautifulSoup(page.text, 'html.parser')

                # Referencing allowedSites global variable
                if allowedSites[0] in str(url):
                    self.bunnings(soup)

                elif allowedSites[1] in str(url):
                    self.jbhifi(soup)

                elif allowedSites[2] in str(url):
                    self.supercheapauto(soup)

                elif allowedSites[3] in str(url):
                    self.spearfishing(soup)

                elif allowedSites[4] in str(url):
                    self.msy(soup)

                elif allowedSites[5] in str(url):
                    self.review(soup)

                elif allowedSites[6] in str(url):
                    self.woolwoths(soup)

                elif allowedSites[7] in str(url):
                    self.umart(soup)

                elif allowedSites[8] in str(url):
                    self.scubadiving(soup)

                elif allowedSites[9] in str(url):
                    self.fantasticfurniture(soup)

                elif allowedSites[10] in str(url):
                    self.harveynorman(soup)

                elif allowedSites[11] in str(url):
                    self.amartfurniture(soup)

                elif allowedSites[12] in str(url):
                    self.rebelsport(soup)

                elif allowedSites[13] in str(url):
                    self.kogan(soup)

                elif allowedSites[14] in str(url):
                    self.annaconda(soup)

                elif allowedSites[15] in str(url):
                    self.bigw(soup)

                elif allowedSites[16] in str(url):
                    self.amanstoyshop(soup)

                elif allowedSites[17] in str(url):
                    self.amazon(soup)

                elif allowedSites[18] in str(url):
                    self.kathmandu(soup)

                elif allowedSites[19] in str(url):
                    self.chemistwarehouse(soup)

                else:
                    print("{} not a valid domain".format(str(url)))

            except Exception as e:
                print("Location 1 - {}\n{}".format(e, traceback.format_exc()))
                error = "{}/{} Error loading website: {}".format(incCount, siteCount, url)
                self.statusUpdateSignal.emit(error)
                # emitInfo = [brand, item, currentPrice, maxPrice, change]
                emitInfo = ["Error", str(url), "", "", ""]

                self.priceSignal.emit(emitInfo)
                return
        except Exception as e:
            print(f"###18 {e}")

##################### Individual Website Functions ########################################

    def chemistwarehouse(self, soup):

        try:
            data = soup.find(class_="product__price").string.strip()
            title = soup.find("h1").text.strip()

            productPrice = data[1:]
            productName = "Chemist Warehouse ### {}".format(title)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###19 {e}")
            self.savedata("Error ### Chemist Warehouse", 0)

    def kathmandu(self, soup):

        try:
            data = soup.find(class_="price").string.strip()
            title = soup.find("h1").text.strip()

            productPrice = data[1:]
            productName = "Kathmandu ### {}".format(title)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###20 {e}")
            self.savedata("Error ### Kathmandu", 0)

    def amazon(self, soup):

        try:
            data = soup.find("span", {"id": "price_inside_buybox"})
            price = data.string.strip()[1:]
            title = soup.find("h1").text.strip()

            productPrice = price
            productName = "Amazon Aus ### {}".format(title)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###21 {e}")
            self.savedata("Error ### Amazon", 0)

    def amanstoyshop(self, soup):

        try:
            data = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_RetailPrice"})
            title = soup.find("span", {"id": "ctl00_pageTitle_label"})

            productPrice = str(data.string[1:])
            productName = "A Man's ToyShop ### {}".format(title.string)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###22 {e}")
            self.savedata("Error ### A Man's Toy Shop", 0)

    def bigw(self, soup):

        try:
            data = soup.find_all("script")[1]
            javscript_data = str(data.string).split("window.dataLayer = window.dataLayer || [];")
            javscript_data = str(javscript_data[1].strip())[15:-2].replace("\'", "\"")

            json_data = json.loads(str(javscript_data))
            Name = json.dumps(json_data['ecommerce']['detail']['products'][0]['name']).strip()
            Price = json.dumps(json_data['ecommerce']['detail']['products'][0]['price']).strip()

            productPrice = str(Price).replace("\"", "")
            productName = "BigW ### {}".format(Name.replace("\"", ""))

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###23 {e}")
            self.savedata("Error ### BigW", 0)

    def annaconda(self, soup):

        try:
            data = soup.find(class_="price price-now")
            price = data.find(class_="amount").string.strip()
            title = soup.find(class_="pdp-title").string.strip()

            productPrice = str(price)[1:]
            productName = "Annaconda ### {}".format(title)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###24 {e}")
            self.savedata("Error ### Annaconda", 0)

    def kogan(self, soup):

        try:
            data = soup.find("meta",  property="product:price:amount")['content'].strip()
            title = soup.find("meta",  property="og:title")['content'].strip()

            productPrice = str(data)
            productName = "Kogan ### {}".format(title)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###25 {e}")
            self.savedata("Error ### Kogan", 0)

    def rebelsport(self, soup):

        try:
            data = soup.find(class_="price-sales").text.strip()
            title = soup.find(class_="product-name").text.strip()

            productPrice = str(data)[1:]
            productName = "Rebel Sport ### {}".format(title)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###26 {e}")
            self.savedata("Error ### Rebel Sport", 0)

    def amartfurniture(self, soup):

        try:
            data = soup.find(class_="value").text.strip()
            title = soup.find("h1").text.strip()
            title2 = soup.find(class_="product-description mb-2").text.strip()

            productPrice = str(data)[1:]
            productName = "Amart Furniture ### {} - {}".format(title, title2)

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###27 {e}")
            self.savedata("Error ### Amart Furniture", 0)

    def harveynorman(self, soup):

        try:
            data = soup.find("div", {"id": "product-view-price"})
            data = data.find(class_="price").text.strip()[1:]

            title = soup.find(class_="product-name").text.strip()

            productPrice = str(data)
            productName = "Harvey Norman ### {}".format(title).strip()

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###28 {e}")
            self.savedata("Error ### Harvey Norman", 0)

    def fantasticfurniture(self, soup):

        try:
            title = soup.find("h1").string.strip()
            data = soup.find('input', {'name': 'DisplayedPrice'})['value']

            productName = "Fantastic Furniture ### {}".format(title).strip()
            productPrice = str(data).strip()

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###29 {e}")
            self.savedata("Error ### Fantastic Furniture", 0)

    def scubadiving(self, soup):

        try:
            title = soup.find("h1", itemprop="name").string.strip()

            data = soup.find("p", itemprop="price", attrs={'itemprop': 'price'})

            productPrice = str(data.string.strip())[1:]
            productName = str("ScubaDiving ### {}".format(title))

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###30 {e}")
            self.savedata("Error ### Scuba Diving", 0)

    def umart(self, soup):

        try:
            title = soup.find("h1", attrs={'itemprop': 'name'})

            data = soup.find("span", attrs={'itemprop': 'price'})
            productPrice = str(data['content']).strip()
            productName = "Umart ### {}".format(title.string).strip()

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###31 {e}")
            self.savedata("Error ### U-Mart", 0)

    def woolwoths(self, soup):

        try:
            data = soup.prettify()
            data = data.splitlines()

            for i, line in enumerate(data):
                if "\"price\":" in line:
                    data = str(line).strip()
                    break

            productData = json.loads(data)
            productName = str("Woolworths ### {}".format(productData['name']).strip())
            productPrice = str(productData['offers']['price']).strip()

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###32 {e}")
            self.savedata("Error ### Woolworths", 0)

    def bunnings(self, soup):

        try:
            data = soup.prettify()
            data = data.splitlines()

            for line in data:
                if "\"price\":\"" in line:
                        data = str(line).strip()
                        break

            json_data = data.split("var productDetailsData = ")[1][:-1]
            productData = json.loads(json_data)

            productName = str("Bunnings ### {}".format(productData['displayName']).strip())
            productPrice = str(productData['price']).strip()

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###33 {e}")
            self.savedata("Error ### Bunnings", 0)

    def jbhifi(self, soup):

        try:
            title = soup.find("h1", attrs={'itemprop': 'name'})

            data = soup.find("meta", attrs={'itemprop': 'price'})
            productPrice = str(data['content']).strip()
            productName = "JB Hifi ### {}".format(title.string).strip()

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###34 {e}")
            self.savedata("Error ### JBHifi", 0)

    def supercheapauto(self, soup):

        try:
            title = soup.find(class_="product-name", itemprop="name")

            data = soup.find(class_="visually-hidden", attrs={'itemprop': 'price'})
            productPrice = str(data.text.strip())
            productName = str("SCA ### {}".format(title.string.strip()))

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###35 {e}")
            self.savedata("Error ### Super Cheap Auto", 0)

    def spearfishing(self, soup):

        try:
            title = soup.find("h1", itemprop="name").string.strip()

            data = soup.find("p", itemprop="price", attrs={'itemprop': 'price'})

            productPrice = str(data.string.strip())[1:]
            productName = str("SpearFishing ### {}".format(title))

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###36 {e}")
            self.savedata("Error ### SpearFishing", 0)

    def msy(self, soup):

        try:
            data = soup.find(class_="current-price")
            productPrice = data.text[2:].strip()

            title = soup.find("h1", itemprop="name")
            productName = str("MSY ### {}".format(title.string.strip()))

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###37 {e}")
            self.savedata("Error ### MSY", 0)

    def review(self, soup):

        try:
            title = soup.find(class_="product-name").string
            productName = str("Review ### {}".format(title).strip())

            data = soup.find(class_="price-sales")
            productPrice = data.string.strip()[1:]

            self.savedata(productName, productPrice)
        except Exception as e:
            print(f"###38 {e}")
            self.savedata("Error ### Review", 0)

###################### End of Individual Website Functions ###############################

    def savedata(self, name, price):
        """
        This function is passed the name and price of item from the individual website functions, it will append
        the name and price to the GLOBAL productHistory dictionary using the name of the item as a key.

        The name of the item from the website is then passed to checksavings() function where it will calculate
        the difference between the max and min prices.

        :param name: The name of the item, prefixed with the Brand and three hashes used as a delimiter.
        :param price:
        :return:
        """
        try:
            try:
                self.productHistory['products'][name].append((price, self.todayDate))
            except KeyError:
                self.productHistory['products'][name] = []
                self.productHistory['products'][name].append((price, self.todayDate))

            self.currentProducts.append(name)

            self.checksavings(name)
        except Exception as e:
            print(f"###39 {e}")

    def checksavings(self, name):
        """
        Passed the name of the item from the savedata() function, this function will loop through the main
        productHistory GLOBAL dictionary to find a reference to the name of the item and extract out the minimum and
        maximum values where it will calculate the savings.

        :param name:
        :return:
        """

        try:
            productCount = 0

            for key in self.productHistory['products'].keys():

                # if name in self.currentProducts:
                if name in key:
                    productCount += 1
                    priceList = []

                    for priceData in self.productHistory['products'][name]:
                        priceList.append(priceData[0])

                    currentPrice = priceList[-1]
                    currentPriceDate = self.productHistory['products'][name][-1][1]
                    maxPrice = max(priceList)
                    maxPriceDate = self.productHistory['products'][name][priceList.index(maxPrice)][1]
                    minPrice = min(priceList)
                    minPriceDate = self.productHistory['products'][name][priceList.index(minPrice)][1]

                    change = str(float(currentPrice)-float(maxPrice))

                    brand = str(name).split("###")[0].strip()
                    item = str(name).split("###")[1].strip()
                    currentPrice = "${:.2f}".format(float(currentPrice))
                    maxPrice = "${:.2f}".format(float(maxPrice))
                    minPrice = "${:.2f}".format(float(minPrice))
                    change = "${:.2f}".format(float(change))

                    emitInfo = [brand, item, currentPrice, maxPrice, change]

                    self.priceSignal.emit(emitInfo)
        except Exception as e:
            print(f"###40 {e}")

    def savehistory(self):

        try:
            # Save data to file
            with open(historyFile, 'w') as f:
                f.write(json.dumps(self.productHistory, indent=4))
        except Exception as e:
            print(f"###41 {e}")


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        try:
            MainWindow.setObjectName("MainWindow")
            MainWindow.setWindowModality(QtCore.Qt.NonModal)
            MainWindow.setEnabled(True)
            MainWindow.resize(1000, 750)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
            MainWindow.setSizePolicy(sizePolicy)
            MainWindow.setMinimumSize(QtCore.QSize(1000, 750))
            MainWindow.setMaximumSize(QtCore.QSize(1000, 750))
            MainWindow.setWindowOpacity(1.0)
            MainWindow.setIconSize(QtCore.QSize(24, 24))
            MainWindow.setDocumentMode(False)
            MainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)
            MainWindow.setDockOptions(QtWidgets.QMainWindow.AllowTabbedDocks|QtWidgets.QMainWindow.AnimatedDocks)
            self.centralwidget = QtWidgets.QWidget(MainWindow)
            self.centralwidget.setObjectName("centralwidget")
            self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
            self.tabWidget.setGeometry(QtCore.QRect(10, 10, 981, 691))
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
            self.tabWidget.setSizePolicy(sizePolicy)
            self.tabWidget.setMinimumSize(QtCore.QSize(981, 691))
            self.tabWidget.setTabPosition(QtWidgets.QTabWidget.North)
            self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)
            self.tabWidget.setUsesScrollButtons(True)
            self.tabWidget.setDocumentMode(False)
            self.tabWidget.setObjectName("tabWidget")
            self.tab = QtWidgets.QWidget()
            self.tab.setObjectName("tab")
            self.tableWidget = QtWidgets.QTableWidget(self.tab)
            self.tableWidget.setGeometry(QtCore.QRect(10, 50, 961, 621))
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
            self.tableWidget.setSizePolicy(sizePolicy)
            self.tableWidget.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.tableWidget.setFrameShadow(QtWidgets.QFrame.Plain)
            self.tableWidget.setLineWidth(0)
            self.tableWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.tableWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
            self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
            self.tableWidget.setProperty("showDropIndicator", False)
            self.tableWidget.setDragDropOverwriteMode(False)
            self.tableWidget.setAlternatingRowColors(True)
            self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            self.tableWidget.setTextElideMode(QtCore.Qt.ElideRight)
            self.tableWidget.setShowGrid(False)
            self.tableWidget.setGridStyle(QtCore.Qt.NoPen)
            self.tableWidget.setWordWrap(False)
            self.tableWidget.setCornerButtonEnabled(False)
            self.tableWidget.setColumnCount(6)
            self.tableWidget.setObjectName("tableWidget")
            self.tableWidget.setRowCount(0)
            self.tableWidget.horizontalHeader().setVisible(True)
            self.tableWidget.horizontalHeader().setHighlightSections(False)
            self.tableWidget.horizontalHeader().setMinimumSectionSize(30)
            self.tableWidget.verticalHeader().setVisible(False)
            self.tableWidget.verticalHeader().setCascadingSectionResizes(False)
            self.tableWidget.verticalHeader().setHighlightSections(False)
            self.refreshButton = QtWidgets.QPushButton(self.tab)
            self.refreshButton.setGeometry(QtCore.QRect(840, 0, 121, 41))
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.refreshButton.sizePolicy().hasHeightForWidth())
            self.refreshButton.setSizePolicy(sizePolicy)
            self.refreshButton.setObjectName("refreshButton")
            self.label_2 = QtWidgets.QLabel(self.tab)
            self.label_2.setGeometry(QtCore.QRect(20, 0, 801, 41))
            self.label_2.setObjectName("label_2")
            self.tabWidget.addTab(self.tab, "")
            self.tab_2 = QtWidgets.QWidget()
            self.tab_2.setObjectName("tab_2")
            self.websiteList = QtWidgets.QTextEdit(self.tab_2)
            self.websiteList.setGeometry(QtCore.QRect(10, 70, 961, 601))
            self.websiteList.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.websiteList.setFrameShadow(QtWidgets.QFrame.Plain)
            self.websiteList.setLineWidth(0)
            self.websiteList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.websiteList.setAcceptRichText(False)
            self.websiteList.setCursorWidth(1)
            self.websiteList.setObjectName("websiteList")
            self.websiteList.setLineWrapMode(self.websiteList.NoWrap)
            self.label = QtWidgets.QLabel(self.tab_2)
            self.label.setGeometry(QtCore.QRect(10, 0, 671, 21))
            self.label.setObjectName("label")
            self.label_3 = QtWidgets.QLabel(self.tab_2)
            self.label_3.setGeometry(QtCore.QRect(10, 20, 321, 16))
            self.label_3.setObjectName("label_3")
            self.label_4 = QtWidgets.QLabel(self.tab_2)
            self.label_4.setGeometry(QtCore.QRect(10, 40, 691, 21))
            self.label_4.setObjectName("label_4")
            self.saveButton = QtWidgets.QPushButton(self.tab_2)
            self.saveButton.setGeometry(QtCore.QRect(840, 0, 121, 41))
            font = QFont()
            font.setBold(False)
            font.setWeight(50)
            self.saveButton.setFont(font)
            self.saveButton.setDefault(False)
            self.saveButton.setFlat(False)
            self.saveButton.setObjectName("saveButton")
            self.saveStatusLabel = QtWidgets.QLabel(self.tab_2)
            self.saveStatusLabel.setGeometry(QtCore.QRect(710, 0, 121, 41))
            self.saveStatusLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
            self.saveStatusLabel.setObjectName("saveStatusLabel")
            self.tabWidget.addTab(self.tab_2, "")
            self.tab_3 = QtWidgets.QWidget()
            self.tab_3.setObjectName("tab_3")
            self.label_5 = QtWidgets.QLabel(self.tab_3)
            self.label_5.setGeometry(QtCore.QRect(10, 50, 211, 31))
            self.label_5.setObjectName("label_5")
            self.plainTextEdit = QtWidgets.QPlainTextEdit(self.tab_3)
            self.plainTextEdit.setGeometry(QtCore.QRect(10, 90, 961, 571))
            self.plainTextEdit.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.plainTextEdit.setFrameShadow(QtWidgets.QFrame.Plain)
            self.plainTextEdit.setReadOnly(True)
            self.plainTextEdit.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
            self.plainTextEdit.setObjectName("plainTextEdit")
            self.openAppDataButton = QtWidgets.QPushButton(self.tab_3)
            self.openAppDataButton.setGeometry(QtCore.QRect(10, 10, 141, 31))
            self.openAppDataButton.setObjectName("openAppDataButton")
            self.openStartupFolderButton = QtWidgets.QPushButton(self.tab_3)
            self.openStartupFolderButton.setGeometry(QtCore.QRect(170, 10, 141, 31))
            self.openStartupFolderButton.setObjectName("openStartupFolderButton")
            self.tabWidget.addTab(self.tab_3, "")
            self.layoutWidget = QtWidgets.QWidget(self.centralwidget)
            self.layoutWidget.setGeometry(QtCore.QRect(20, 710, 951, 31))
            self.layoutWidget.setObjectName("layoutWidget")
            self.horizontalLayout = QtWidgets.QHBoxLayout(self.layoutWidget)
            self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
            self.horizontalLayout.setObjectName("horizontalLayout")
            self.statusLabel = QtWidgets.QLabel(self.layoutWidget)
            self.statusLabel.setTextFormat(QtCore.Qt.PlainText)
            self.statusLabel.setObjectName("statusLabel")
            self.horizontalLayout.addWidget(self.statusLabel)
            self.autostartBox = QtWidgets.QCheckBox(self.layoutWidget)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(self.autostartBox.sizePolicy().hasHeightForWidth())
            self.autostartBox.setSizePolicy(sizePolicy)
            self.autostartBox.setObjectName("autostartBox")
            self.horizontalLayout.addWidget(self.autostartBox)
            MainWindow.setCentralWidget(self.centralwidget)

            self.retranslateUi(MainWindow)
            self.tabWidget.setCurrentIndex(0)
            QtCore.QMetaObject.connectSlotsByName(MainWindow)
        except Exception as e:
            print(f"###42 {e}")

    def retranslateUi(self, MainWindow):
        try:
            _translate = QtCore.QCoreApplication.translate
            MainWindow.setWindowTitle(_translate("MainWindow", "Aus Price Checker"))
            self.refreshButton.setText(_translate("MainWindow", "Refresh"))
            self.label_2.setText(_translate("MainWindow", "Items on special will be highlighted green"))
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "  Prices  "))
            self.label.setText(_translate("MainWindow", "<html><head/><body><p>Paste URLs to individual product pages below, lines starting with a # are ignored</p></body></html>"))
            self.label_3.setText(_translate("MainWindow", "Remove URLs from the list to stop them being updated"))
            self.label_4.setText(_translate("MainWindow", "<html><head/><body><p>See <span style=\" font-weight:600;\">Info </span>tab for currently supported websites, invalid URL\'s are removed on restart</p></body></html>"))
            self.saveButton.setText(_translate("MainWindow", "Save List Changes"))
            self.saveStatusLabel.setText(_translate("MainWindow", "SaveStatus"))
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "  Websites  "))
            self.label_5.setText(_translate("MainWindow", "Currently Supported Websites:"))
            self.openAppDataButton.setText(_translate("MainWindow", "Open Config Folder"))
            self.openStartupFolderButton.setText(_translate("MainWindow", "Open Startup Folder"))
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "  Info  "))
            self.statusLabel.setText(_translate("MainWindow", "Status Bar"))
            self.autostartBox.setText(_translate("MainWindow", "Autostart"))
        except Exception as e:
            print(f"###43 {e}")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        application = Gui()
        app.exec()
    except Exception as e:
        print(f"###44 {e}")

