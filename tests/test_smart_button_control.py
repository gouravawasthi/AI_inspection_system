#!/usr/bin/env python3
"""Test the smart button control system in inspection windows."""

import sys
import os
sys.path.append('/home/taisys/Desktop/AI_inspection_system')
sys.path.append('/home/taisys/Desktop/AI_inspection_system/src')

from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Mock the base inspection window for testing
class MockInspectionWindow(QWidget):
    """Mock inspection window to test button logic"""
    
    # Mock inspection states
    class InspectionState:
        IDLE = "idle"
        BARCODE_ENTERED = "barcode_entered"
        INSPECTION_ACTIVE = "inspection_active"
        STEP_IN_PROGRESS = "step_in_progress"
        STEP_COMPLETED = "step_completed"
        INSPECTION_COMPLETED = "inspection_completed"
        OVERRIDE_APPLIED = "override_applied"
        DATA_SUBMITTED = "data_submitted"
    
    def __init__(self):
        super().__init__()
        
        # Initialize state variables
        self.inspection_state = self.InspectionState.IDLE
        self.step_data_collected = False
        self.override_allowed = False
        self.current_step = 0
        self.inspection_steps = ["Visual Check", "Measurement", "Functional Test", "Final Review"]
        self.inspection_results = {}
        self.barcode = ""
        
        self.initUI()
        self.create_buttons()
        self.update_button_states()
        self.update_status_display()
    
    def initUI(self):
        """Initialize UI"""
        self.setWindowTitle('Smart Button Control System Test')
        self.setGeometry(100, 100, 1000, 700)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Title
        title = QLabel("Smart Button Control System Test")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin: 20px;")
        main_layout.addWidget(title)
        
        # Status display
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(150)
        self.status_display.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ddd; font-family: monospace; font-size: 12px;")
        main_layout.addWidget(self.status_display)
        
        # Button area
        button_area = QWidget()
        button_layout = QHBoxLayout()
        button_area.setLayout(button_layout)
        main_layout.addWidget(button_area)
        
        # Control buttons (left side)
        control_frame = QWidget()
        control_frame.setFixedWidth(320)
        control_frame.setStyleSheet("border: 2px solid #ccc; border-radius: 10px; background-color: white; padding: 15px;")
        self.control_layout = QVBoxLayout()
        control_frame.setLayout(self.control_layout)
        button_layout.addWidget(control_frame)
        
        # State control buttons (right side)
        state_frame = QWidget()
        state_frame.setFixedWidth(350)
        state_frame.setStyleSheet("border: 2px solid #3498db; border-radius: 10px; background-color: #ecf0f1; padding: 15px;")
        state_layout = QVBoxLayout()
        state_frame.setLayout(state_layout)
        
        state_title = QLabel("State Control (for Testing)")
        state_title.setFont(QFont("Arial", 14, QFont.Bold))
        state_title.setAlignment(Qt.AlignCenter)
        state_title.setStyleSheet("color: #2c3e50; margin: 10px;")
        state_layout.addWidget(state_title)
        
        # State buttons
        self.create_state_buttons(state_layout)
        
        button_layout.addWidget(state_frame)
        
        # Status info
        info_layout = QVBoxLayout()
        
        self.state_label = QLabel(f"Current State: {self.inspection_state}")
        self.state_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.state_label.setStyleSheet("color: #27ae60; margin: 10px;")
        info_layout.addWidget(self.state_label)
        
        self.step_label = QLabel(f"Step: {self.current_step}/{len(self.inspection_steps)}")
        self.step_label.setStyleSheet("color: #34495e; margin: 5px;")
        info_layout.addWidget(self.step_label)
        
        self.data_label = QLabel(f"Data Collected: {self.step_data_collected}")
        self.data_label.setStyleSheet("color: #34495e; margin: 5px;")
        info_layout.addWidget(self.data_label)
        
        self.override_label = QLabel(f"Override Allowed: {self.override_allowed}")
        self.override_label.setStyleSheet("color: #34495e; margin: 5px;")
        info_layout.addWidget(self.override_label)
        
        info_widget = QWidget()
        info_widget.setLayout(info_layout)
        button_layout.addWidget(info_widget)
    
    def create_buttons(self):
        """Create the inspection control buttons"""
        # Title for control buttons
        control_title = QLabel("Inspection Controls")
        control_title.setFont(QFont("Arial", 14, QFont.Bold))
        control_title.setAlignment(Qt.AlignCenter)
        control_title.setStyleSheet("color: #2c3e50; margin: 10px;")
        self.control_layout.addWidget(control_title)
        
        # Button style
        button_style = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                margin: 3px 0px;
                min-height: 40px;
                border-radius: 5px;
                border: 2px solid #333;
            }
            QPushButton:disabled {
                color: #888888;
                border: 1px solid #BBBBBB;
            }
        """
        
        # Create buttons
        self.start_inspection_button = QPushButton("Capture")
        self.start_inspection_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #A8D8A8;
            }
        """)
        self.start_inspection_button.clicked.connect(lambda: self.test_action("Capture clicked"))
        self.control_layout.addWidget(self.start_inspection_button)
        
        self.next_step_button = QPushButton("Next Step")
        self.next_step_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #A8C8E8;
            }
        """)
        self.next_step_button.clicked.connect(lambda: self.test_action("Next Step clicked"))
        self.control_layout.addWidget(self.next_step_button)
        
        self.repeat_step_button = QPushButton("Repeat Step")
        self.repeat_step_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #A8C8E8;
            }
        """)
        self.repeat_step_button.clicked.connect(lambda: self.test_action("Repeat Step clicked"))
        self.control_layout.addWidget(self.repeat_step_button)
        
        self.manual_override_button = QPushButton("Manual Override")
        self.manual_override_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #FF9800;
                color: white;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #E8C8A8;
            }
        """)
        self.manual_override_button.clicked.connect(lambda: self.test_action("Manual Override clicked"))
        self.control_layout.addWidget(self.manual_override_button)
        
        # Add note about excluded buttons
        note_label = QLabel("Note: Stop Inspection, Main Menu, and Quit buttons are NOT controlled by logic (always enabled)")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 10px; padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
        self.control_layout.addWidget(note_label)
    
    def create_state_buttons(self, layout):
        """Create state control buttons for testing"""
        states = [
            ("Idle", self.InspectionState.IDLE),
            ("Barcode Entered", self.InspectionState.BARCODE_ENTERED),
            ("Inspection Active", self.InspectionState.INSPECTION_ACTIVE),
            ("Step In Progress", self.InspectionState.STEP_IN_PROGRESS),
            ("Step Completed", self.InspectionState.STEP_COMPLETED),
            ("Inspection Complete", self.InspectionState.INSPECTION_COMPLETED),
            ("Override Applied", self.InspectionState.OVERRIDE_APPLIED),
        ]
        
        for name, state in states:
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 8px;
                    margin: 2px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            btn.clicked.connect(lambda checked, s=state: self.set_test_state(s))
            layout.addWidget(btn)
        
        # Special actions
        special_layout = QHBoxLayout()
        
        collect_data_btn = QPushButton("Collect Data")
        collect_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        collect_data_btn.clicked.connect(self.simulate_data_collection)
        special_layout.addWidget(collect_data_btn)
        
        next_step_btn = QPushButton("Advance Step")
        next_step_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        next_step_btn.clicked.connect(self.advance_step)
        special_layout.addWidget(next_step_btn)
        
        layout.addLayout(special_layout)
    
    def set_test_state(self, state):
        """Set test state and update buttons"""
        self.inspection_state = state
        
        # Set contextual flags based on state
        if state == self.InspectionState.IDLE:
            self.step_data_collected = False
            self.override_allowed = False
            self.barcode = ""
        elif state == self.InspectionState.BARCODE_ENTERED:
            self.step_data_collected = False
            self.override_allowed = False
            self.barcode = "TEST123"
        elif state == self.InspectionState.INSPECTION_ACTIVE:
            self.step_data_collected = False
            self.override_allowed = False
            self.barcode = "TEST123"
        elif state == self.InspectionState.STEP_IN_PROGRESS:
            self.step_data_collected = False
            self.override_allowed = False
            self.barcode = "TEST123"
        elif state == self.InspectionState.STEP_COMPLETED:
            self.step_data_collected = True
            self.override_allowed = True
            self.barcode = "TEST123"
        elif state == self.InspectionState.INSPECTION_COMPLETED:
            self.step_data_collected = True
            self.override_allowed = True
            self.barcode = "TEST123"
            self.current_step = len(self.inspection_steps)
        elif state == self.InspectionState.OVERRIDE_APPLIED:
            self.step_data_collected = True
            self.override_allowed = False
            self.barcode = "TEST123"
        
        self.update_button_states()
        self.update_labels()
        self.update_status_display()
    
    def simulate_data_collection(self):
        """Simulate data collection"""
        self.step_data_collected = True
        self.override_allowed = True
        self.update_button_states()
        self.update_labels()
        self.update_status_display()
        self.test_action("Data collected for current step")
    
    def advance_step(self):
        """Advance to next step"""
        if self.current_step < len(self.inspection_steps):
            self.current_step += 1
            self.step_data_collected = False
            self.update_button_states()
            self.update_labels()
            self.update_status_display()
            self.test_action(f"Advanced to step {self.current_step}")
    
    def update_button_states(self):
        """Update button states based on current state and logic"""
        # Get current state info
        has_barcode = bool(self.barcode)
        inspection_ongoing = self.inspection_state in [
            self.InspectionState.INSPECTION_ACTIVE, 
            self.InspectionState.STEP_IN_PROGRESS,
            self.InspectionState.STEP_COMPLETED
        ]
        inspection_complete = self.inspection_state == self.InspectionState.INSPECTION_COMPLETED
        all_steps_done = self.current_step >= len(self.inspection_steps)
        
        # === CAPTURE BUTTON ===
        capture_enabled = (
            has_barcode and 
            self.inspection_state in [self.InspectionState.BARCODE_ENTERED, self.InspectionState.DATA_SUBMITTED]
        )
        self.start_inspection_button.setEnabled(capture_enabled)
        
        # === NEXT STEP BUTTON ===  
        next_step_enabled = (
            inspection_ongoing and
            self.current_step < len(self.inspection_steps) and
            self.step_data_collected
        )
        self.next_step_button.setEnabled(next_step_enabled)
        
        # === REPEAT STEP BUTTON ===
        repeat_step_enabled = (
            inspection_ongoing and 
            self.current_step < len(self.inspection_steps)
        )
        self.repeat_step_button.setEnabled(repeat_step_enabled)
        
        # === MANUAL OVERRIDE BUTTON ===
        override_enabled = (
            self.override_allowed and
            (inspection_complete or len(self.inspection_results) > 0) and
            self.inspection_state not in [self.InspectionState.OVERRIDE_APPLIED]
        )
        self.manual_override_button.setEnabled(override_enabled)
        
        # Update tooltips
        self.update_tooltips()
    
    def update_tooltips(self):
        """Update button tooltips"""
        # Capture button
        if not self.barcode:
            self.start_inspection_button.setToolTip("Enter a barcode first")
        elif self.inspection_state == self.InspectionState.BARCODE_ENTERED:
            self.start_inspection_button.setToolTip("Click to start inspection process")
        else:
            self.start_inspection_button.setToolTip("Inspection active or complete")
        
        # Next step button
        if not self.step_data_collected:
            self.next_step_button.setToolTip("Collect data for current step first")
        elif self.current_step >= len(self.inspection_steps):
            self.next_step_button.setToolTip("All steps completed")
        else:
            self.next_step_button.setToolTip("Proceed to next step")
        
        # Repeat step button
        if self.current_step >= len(self.inspection_steps):
            self.repeat_step_button.setToolTip("No active step to repeat")
        else:
            self.repeat_step_button.setToolTip(f"Repeat step {self.current_step + 1}")
        
        # Manual override button
        if not self.override_allowed:
            self.manual_override_button.setToolTip("Override not available in current state")
        else:
            self.manual_override_button.setToolTip("Apply manual override to inspection results")
    
    def update_labels(self):
        """Update info labels"""
        self.state_label.setText(f"Current State: {self.inspection_state}")
        self.step_label.setText(f"Step: {self.current_step}/{len(self.inspection_steps)}")
        self.data_label.setText(f"Data Collected: {self.step_data_collected}")
        self.override_label.setText(f"Override Allowed: {self.override_allowed}")
    
    def update_status_display(self):
        """Update status display"""
        button_states = {
            'Capture': self.start_inspection_button.isEnabled(),
            'Next Step': self.next_step_button.isEnabled(),
            'Repeat Step': self.repeat_step_button.isEnabled(),
            'Manual Override': self.manual_override_button.isEnabled()
        }
        
        status_text = f"=== SMART BUTTON CONTROL STATUS ===\\n"
        status_text += f"State: {self.inspection_state}\\n"
        status_text += f"Step: {self.current_step}/{len(self.inspection_steps)}\\n"
        status_text += f"Barcode: {'Yes' if self.barcode else 'No'}\\n"
        status_text += f"Data Collected: {self.step_data_collected}\\n"
        status_text += f"Override Allowed: {self.override_allowed}\\n\\n"
        
        status_text += "BUTTON STATES:\\n"
        for name, enabled in button_states.items():
            status = "✅ ENABLED " if enabled else "❌ DISABLED"
            status_text += f"  {name}: {status}\\n"
            
        self.status_display.setText(status_text)
    
    def test_action(self, action):
        """Log test action"""
        print(f"🎯 {action}")
        current_text = self.status_display.toPlainText()
        self.status_display.setText(current_text + f"\\n> {action}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MockInspectionWindow()
    window.show()
    
    print("🧪 Smart Button Control System Test")
    print("📊 Use the State Control buttons to change inspection states")
    print("🔘 Watch how the inspection control buttons enable/disable based on logic")
    print("💡 Excluded buttons (Stop, Main Menu, Quit) would always be enabled")
    print("\\n📋 Test Scenarios:")
    print("   1. Start with 'Barcode Entered' → only Capture enabled")
    print("   2. Go to 'Step In Progress' → Repeat Step enabled")
    print("   3. Click 'Collect Data' → Next Step becomes enabled")
    print("   4. Go to 'Inspection Complete' → Manual Override enabled")
    
    sys.exit(app.exec_())