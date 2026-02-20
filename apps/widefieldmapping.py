"""
PyQt6 application for interactive widefield imaging analysis visualization.

This application displays normalized signal change images for each frequency channel
and a merged RGB image showing the dominant response at each pixel.
"""

import sys
import signal
import argparse
import numpy as np
from scipy import ndimage
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSlider, QLabel, QCheckBox, QGroupBox, QGridLayout, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from jaratoolbox import widefieldanalysis
from jaratoolbox.widefieldanalysis import CHANNEL_COLORS, CHANNEL_NAMES

SCALE_BAR_LENGTH = 1.0  # in mm
SCALE_BAR_POS = 'lower left'

ORIENTATION_LABELS_COLOR = 'yellow'  # Color for anatomical direction labels

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
        
        # Track orientation labels
        self.orientation_label_artists = []  # List to store text artists
        self.show_orientation_labels = True  # Whether to show orientation labels
        
        # Display rotation angle (in degrees, CCW)
        self.rotation_angle = 0.0
        
        # Horizontal flip
        self.flip_horizontal = False
        
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
        
        self.orientation_labels_checkbox = QCheckBox('Show orientation labels')
        self.orientation_labels_checkbox.setChecked(True)
        self.orientation_labels_checkbox.stateChanged.connect(self.on_orientation_labels_toggled)
        display_layout.addWidget(self.orientation_labels_checkbox, 1, 0)
        
        # Flip horizontal checkbox
        self.flip_horizontal_checkbox = QCheckBox('Flip left/right')
        self.flip_horizontal_checkbox.setChecked(False)
        self.flip_horizontal_checkbox.stateChanged.connect(self.on_flip_horizontal_toggled)
        display_layout.addWidget(self.flip_horizontal_checkbox, 2, 0)
        
        # Rotation angle control
        display_layout.addWidget(QLabel('Rotation (deg):'), 3, 0)
        self.rotation_angle_input = QLineEdit()
        self.rotation_angle_input.setText('0.0')
        self.rotation_angle_input.setMaximumWidth(80)
        self.rotation_angle_input.textChanged.connect(self.on_rotation_text_changed)
        display_layout.addWidget(self.rotation_angle_input, 3, 1)
        
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
    
    def on_orientation_labels_toggled(self, state):
        """Handle orientation labels checkbox toggle."""
        self.show_orientation_labels = (state == Qt.CheckState.Checked.value)
        if self.show_orientation_labels:
            self.add_orientation_labels()
        else:
            self.remove_orientation_labels()
        self.canvas.draw_idle()
    
    def on_flip_horizontal_toggled(self, state):
        """Handle flip horizontal checkbox toggle."""
        self.flip_horizontal = (state == Qt.CheckState.Checked.value)
        self.update_plots()
    
    def on_rotation_text_changed(self, text):
        """Handle rotation angle text change."""
        try:
            angle = float(text)
            self.rotation_angle = angle
            self.update_plots()
        except ValueError:
            # Invalid input, ignore
            pass
    
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
    
    def add_orientation_labels(self):
        """Add anatomical direction labels to the merged image axis."""
        if not hasattr(self, 'figure') or not self.figure.axes:
            return
        
        # Find the merged axis (last one created)
        ax_merged = self.figure.axes[-1]
        orientation = self.wfavg.orientation
        label_offset = 0.04  # Offset from edge in axes coordinates
        
        # Define base label positions (before any transformation)
        # Note: imshow displays row 0 at top of axes, so orientation['top'] goes at y=1-label_offset
        base_positions = [
            (0.5, 1-label_offset, 'top'),      # Top
            (0.5, label_offset, 'bottom'),     # Bottom
            (label_offset, 0.5, 'left'),       # Left
            (1-label_offset, 0.5, 'right'),    # Right
        ]
        
        # Apply flip transformation to label positions if needed
        if self.flip_horizontal:
            # When flipped horizontally, left and right anatomical directions swap positions
            # but the screen positions stay the same
            flipped_positions = []
            for x, y, direction_key in base_positions:
                # Keep x position the same (screen position doesn't change)
                # But swap left and right direction keys (anatomy changes sides)
                if direction_key == 'left':
                    direction_key = 'right'
                elif direction_key == 'right':
                    direction_key = 'left'
                flipped_positions.append((x, y, direction_key))
            positions_to_use = flipped_positions
        else:
            positions_to_use = base_positions
        
        # Compute rotated label positions
        angle_rad = np.radians(self.rotation_angle)
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        
        self.orientation_label_artists = []
        for x, y, direction_key in positions_to_use:
            # Convert to centered coordinates (-0.5 to 0.5)
            x_centered = x - 0.5
            y_centered = y - 0.5
            
            # Apply rotation matrix
            x_rot = x_centered * cos_a - y_centered * sin_a
            y_rot = x_centered * sin_a + y_centered * cos_a
            
            # Convert back to axes coordinates (0 to 1)
            x_new = x_rot + 0.5
            y_new = y_rot + 0.5
            
            # Create label with rotated position
            # Keep text rotation at 0 for readability
            text = ax_merged.text(x_new, y_new, orientation[direction_key][0].upper(), 
                                 transform=ax_merged.transAxes, ha='center', va='center',
                                 fontsize=12, weight='bold', color=ORIENTATION_LABELS_COLOR,
                                 rotation=0)
            self.orientation_label_artists.append(text)
    
    def remove_orientation_labels(self):
        """Remove the orientation labels if they exist."""
        for text_artist in self.orientation_label_artists:
            text_artist.remove()
        self.orientation_label_artists = []
    
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
        
        # Create subplots with GridSpec for better control over spacing
        # Use width_ratios to give more space to the merged image (right column)
        gs = GridSpec(3, 2, figure=self.figure, width_ratios=[1, 2], 
                     hspace=0.25, wspace=0.25, top=0.95, bottom=0.05, left=0.05, right=0.95)
        
        # Create first axis
        ax_first = self.figure.add_subplot(gs[0, 0])
        
        # Connect to axis limit change events to update ROI text boxes
        ax_first.callbacks.connect('xlim_changed', self.on_axis_limits_changed)
        ax_first.callbacks.connect('ylim_changed', self.on_axis_limits_changed)
        
        # Left column: individual normalized signal change images
        for indf in range(3):
            if indf == 0:
                ax = ax_first
            else:
                ax = self.figure.add_subplot(gs[indf, 0], 
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
        
        # Right column: merged RGB image spanning all rows
        ax_merged = self.figure.add_subplot(gs[:, 1], sharex=ax_first, sharey=ax_first)
        
        # Apply transformations: flip first, then rotate
        transformed_image = merged_image
        
        if self.flip_horizontal:
            # Flip left-right (along axis 1, which is the width dimension)
            transformed_image = np.flip(transformed_image, axis=1)
        
        if self.rotation_angle != 0:
            # Rotate the RGB image (reshape=False keeps original dimensions)
            transformed_image = ndimage.rotate(transformed_image, self.rotation_angle, 
                                              reshape=False, order=1, mode='constant', cval=0)
        
        ax_merged.imshow(transformed_image)
        
        session_str = f'{self.wfavg.subject}_{self.wfavg.date}_{self.wfavg.session}'
        ax_merged.set_title(f'{session_str}')
        ax_merged.set_aspect('equal')
        
        # Apply zoom: use stored limits if available, otherwise use ROI
        if stored_limits is not None:
            ax_first.set_xlim(stored_limits[0])
            ax_first.set_ylim(stored_limits[1])
        elif self.roi is not None:
            (x_min, x_max), (y_min, y_max) = self.roi
            ax_first.set_xlim(x_min, x_max)
            ax_first.set_ylim(y_max, y_min)
        
        # Add orientation labels to merged image (if enabled)
        if self.show_orientation_labels:
            self.add_orientation_labels()
        
        # Add scale bar to merged image (after zoom is applied so it positions correctly)
        if self.show_scale_bar:
            self.add_scale_bar()

        #self.figure.tight_layout()
        self.canvas.draw()
        
        # Reset flag after update is complete
        self._updating_plots = False


def main():
    """Main entry point for the application."""
    # Enable Ctrl-C to exit the application
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
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
