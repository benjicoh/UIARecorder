import uiautomation as auto
import time
import logging
import _ctypes
from uiautomation import errors  # Correctly import the 'errors' submodule

# Configure logging for better debugging and script flow visibility.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_automation_script():
    """
    Automates the CARTO 3 application workflow. This version includes a robust
    retry loop to handle UI stabilization delays and correct exception handling.
    """
    try:
        # Set a global search timeout. The library will wait up to this duration
        # for any control to appear before raising a LookupError.
        auto.SetGlobalSearchTimeout(25)

        logging.info("Starting automation script...")

        # 1. Find and focus the main application window.
        main_window = auto.WindowControl(searchDepth=1, ClassName='WindowsForms10.Window.8.app.0.bf7771_r3_ad1')
        main_window.SetFocus()
        logging.info("Main application window found and focused.")

        # 2. Click the "New Study" button.
        main_window.ButtonControl(Name='buttonsContainer.newStudyButton').Click(simulateMove=True)
        logging.info("Clicked 'New Study' button.")

        # 3. ROBUST WAIT and CLICK for the "Study" tab.
        # This loop waits for the UI to become fully responsive before proceeding.
        logging.info("Waiting for Study Setup screen to stabilize...")
        study_tab = None
        for i in range(15):  # Retry for up to 15 seconds
            try:
                study_tab = main_window.PaneControl(Name='SETUP_PHASE_NAME_STUDY')
                # Access a property to confirm the control is responsive.
                # This will raise a COMError if the UI is not ready.
                _ = study_tab.Name
                logging.info("Study tab is now responsive.")
                break  # Exit loop if successful
            except (_ctypes.COMError, errors.LookupError):
                logging.info(f"UI not ready yet (attempt {i+1}/15). Waiting...")
                time.sleep(1)
        
        if not study_tab:
            raise errors.LookupError("Could not find a stable 'Study' tab after waiting.")
        
        study_tab.Click(simulateMove=True)
        logging.info("Clicked 'Study' tab.")

        # 4. Fill in Patient Details.
        patient_details_pane = main_window.PaneControl(Name='First Name:')
        edit_fields = patient_details_pane.GetChildren()
        edit_fields[0].EditControl().SetValue('John')
        logging.info("Entered Last Name: John")
        edit_fields[1].EditControl().SetValue('Doe')
        logging.info("Entered First Name: Doe")
        main_window.PaneControl(Name='ID:').EditControl().SetValue('1234')
        logging.info("Entered ID: 1234")

        # 5. Select the procedure template.
        template_pane = main_window.PaneControl(Name='Comments:')
        template_pane.ListItemControl(Name='  Atrial Fibrillation').Click(simulateMove=True)
        logging.info("Selected template category: Atrial Fibrillation.")
        time.sleep(1)
        template_pane.ListItemControl(Name='  Default').Click(simulateMove=True)
        logging.info("Selected template: Default.")
        
        # 6. Navigate to the "Map" setup screen.
        main_window.PaneControl(Name='SETUP_PHASE_NAME_MAP').Click(simulateMove=True)
        logging.info("Clicked 'Map' tab.")

        # 7. Change context to the new map setup form.
        map_setup_form = main_window.WindowControl(Name='MapSetupForm.MapSetupForm')
        logging.info("Found 'MapSetupForm' container.")

        # 8. Configure map settings.
        map_setup_form.ComboBoxControl(Name='Chamber of Interest').Click(simulateMove=True)
        logging.info("Clicked 'Chamber of Interest' dropdown.")
        time.sleep(1)
        auto.ListItemControl(Name='Left Atrium').Click(simulateMove=True)
        logging.info("Selected 'Left Atrium'.")

        # 9. Initialize the study.
        map_setup_form.ButtonControl(Name='studyInitializationControlGrid.initializationButton').Click(simulateMove=True)
        logging.info("Clicked 'Initialize' button.")
        time.sleep(1)

        # 10. Revert context to the main window for the final step.
        main_window.PaneControl(Name='SETUP_PHASE_NAME_MAPPING').Click(simulateMove=True)
        logging.info("Clicked 'Mapping' tab.")

        logging.info("Automation script completed successfully!")

    # CORRECTED EXCEPTION HANDLING
    except errors.LookupError as e:
        logging.error(f"A UI element was not found (LookupError): {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during the automation script: {e}")

if __name__ == '__main__':
    run_automation_script()