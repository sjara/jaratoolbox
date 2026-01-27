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
import matplotlib.pyplot as plt

from jaratoolbox import widefieldanalysis
from jaratoolbox.widefieldanalysis import CHANNEL_COLORS, CHANNEL_NAMES

SCALE_BAR_LENGTH = 1.0  # in mm
SCALE_BAR_POS = 'lower left'

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
        
        # Normalize signal change and compute clim
        self.normed_signal_change = wfavg.normalize_signal_change(roi=roi)
        self.clim = wfavg.compute_clim(self.normed_signal_change)
        
        # Initialize thresholds and enabled states
        self.thresholds = [0.5, 0.5, 0.5]
        self.enabled = [True, True, True]
        
        # Track scale bar artists for easy removal
        self.scale_bar_artists = None
        self.show_scale_bar = True  # Whether to show the scale bar
        
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
            group = QGroupBox(f'{CHANNEL_NAMES[ind]} Channel ({self.wfavg.possible_freq[ind]:.0f} Hz)')
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
        
        # Display options
        display_group = QGroupBox('Display Options')
        display_layout = QGridLayout(display_group)
        
        self.scale_bar_checkbox = QCheckBox('Show scale bar')
        self.scale_bar_checkbox.setChecked(True)
        self.scale_bar_checkbox.stateChanged.connect(self.on_scale_bar_toggled)
        display_layout.addWidget(self.scale_bar_checkbox, 0, 0)
        
        controls_layout.addWidget(display_group)
        
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
    
    def on_scale_bar_toggled(self, state):
        """Handle scale bar checkbox toggle."""
        self.show_scale_bar = (state == Qt.CheckState.Checked.value)
        if self.show_scale_bar:
            self.add_scale_bar()
        else:
            self.remove_scale_bar()
        self.canvas.draw_idle()
    
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
            self.clim = self.wfavg.compute_clim(self.normed_signal_change)
            
            self.update_plots(reset_zoom=True)
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
        
        # Redraw scale bar on merged image to reflect new zoom
        self.redraw_scale_bar()
    
    def add_scale_bar(self):
        """Add a scale bar to the merged image axis."""
        if not hasattr(self, 'figure') or not self.figure.axes:
            return
        
        # Find the merged axis (last one created)
        ax_merged = self.figure.axes[-1]
        
        # Add scale bar and store artists for later removal
        self.scale_bar_artists = self.wfavg.add_scale_bar(
            ax_merged, bar_length_mm=SCALE_BAR_LENGTH, location=SCALE_BAR_POS
        )
    
    def remove_scale_bar(self):
        """Remove the scale bar if it exists."""
        if self.scale_bar_artists is not None:
            line, text = self.scale_bar_artists
            line.remove()
            text.remove()
            self.scale_bar_artists = None
    
    def redraw_scale_bar(self):
        """Redraw the scale bar on the merged image axis after zoom/pan."""
        # Skip if we're programmatically updating the plots
        if self._updating_plots:
            print('  -> skipping (updating plots)')
            return
        
        if not hasattr(self, 'figure') or not self.figure.axes:
            return
        
        self.remove_scale_bar()
        if self.show_scale_bar:
            self.add_scale_bar()
        self.canvas.draw_idle()
        
    def update_plots(self, reset_zoom=False):
        """Update all plots based on current slider and checkbox states.
        
        Args:
            reset_zoom (bool): If True, reset zoom to ROI. Otherwise preserve current zoom.
        """
        # Set flag to prevent callbacks from triggering during update
        self._updating_plots = True
        
        # Store current axis limits if axes exist and we're not resetting
        stored_limits = None
        if not reset_zoom and hasattr(self, 'figure') and self.figure.axes:
            try:
                ax = self.figure.axes[0]
                stored_limits = (ax.get_xlim(), ax.get_ylim())
            except:
                raise  #pass
        
        self.figure.clear()
        
        # Compute merged image using the WidefieldAverage method
        merged_image = self.wfavg.compute_merged_image(
            self.normed_signal_change,
            thresholds=self.thresholds,
            enabled=self.enabled,
            bg_image=self.wfavg.avg_baseline_each_freq[0],
            alpha=0.5
        )
        
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
            ax.set_ylabel(f'{self.wfavg.possible_freq[indf]:.0f} Hz\n({CHANNEL_NAMES[indf]}){status}')
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
        
        # Add scale bar to merged image (after zoom is applied so it positions correctly)
        if self.show_scale_bar:
            self.add_scale_bar()

        self.figure.tight_layout()
        self.canvas.draw()
        
        # Reset flag after update is complete
        self._updating_plots = False


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
    
    roi = [[170, 370], [250, 450]]  #[[200, 400], [150, 350]]
    
    # Load precomputed averages
    wfavg = widefieldanalysis.WidefieldAverage(subject, date, session)
    
    # Create and run application
    app = QApplication(sys.argv)
    viewer = WidefieldMergedViewer(wfavg, roi=roi)
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
