from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from pathlib import Path
from PyQt5.QtGui import *
from matplotlib.pyplot import box
import pyqtgraph as pg
import nmrglue as ng
from qt_material import apply_stylesheet
from functools import partial


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.static_dir = Path(__file__).joinpath('../../icons').resolve()
        self.loaded_data = []
        # For keeping track of whether files are hidden
        self._hidden_folders = False
        # Hide starting widget until start button pressed
        landing_page_frame = QFrame()
        landing_page_layout = QVBoxLayout()
        landing_page_frame.setLayout(landing_page_layout)
        start_button = QPushButton('Start')
        start_button.pressed.connect(self.show_menu)
        logo = QLabel()
        logo.setPixmap(QPixmap(str(self.static_dir/"NMRVis_Logo.png")))
        landing_page_layout.addWidget(logo)
        landing_page_layout.addWidget(start_button)
        self.setCentralWidget(landing_page_frame)
        self.show()

    def show_menu(self):
        w = QWidget()
        menu_layout = QVBoxLayout()
        load_button = QPushButton('Load NMR Data')
        load_button.pressed.connect(self.get_directory)
        menu_layout.addWidget(load_button)
        w.setLayout(menu_layout)
        self.setCentralWidget(w)

    def draw_plot(self):
        tb = QToolBar()
        tb_action = QAction('Hide/Show', self)
        tb_action.setStatusTip('Hide or show loaded files')
        tb_action.triggered.connect(
            lambda x: self.show_folders() if self._hidden_folders else self.hide_folders()
        )
        tb.addAction(tb_action)
        self.addToolBar(tb)

        self.w = QWidget()
        self.setCentralWidget(self.w)

        # Left-side VBox
        self.vbox = QVBoxLayout()
        hide_button = QPushButton('Close')
        hide_button.pressed.connect(self.hide_folders)
        self.vbox.addWidget(hide_button)
        self.vframe = QFrame()
        self.vframe.setLayout(self.vbox)
        self.hide_folders()
        # Right side plot
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.vframe)

        self.plt = pg.PlotWidget(background=(46, 54, 59))
        self.loaded_data = []
        self.hbox.addWidget(self.plt)

        self.w.setLayout(self.hbox)

    def hide_folders(self):
        self._hidden_folders = True
        self.vframe.hide()

    def show_folders(self):
        self._hidden_folders = False
        self.vframe.show()

    @staticmethod
    def find_pdata(path):
        for p in path.rglob('*'):
            if str(p.stem) == "pdata":
                # Number of directories traversed
                dir_depth = str(p.relative_to(path)).count('/')
                if dir_depth == 0:
                    return path
                else:
                    return p.parents[dir_depth-1].resolve()

    def update_loaded_data(self, dirname):
        name = str(dirname.relative_to(Path.home()).parents[1])
        hbox = QHBoxLayout()
        box = QCheckBox(str(name))
        show = QPushButton('Show')

        show.pressed.connect(partial(self.update_plot, dirname))
        hbox.addWidget(box)
        hbox.addWidget(show)
        self.vbox.addLayout(hbox)
        self.show_folders()

    def get_directory(self, nmr_format='bruker'):
        file_dialog = QFileDialog()

        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QListView, 'listView')
        # To select multiple directories
        if file_view:
            file_view.setSelectionMode(QAbstractItemView.MultiSelection)
        f_tree_view = file_dialog.findChild(QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)
        if file_dialog.exec():
            dirnames = file_dialog.selectedFiles()
            if nmr_format == 'bruker':
                if not getattr(self, 'plt', None):
                    self.draw_plot()
                for dirname in dirnames:
                    dirname = self.find_pdata(Path(dirname))
                    dirname = Path(dirname).joinpath('pdata/1')
                    self.loaded_data.append(dirname)
                    self.update_plot(dirname)
                    self.update_loaded_data(dirname)

    def update_plot(self, dirname):
        params, data = ng.fileio.bruker.read_pdata(dirname)
        udic = ng.bruker.guess_udic(params, data)
        uc = ng.fileiobase.uc_from_udic(udic, 0)
        ppm = uc.ppm_scale()
        self.plt.clear()
        plot = self.plt.plot(ppm, data)
        self.plt.setLabel(axis='bottom', text='ppm')
        view = plot.getViewBox()
        view.setLimits(xMin=-0.5, xMax=max(data)+5)
        view.invertX(True)


class AppContext(ApplicationContext):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window = MainWindow()

    def run(self):
        self.window.show()
        return self.app_exec_()


if __name__ == '__main__':
    context = AppContext()
    # window = QMainWindow()
    # window.resize(250, 150)
    # window.show()
    apply_stylesheet(context.app, theme='dark_teal.xml')
    exit_code = context.app.exec_()
