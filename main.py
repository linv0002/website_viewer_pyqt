import sys
import json
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QToolBar, QAction, QTabWidget, QMenuBar, QMenu, QListWidget, QPushButton, QDialog, QHBoxLayout, QInputDialog, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QFont

# Set the User-Agent string
#profile = QWebEngineProfile.defaultProfile()
#profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36")


CONFIG_FILE = "browser_config.json"
HISTORY_FILE = "browser_history.json"
STORAGE_PATH = os.path.join(os.getcwd(), "browser_data")

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load configuration (home page, bookmarks, history)
        self.load_config()
        self.load_history()

        # Set the main window properties
        self.setWindowTitle('PyQt Web Browser')
        self.setGeometry(100, 100, 1200, 800)

        # Create a toolbar for navigation
        navtb = QToolBar("Navigation")
        self.addToolBar(navtb)

        # Add Back button
        back_btn = QAction("Back", self)
        back_btn.triggered.connect(self.back)
        navtb.addAction(back_btn)

        # Add Forward button
        forward_btn = QAction("Forward", self)
        forward_btn.triggered.connect(self.forward)
        navtb.addAction(forward_btn)

        # Add Reload button
        reload_btn = QAction("Reload", self)
        reload_btn.triggered.connect(self.reload)
        navtb.addAction(reload_btn)

        # Add Home button
        home_btn = QAction("Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        # Add New Tab button
        new_tab_btn = QAction("New Tab", self)
        new_tab_btn.triggered.connect(self.open_new_tab)
        navtb.addAction(new_tab_btn)

        # Create a QLineEdit for the URL input with larger font
        self.url_bar = QLineEdit(self)
        self.url_bar.setPlaceholderText("Enter URL and press Enter...")
        font = QFont()
        font.setPointSize(16)  # Larger font size
        self.url_bar.setFont(font)
        self.url_bar.returnPressed.connect(self.load_url)

        # Add the URL bar to the toolbar
        navtb.addWidget(self.url_bar)

        # Set up the QWebEngineProfile with persistent storage
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        profile.setCachePath(STORAGE_PATH)
        profile.setPersistentStoragePath(STORAGE_PATH)

        # Create a QWebEngineView with a custom page that uses the profile
        page = QWebEnginePage(profile, self)
        self.browser = QWebEngineView()
        self.browser.setPage(page)
        self.browser.setUrl(QUrl(self.home_page))  # Set the home page
        self.browser.urlChanged.connect(self.update_url)

        # Create a tab widget for tabbed browsing
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.update_current_tab)
        self.tabs.addTab(self.browser, "Charts")

        # Add the tab widget to the layout
        self.setCentralWidget(self.tabs)

        # Create a menu bar
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # Add Bookmarks menu
        self.bookmarks_menu = QMenu("Bookmarks", self)
        menubar.addMenu(self.bookmarks_menu)

        # Add History menu
        self.history_menu = QMenu("History", self)
        menubar.addMenu(self.history_menu)

        # Load bookmarks and history into the menu
        self.load_bookmarks()
        self.load_history_menu()

        # Add a bookmark action
        bookmark_btn = QAction("Add Bookmark", self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        navtb.addAction(bookmark_btn)

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as file:
                config = json.load(file)
                self.home_page = config.get("home_page", "https://www.tradingview.com/chart/")
                self.bookmarks = config.get("bookmarks", [])
        except FileNotFoundError:
            self.home_page = "https://www.tradingview.com/chart/"
            self.bookmarks = []

    def save_config(self):
        config = {
            "home_page": self.home_page,
            "bookmarks": self.bookmarks
        }
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file)

    def load_history(self):
        try:
            with open(HISTORY_FILE, "r") as file:
                self.history = json.load(file)
        except FileNotFoundError:
            self.history = []

    def save_history(self):
        with open(HISTORY_FILE, "w") as file:
            json.dump(self.history, file)

    def validate_url(self, url):
        if not url.startswith(("http://", "https://")):
            return "http://" + url
        return url

    def load_url(self):
        url = self.validate_url(self.url_bar.text())
        self.browser.setUrl(QUrl(url))
        self.add_to_history(url)

    def update_url(self, q):
        self.url_bar.setText(q.toString())

    def navigate_home(self):
        self.browser.setUrl(QUrl(self.home_page))

    def back(self):
        self.browser.back()

    def forward(self):
        self.browser.forward()

    def reload(self):
        self.browser.reload()

    def close_current_tab(self, i):
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)

    def update_current_tab(self, i):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            self.browser = current_browser
            self.url_bar.setText(current_browser.url().toString())

    def add_new_tab(self, url="https://www.tradingview.com/chart/", label="Charts"):
        profile = QWebEngineProfile.defaultProfile()
        page = QWebEnginePage(profile, self)
        new_browser = QWebEngineView()
        new_browser.setPage(page)
        new_browser.setUrl(QUrl(url))
        new_browser.urlChanged.connect(lambda q: self.update_url(q))
        i = self.tabs.addTab(new_browser, label)
        self.tabs.setCurrentIndex(i)

    def open_new_tab(self):
        # Opens a new tab with the home page or a blank page
        self.add_new_tab()

    def add_bookmark(self):
        url = self.validate_url(self.url_bar.text())
        if url not in self.bookmarks:
            self.bookmarks.append(url)
            self.load_bookmarks()

    def load_bookmarks(self):
        self.bookmarks_menu.clear()  # Clear current bookmarks

        # Load and add bookmarks
        for url in self.bookmarks:
            self.add_bookmark_action(url)

        # Ensure the "Edit Bookmarks" option is always present
        self.add_edit_bookmarks_option()

    def add_bookmark_action(self, url):
        bookmark_action = QAction(url, self)
        bookmark_action.triggered.connect(lambda: self.load_bookmark_from_menu(url))

        # Insert bookmark before "Edit Bookmarks"
        actions = self.bookmarks_menu.actions()
        if actions and actions[-1].text() == "Edit Bookmarks...":
            self.bookmarks_menu.insertAction(actions[-1], bookmark_action)
        else:
            # If "Edit Bookmarks" isn't present, add it first, then insert the bookmark
            self.add_edit_bookmarks_option()
            self.bookmarks_menu.insertAction(self.bookmarks_menu.actions()[-1], bookmark_action)

    def add_edit_bookmarks_option(self):
        # Check if "Edit Bookmarks" is already in the menu
        for action in self.bookmarks_menu.actions():
            if action.text() == "Edit Bookmarks...":
                return

        # Add a separator before the "Edit Bookmarks" option
        self.bookmarks_menu.addSeparator()

        # Add the Edit Bookmarks option at the bottom
        edit_bookmarks_action = QAction("Edit Bookmarks...", self)
        edit_bookmarks_action.triggered.connect(self.edit_bookmarks)
        self.bookmarks_menu.addAction(edit_bookmarks_action)

    def load_bookmark_from_menu(self, url):
        self.add_to_history(url)
        self.add_new_tab(url, url)

    def edit_bookmarks(self):
        dialog = EditBookmarksDialog(self.bookmarks, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update bookmarks with the changes and reload
            self.bookmarks = dialog.get_bookmarks()
            self.save_config()
            self.load_bookmarks()

    def add_to_history(self, url):
        timestamp = datetime.now().isoformat()
        self.history.append({"url": url, "timestamp": timestamp})

        # Keep only the last month of history
        one_month_ago = datetime.now() - timedelta(days=30)
        self.history = [entry for entry in self.history if datetime.fromisoformat(entry["timestamp"]) > one_month_ago]

        self.save_history()
        self.load_history_menu()

    def load_history_menu(self):
        self.history_menu.clear()  # Clear current history

        # Show the last 10 history items
        last_10 = self.history[-10:]
        for entry in reversed(last_10):
            history_action = QAction(entry["url"], self)
            history_action.triggered.connect(lambda checked, url=entry["url"]: self.load_bookmark_from_menu(url))
            self.history_menu.addAction(history_action)

        # Add a separator and the "View Detailed History" option
        if self.history:
            self.history_menu.addSeparator()
            detailed_history_action = QAction("View Detailed History...", self)
            detailed_history_action.triggered.connect(self.view_detailed_history)
            self.history_menu.addAction(detailed_history_action)

    def view_detailed_history(self):
        dialog = DetailedHistoryDialog(self.history, self)
        if dialog.exec_() == QDialog.Accepted:
            url = dialog.get_selected_url()
            if url:
                self.load_bookmark_from_menu(url)

    def closeEvent(self, event):
        self.save_config()
        self.save_history()
        event.accept()


class EditBookmarksDialog(QDialog):
    def __init__(self, bookmarks, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Bookmarks")
        self.bookmarks = list(bookmarks)  # Make a copy of the bookmarks

        layout = QVBoxLayout(self)

        self.bookmark_list = QListWidget(self)
        self.bookmark_list.addItems(self.bookmarks)
        layout.addWidget(self.bookmark_list)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Add", self)
        add_button.clicked.connect(self.add_bookmark)
        button_layout.addWidget(add_button)

        edit_button = QPushButton("Edit", self)
        edit_button.clicked.connect(self.edit_bookmark)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete", self)
        delete_button.clicked.connect(self.delete_bookmark)
        button_layout.addWidget(delete_button)

        up_button = QPushButton("Move Up", self)
        up_button.clicked.connect(self.move_up)
        button_layout.addWidget(up_button)

        down_button = QPushButton("Move Down", self)
        down_button.clicked.connect(self.move_down)
        button_layout.addWidget(down_button)

        save_button = QPushButton("Save", self)
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

    def validate_url(self, url):
        if not url.startswith(("http://", "https://")):
            return "http://" + url
        return url

    def add_bookmark(self):
        url, ok = QInputDialog.getText(self, "Add Bookmark", "Enter new URL:")
        if ok and url:
            url = self.validate_url(url)
            self.bookmarks.append(url)
            self.bookmark_list.addItem(url)

    def edit_bookmark(self):
        current_row = self.bookmark_list.currentRow()
        if current_row >= 0:
            url, ok = QInputDialog.getText(self, "Edit Bookmark", "Enter new URL:", text=self.bookmarks[current_row])
            if ok and url:
                url = self.validate_url(url)
                self.bookmarks[current_row] = url
                self.bookmark_list.item(current_row).setText(url)

    def delete_bookmark(self):
        current_row = self.bookmark_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, 'Delete Bookmark', 'Are you sure you want to delete this bookmark?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.bookmark_list.takeItem(current_row)
                del self.bookmarks[current_row]

    def move_up(self):
        current_row = self.bookmark_list.currentRow()
        if current_row > 0:
            self.bookmarks[current_row], self.bookmarks[current_row - 1] = self.bookmarks[current_row - 1], self.bookmarks[current_row]
            self.bookmark_list.insertItem(current_row - 1, self.bookmark_list.takeItem(current_row))
            self.bookmark_list.setCurrentRow(current_row - 1)

    def move_down(self):
        current_row = self.bookmark_list.currentRow()
        if current_row < self.bookmark_list.count() - 1:
            self.bookmarks[current_row], self.bookmarks[current_row + 1] = self.bookmarks[current_row + 1], self.bookmarks[current_row]
            self.bookmark_list.insertItem(current_row + 1, self.bookmark_list.takeItem(current_row))
            self.bookmark_list.setCurrentRow(current_row + 1)

    def get_bookmarks(self):
        return self.bookmarks


class DetailedHistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detailed History")
        self.history = list(history)  # Make a copy of the history

        layout = QVBoxLayout(self)

        self.history_list = QListWidget(self)

        # Classify history by week
        weeks = {}
        for entry in self.history:
            week_start = datetime.fromisoformat(entry["timestamp"]).strftime('%Y-%U')
            if week_start not in weeks:
                weeks[week_start] = []
            weeks[week_start].append(entry)

        for week_start, entries in weeks.items():
            self.history_list.addItem(f"Week {week_start}:")
            for entry in entries:
                self.history_list.addItem(f"  {entry['timestamp']} - {entry['url']}")

        layout.addWidget(self.history_list)

        button_layout = QHBoxLayout()
        select_button = QPushButton("Select", self)
        select_button.clicked.connect(self.accept)
        button_layout.addWidget(select_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_selected_url(self):
        selected_item = self.history_list.currentItem()
        if selected_item and "http" in selected_item.text():
            return selected_item.text().split(" - ")[-1]
        return None


def main():
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
