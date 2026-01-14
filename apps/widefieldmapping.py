"""
PyQt6 application for interactive widefield imaging analysis visualization.

This application displays normalized signal change images for each frequency channel
and a merged RGB image showing the dominant response at each pixel.
"""

import sys
import argparse
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSlider, QLabel, QCheckBox, QGroupBox, QGridLayout, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure

from jaratoolbox import widefieldanalysis


class WidefieldMergedViewer(QMainWindow):
    """
    Interactive viewer for merged widefield signal change images.
    
    Displays normalized dF/F images for each frequency channel and a merged RGB
    image where each pixel is colored according to which frequency has the maximum
    response. Includes sliders to adjust thresholds and checkboxes to enable/disable
    each channel.
    """
    
    def __init__(self, wfavg, roi=None):
        """
        Initialize the viewer.
        
        Args:
            wfavg (WidefieldAverage): Precomputed widefield averages object.
            roi (tuple or None): Region of interest. Format: ((x_min, x_max), (y_min, y_max)).
        """
        super().__init__()
        self.wfavg = wfavg
        self.roi = roi
        
        # Channel names and colors
        self.channel_names = ['Red', 'Green', 'Blue']
        self.channel_colors = [
            [1, 0, 0],       # Red
            [0, 1, 0],       # Green
            [0.25, 0.5, 1],  # Light blue
        ]
        
        # Normalize signal change
        self.normed_signal_change = wfavg.normalize_signal_change(roi=roi)
        
        # Calculate clim based on standard deviation
        global_std = np.std(self.normed_signal_change[:3])
        self.clim = (-2 * global_std, 8 * global_std)
        
        # Initialize thresholds and enabled states
        self.thresholds = [0.5, 0.5, 0.5]
        self.enabled = [True, True, True]
        
        # Flag to prevent recursive updates
        self._updating_plots = False
        
        self.init_ui()
        self.update_plots(reset_zoom=True)
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Widefield Merged Signal Change Viewer')
        self.setGeometry(100, 100, 1400, 800)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Left side: matplotlib figure with toolbar
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, plot_widget)
        
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        main_layout.addWidget(plot_widget, stretch=3)
        
        # Right side: controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        main_layout.addWidget(controls_widget, stretch=1)
        
        # Create controls for each channel
        self.sliders = []
        self.slider_labels = []
        self.checkboxes = []
        
        for ind in range(3):
            group = QGroupBox(f'{self.channel_names[ind]} Channel ({self.wfavg.possible_freq[ind]:.0f} Hz)')
            group_layout = QGridLayout(group)
            
            # Enable checkbox
            checkbox = QCheckBox('Enabled')
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, idx=ind: self.on_checkbox_changed(idx, state))
            group_layout.addWidget(checkbox, 0, 0, 1, 2)
            self.checkboxes.append(checkbox)
            
            # Threshold slider
            slider_label = QLabel('Threshold: 0.50')
            group_layout.addWidget(slider_label, 1, 0)
            self.slider_labels.append(slider_label)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(25)  # 25/50 = 0.5 threshold
            slider.valueChanged.connect(lambda value, idx=ind: self.on_slider_changed(idx, value))
            group_layout.addWidget(slider, 1, 1)
            self.sliders.append(slider)
            
            controls_layout.addWidget(group)
        
        # ROI controls
        roi_group = QGroupBox('Region of Interest')
        roi_layout = QGridLayout(roi_group)
        
        roi_layout.addWidget(QLabel('X min:'), 0, 0)
        self.roi_x_min = QLineEdit()
        self.roi_x_min.setText(str(self.roi[0][0]) if self.roi else '0')
        roi_layout.addWidget(self.roi_x_min, 0, 1)
        
        roi_layout.addWidget(QLabel('X max:'), 1, 0)
        self.roi_x_max = QLineEdit()
        self.roi_x_max.setText(str(self.roi[0][1]) if self.roi else '512')
        roi_layout.addWidget(self.roi_x_max, 1, 1)
        
        roi_layout.addWidget(QLabel('Y min:'), 2, 0)
        self.roi_y_min = QLineEdit()
        self.roi_y_min.setText(str(self.roi[1][0]) if self.roi else '0')
        roi_layout.addWidget(self.roi_y_min, 2, 1)
        
        roi_layout.addWidget(QLabel('Y max:'), 3, 0)
        self.roi_y_max = QLineEdit()
        self.roi_y_max.setText(str(self.roi[1][1]) if self.roi else '512')
        roi_layout.addWidget(self.roi_y_max, 3, 1)
        
        roi_apply_btn = QPushButton('Apply ROI')
        roi_apply_btn.clicked.connect(self.on_roi_changed)
        roi_layout.addWidget(roi_apply_btn, 4, 0, 1, 2)
        
        controls_layout.addWidget(roi_group)
        
        # Add stretch to push controls to top
        controls_layout.addStretch()
        
    def on_slider_changed(self, channel_idx, value):
        """
        Handle slider value change.
        
        Args:
            channel_idx (int): Index of the channel (0=Red, 1=Green, 2=Blue).
            value (int): Slider value (0-100).
        """
        # Convert slider value to threshold (0.0 to 2.0 range)
        threshold = value / 50.0
        self.thresholds[channel_idx] = threshold
        self.slider_labels[channel_idx].setText(f'Threshold: {threshold:.2f}')
        self.update_plots()
        
    def on_checkbox_changed(self, channel_idx, state):
        """
        Handle checkbox state change.
        
        Args:
            channel_idx (int): Index of the channel (0=Red, 1=Green, 2=Blue).
            state (int): Checkbox state.
        """
        self.enabled[channel_idx] = (state == Qt.CheckState.Checked.value)
        self.update_plots()
    
    def on_roi_changed(self):
        """Handle ROI change from edit boxes."""
        try:
            x_min = int(self.roi_x_min.text())
            x_max = int(self.roi_x_max.text())
            y_min = int(self.roi_y_min.text())
            y_max = int(self.roi_y_max.text())
            
            # Validate ROI values
            if x_min >= x_max or y_min >= y_max:
                print("Invalid ROI: min values must be less than max values")
                return
            
            self.roi = [[x_min, x_max], [y_min, y_max]]
            
            # Re-normalize with new ROI
            self.normed_signal_change = self.wfavg.normalize_signal_change(roi=self.roi)
            
            # Recalculate clim
            global_std = np.std(self.normed_signal_change[:3])
            self.clim = (-2 * global_std, 8 * global_std)
            
            # Set flag to prevent callback from overwriting ROI
            self._updating_plots = True
            self.update_plots(reset_zoom=True)
            self._updating_plots = False
        except ValueError:
            print("Invalid ROI values: please enter integers")
    
    def on_axis_limits_changed(self, ax):
        """Handle axis limit changes from interactive zoom/pan."""
        # Skip if we're programmatically updating the plots
        if self._updating_plots:
            return
        
        # Get current axis limits
        x_min, x_max = ax.get_xlim()
        y_max, y_min = ax.get_ylim()  # Note: y-axis is inverted for images
        
        # Update text boxes (round to nearest integer)
        self.roi_x_min.setText(str(int(round(x_min))))
        self.roi_x_max.setText(str(int(round(x_max))))
        self.roi_y_min.setText(str(int(round(y_min))))
        self.roi_y_max.setText(str(int(round(y_max))))
        
        # Update internal ROI (but don't trigger re-normalization)
        self.roi = [[int(round(x_min)), int(round(x_max))], 
                    [int(round(y_min)), int(round(y_max))]]
        
    def update_plots(self, reset_zoom=False):
        """Update all plots based on current slider and checkbox states.
        
        Args:
            reset_zoom (bool): If True, reset zoom to ROI. Otherwise preserve current zoom.
        """
        # Store current axis limits if axes exist and we're not resetting
        stored_limits = None
        if not reset_zoom and hasattr(self, 'figure') and self.figure.axes:
            try:
                ax = self.figure.axes[0]
                stored_limits = (ax.get_xlim(), ax.get_ylim())
            except:
                pass
        
        self.figure.clear()
        
        # Get first three channels
        first_three = self.normed_signal_change[:3].copy()
        
        # Apply thresholds to each channel for the merged image
        thresholded = first_three.copy()
        for i in range(3):
            if not self.enabled[i]:
                thresholded[i] = -np.inf  # Disable channel by setting to -inf
            else:
                # Set values below threshold to -inf so they don't win max comparison
                thresholded[i] = np.where(first_three[i] >= self.thresholds[i], 
                                          first_three[i], -np.inf)
        
        # Find which channel has max value at each pixel
        max_channel = np.argmax(thresholded, axis=0)
        max_values = np.max(thresholded, axis=0)
        
        # Create RGB image
        merged_image = np.zeros((*self.normed_signal_change.shape[1:], 3))
        for channel in range(3):
            if self.enabled[channel]:
                mask = (max_channel == channel) & (max_values > -np.inf)
                for c in range(3):
                    merged_image[mask, c] = max_values[mask] * self.channel_colors[channel][c]
        
        # Clip merged image values
        merged_image = np.clip(merged_image, 0, 1)
        
        # Create subplots
        ax_first = self.figure.add_subplot(3, 2, 1)
        
        # Connect to axis limit change events to update ROI text boxes
        ax_first.callbacks.connect('xlim_changed', self.on_axis_limits_changed)
        ax_first.callbacks.connect('ylim_changed', self.on_axis_limits_changed)
        
        # Left column: individual normalized signal change images
        for indf in range(3):
            if indf == 0:
                ax = ax_first
            else:
                ax = self.figure.add_subplot(3, 2, 2 * indf + 1, 
                                             sharex=ax_first, sharey=ax_first)
            
            im = ax.imshow(self.normed_signal_change[indf], cmap='viridis',
                          vmin=self.clim[0], vmax=self.clim[1])
            
            # Add indicator if channel is disabled
            status = '' if self.enabled[indf] else ' [DISABLED]'
            ax.set_ylabel(f'{self.wfavg.possible_freq[indf]:.0f} Hz\n({self.channel_names[indf]}){status}')
            ax.set_aspect('equal')
            
            if indf == 0:
                ax.set_title('Normalized dF/F')
            
            self.figure.colorbar(im, ax=ax)
        
        # Right column: merged RGB image
        ax_merged = self.figure.add_subplot(1, 2, 2, sharex=ax_first, sharey=ax_first)
        ax_merged.imshow(merged_image)
        ax_merged.set_title('Merged (RGB: max channel)')
        ax_merged.set_aspect('equal')
        
        # Apply zoom: use stored limits if available, otherwise use ROI
        if stored_limits is not None:
            ax_first.set_xlim(stored_limits[0])
            ax_first.set_ylim(stored_limits[1])
        elif self.roi is not None:
            (x_min, x_max), (y_min, y_max) = self.roi
            ax_first.set_xlim(x_min, x_max)
            ax_first.set_ylim(y_max, y_min)
        
        self.figure.tight_layout()
        self.canvas.draw()


def main():
    """Main entry point for the application."""
    DEFAULT_SESSION = 'wifi008_20241219_161007'
    parser = argparse.ArgumentParser(
        description='Interactive viewer for widefield merged signal change images.'
    )
    parser.add_argument('session_info', type=str, nargs='?', default=DEFAULT_SESSION,
                        help='Session info as subject_date_session (default: wifi008_20241219_161007)')
    args = parser.parse_args()
    
    # Parse session info
    parts = args.session_info.split('_')
    if len(parts) != 3:
        parser.error('session_info must be in format: subject_date_session')
    subject, date, session = parts
    
    roi = [[200, 400], [150, 350]]
    
    # Load precomputed averages
    wfavg = widefieldanalysis.WidefieldAverage(subject, date, session)
    
    # Create and run application
    app = QApplication(sys.argv)
    viewer = WidefieldMergedViewer(wfavg, roi=roi)
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
