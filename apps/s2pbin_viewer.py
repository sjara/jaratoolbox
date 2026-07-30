"""
PyQt6 application to display the frames of a Suite2p binary file.
"""

import sys
import argparse
from suite2p.io import BinaryFile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QSlider, QLabel)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

DEFAULT_SIZE = 796
DEFAULT_N_FRAMES = 10000


class BinaryViewer(QMainWindow):
    def __init__(self, frames):
        super().__init__()
        self.frames = frames
        n_frames = len(frames)
        self.setWindowTitle('Suite2p Binary Viewer')

        vmin = 0
        vmax = 2**16 - 1

        fig = Figure(figsize=(7, 7))
        self.canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.axis('off')
        fig.tight_layout()
        self.img = ax.imshow(frames[0], cmap='gray', vmin=vmin, vmax=vmax)
        self.title = ax.set_title('Frame 0')

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(n_frames - 1)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.on_slider_changed)

        self.frame_label = QLabel('Frame: 0')

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.frame_label)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addLayout(slider_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_slider_changed(self, value):
        self.img.set_data(self.frames[value])
        self.title.set_text(f'Frame {value}')
        self.frame_label.setText(f'Frame: {value}')
        self.canvas.draw_idle()


def parse_args():
    parser = argparse.ArgumentParser(description='Display frames of a Suite2p binary file.')
    parser.add_argument('binfile', help='Path to the Suite2p binary file (data.bin)')
    parser.add_argument('--size', type=int, nargs=2, metavar=('Ly', 'Lx'), default=(DEFAULT_SIZE, DEFAULT_SIZE),
                         help=f'Frame size as Ly Lx (default: {DEFAULT_SIZE} {DEFAULT_SIZE})')
    parser.add_argument('--nframes', type=int, default=DEFAULT_N_FRAMES,
                         help=f'Number of frames to load (default: {DEFAULT_N_FRAMES})')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    Ly, Lx = args.size

    print(f"Loading binary: {args.binfile} ({Ly}x{Lx} pixels, {args.nframes} frames)", flush=True)
    bf = BinaryFile(Ly=Ly, Lx=Lx, filename=args.binfile)
    frames = bf[0:args.nframes]

    print("Launching viewer...", flush=True)
    app = QApplication(sys.argv)
    window = BinaryViewer(frames)
    window.show()
    sys.exit(app.exec())
