from PyQt5 import uic


def generate_python_files():
    py_path = '../src/products_design.py'
    ui_path = 'products_design.ui'

    with open(py_path, 'w', encoding="utf-8") as gui:
        uic.compileUi(ui_path, gui)


if __name__ == "__main__":
    generate_python_files()
