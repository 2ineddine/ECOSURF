from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout,
    QSpinBox, QDialogButtonBox, QRadioButton, QButtonGroup
)


class PeriodSelectionDialog(QDialog):
    """Dialog for selecting time period from audio metadata"""

    def __init__(self, metadata, audio_duration, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Time Period")
        self.metadata = metadata
        self.audio_duration = audio_duration
        
        layout = QVBoxLayout()

        info_label = QLabel(
            f"File: {metadata.get('date','')} {metadata.get('time','')}\n"
            f"Duration: {audio_duration:.1f} seconds ({audio_duration/60:.1f} minutes)"
        )
        layout.addWidget(info_label)

        mode_group = QGroupBox("Selection Mode")
        mode_layout = QVBoxLayout()

        self.button_group = QButtonGroup()
        self.full_radio = QRadioButton("Full audio")
        self.full_radio.setChecked(True)
        self.custom_radio = QRadioButton("Custom time range")

        self.button_group.addButton(self.full_radio)
        self.button_group.addButton(self.custom_radio)

        mode_layout.addWidget(self.full_radio)
        mode_layout.addWidget(self.custom_radio)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        range_group = QGroupBox("Time Range (seconds)")
        range_layout = QVBoxLayout()

        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Start:"))
        self.start_spin = QSpinBox()
        self.start_spin.setMaximum(int(audio_duration))
        self.start_spin.setValue(0)
        start_layout.addWidget(self.start_spin)
        range_layout.addLayout(start_layout)

        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("End:"))
        self.end_spin = QSpinBox()
        self.end_spin.setMaximum(int(audio_duration))
        self.end_spin.setValue(min(300, int(audio_duration)))
        end_layout.addWidget(self.end_spin)
        range_layout.addLayout(end_layout)

        range_group.setLayout(range_layout)
        layout.addWidget(range_group)
        self.full_radio.toggled.connect(lambda checked: range_group.setEnabled(not checked))
        range_group.setEnabled(False)

        #self.full_radio.toggled.connect(lambda checked: range_group.setEnabled(not checked))
        range_group.setEnabled(False)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_time_range(self):
        if self.full_radio.isChecked():
            return (0, self.audio_duration)
        else:
            return (self.start_spin.value(), self.end_spin.value())
