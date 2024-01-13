import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from products_design import Ui_MainWindow


class ScrapeThread(QThread):
    line_processed = pyqtSignal(str,int)
    finished_signal = pyqtSignal(list)

    def __init__(self, link):
        super().__init__()
        self.link = link

    def run(self):
        page_number = 1
        product_data = []
        count = 1
        while True:
            try:
                response = requests.get(f"{self.link}&page={page_number}")

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    items = soup.find_all('li', class_='grid__item')

                    if not items:
                        break

                    for item in items:
                        product_name = item.select_one('.card-information__text').get_text(strip=True)
                        price = item.select_one('.price-item--sale').get_text(strip=True)

                        product_data.append([product_name, price])

                        # Emit signal for each line processed
                        self.line_processed.emit(f' - {product_name} : {price}', count)
                        count += 1

                    page_number += 1
                else:
                    break
            except Exception as e:
                break

        self.finished_signal.emit(product_data)


class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.scrape_thread = None
        self.setupUi(self)
        self.color_error = 'background-color:#fa8f87'
        self.color_normal = 'color:#033FCB'
        self.button_export_to_excel.hide()
        self.button_get_data.clicked.connect(self.start_scraping)
        self.button_export_to_excel.clicked.connect(self.export_to_excel)
        self.button_about.clicked.connect(self.about)
        self.button_github.clicked.connect(self.github)

    def about(self):
        info = """
        Proqram  : Scraper 
        Versiya  : 1.0.1.0
        
        Sabuhi Alasgarov. Müəllif hüquqları qorunur © 2024
        Əlaqə : sabuhi.alasgarli@pm.me
        
        """
        QMessageBox.information(self, 'Scraper', info)

    @staticmethod
    def github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/alasgarovs/scraper"))

    def start_scraping(self):
        link = self.input_link.text().strip()

        if not link:
            self.show_error_message(
                'Məlumat əldə etmək üçün saytdan kateqoriya linkini daxil edin!')
            return

        self.list_info.clear()

        self.button_get_data.setStyleSheet('color:grey')
        self.button_get_data.setEnabled(False)

        self.scrape_thread = ScrapeThread(link)
        self.scrape_thread.line_processed.connect(self.update_list_info)
        self.scrape_thread.finished_signal.connect(self.display_scraped_data)
        self.scrape_thread.finished.connect(lambda: self.button_get_data.setEnabled(True))
        self.scrape_thread.finished.connect(lambda: self.button_get_data.setStyleSheet('color:#024871'))
        self.scrape_thread.start()

    def update_list_info(self, line, count):
        self.list_info.addItem(line)
        self.label_info.setText(f'Proses başladı : Ümumi {count} məhsul')

    def display_scraped_data(self, product_data):
        self.write_to_file(product_data, 'products.txt')
        self.label_info.setText(f'Proses bitdi : Ümumi {len(product_data)} məhsul')
        self.button_export_to_excel.show()

    def export_to_excel(self):
        options = QFileDialog.Options()
        file_name, _  = QFileDialog.getSaveFileName(self, "Faylı saxla", "", "Excel Faylı (*.xlsx);", options=options)

        if file_name:
            if file_name[-5:] == '.xlsx':
                pass
            else:
                file_name = file_name +'.xlsx'
            product_data = self.read_from_file('products.txt')
            df = pd.DataFrame(product_data, columns=['Məhsul', 'Qiymət'])
            try:
                df.to_excel(file_name, index=False)
                QMessageBox.information(self, 'Scraper', f'Məlumat uğurla qeyd edildi!')

                self.input_link.clear()
                self.list_info.clear()
                self.label_info.setText('')
                self.button_export_to_excel.hide()
            except Exception as e:
                self.show_error_message(f"Məlumatı Excel'ə köçürərkən xəta baş verdi!: {e}")

    @staticmethod
    def read_from_file(filename):
        product_data = []
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                product_name, price = line.strip().split(' : ')
                product_data.append([product_name, price])
        return product_data

    @staticmethod
    def write_to_file(data, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            for item in data:
                line = f"{item[0]} : {item[1]}"
                file.write(f"{line}\n")
            file.close()

    def show_error_message(self, message):
        self.input_link.setStyleSheet(self.color_error)
        QMessageBox.critical(self, 'Scraper', message)
        self.input_link.setStyleSheet(self.color_normal)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Main()
    main_window.show()
    sys.exit(app.exec_())
