import uiautomation as auto
import time
import pyautogui
import threading
import psutil

class UIAHelper:
    def __init__(self):
        self.element_id_counter = 1
        self.element_ids = {}
        self.is_highlighting = False
        self.highlight_thread = None

    def start_highlighting(self):
        self.is_highlighting = True
        self.highlight_thread = threading.Thread(target=self._highlight_element)
        self.highlight_thread.start()

    def stop_highlighting(self):
        self.is_highlighting = False
        if self.highlight_thread:
            self.highlight_thread.join()

    def _highlight_element(self):
        print("[UIAHelper] Highlight thread started.")
        auto.UIAutomationInitializerInThread()
        while self.is_highlighting:
            try:
                x, y = pyautogui.position()
                element = auto.ControlFromPoint(x, y)
                if element:
                    element.ShowDesktopRectangle(color=0xFF0000, width=3)
            except Exception:
                pass
            time.sleep(0.1)
        print("[UIAHelper] Highlight thread stopped.")

    def get_element_from_point(self, x, y):
        try:
            return auto.ControlFromPoint(x, y)
        except Exception:
            return None

    def get_focused_element(self):
        try:
            return auto.GetFocusedControl()
        except Exception:
            return None

    def get_element_info(self, element):
        if not element:
            return None

        try:
            runtime_id = element.GetRuntimeId()
            if runtime_id not in self.element_ids:
                self.element_ids[runtime_id] = f"element-{self.element_id_counter}"
                self.element_id_counter += 1
            element_id = self.element_ids[runtime_id]
        except Exception:
            return None

        info = {'id': element_id}
        try:
            info['name'] = element.Name
        except Exception:
            info['name'] = 'N/A'
        try:
            pid = element.ProcessId
            # get the name by id
            pname = psutil.Process(pid).name()
            info['process_name'] = pname    
        except Exception:
            info['process_name'] = 'N/A'
        try:
            info['automation_id'] = element.AutomationId
        except Exception:
            info['automation_id'] = 'N/A'
        try:
            info['class_name'] = element.ClassName
        except Exception:
            info['class_name'] = 'N/A'
        try:
            info['control_type'] = element.ControlTypeName
        except Exception:
            info['control_type'] = 'N/A'
        try:
            info['bounding_rectangle'] = element.BoundingRectangle
        except Exception:
            info['bounding_rectangle'] = None
        try:
            info['is_offscreen'] = element.IsOffscreen
        except Exception:
            info['is_offscreen'] = True

        patterns = {}

        try:
            p = element.GetDockPattern()
            patterns['DockPattern'] = {'DockPosition': str(p.DockPosition)}
        except Exception: pass

        try:
            p = element.GetExpandCollapsePattern()
            patterns['ExpandCollapsePattern'] = {'ExpandCollapseState': str(p.ExpandCollapseState)}
        except Exception: pass

        try:
            p = element.GetGridPattern()
            patterns['GridPattern'] = {'RowCount': p.RowCount, 'ColumnCount': p.ColumnCount}
        except Exception: pass

        try:
            p = element.GetGridItemPattern()
            patterns['GridItemPattern'] = {'Row': p.Row, 'Column': p.Column, 'RowSpan': p.RowSpan, 'ColumnSpan': p.ColumnSpan}
        except Exception: pass

        try:
            if element.IsInvokePatternAvailable():
                patterns['InvokePattern'] = {'Available': True}
        except Exception: pass

        try:
            p = element.GetMultipleViewPattern()
            patterns['MultipleViewPattern'] = {'CurrentView': p.CurrentView, 'SupportedViews': p.GetSupportedViews()}
        except Exception: pass

        try:
            p = element.GetRangeValuePattern()
            patterns['RangeValuePattern'] = {
                'Value': p.Value, 'IsReadOnly': p.IsReadOnly, 'LargeChange': p.LargeChange,
                'SmallChange': p.SmallChange, 'Maximum': p.Maximum, 'Minimum': p.Minimum
            }
        except Exception: pass

        try:
            if element.IsScrollItemPatternAvailable():
                patterns['ScrollItemPattern'] = {'Available': True}
        except Exception: pass

        try:
            p = element.GetScrollPattern()
            patterns['ScrollPattern'] = {
                'HorizontalScrollPercent': p.HorizontalScrollPercent, 'VerticalScrollPercent': p.VerticalScrollPercent,
                'HorizontalViewSize': p.HorizontalViewSize, 'VerticalViewSize': p.VerticalViewSize,
                'HorizontallyScrollable': p.HorizontallyScrollable, 'VerticallyScrollable': p.VerticallyScrollable
            }
        except Exception: pass

        try:
            p = element.GetSelectionPattern()
            patterns['SelectionPattern'] = {
                'CanSelectMultiple': p.CanSelectMultiple, 'IsSelectionRequired': p.IsSelectionRequired,
                'Selection': [item.Name for item in p.GetSelection()]
            }
        except Exception: pass

        try:
            p = element.GetSelectionItemPattern()
            patterns['SelectionItemPattern'] = {'IsSelected': p.IsSelected}
        except Exception: pass

        try:
            p = element.GetTablePattern()
            patterns['TablePattern'] = {
                'RowCount': p.RowCount, 'ColumnCount': p.ColumnCount,
                'RowOrColumnMajor': str(p.RowOrColumnMajor)
            }
        except Exception: pass

        try:
            p = element.GetTableItemPattern()
            patterns['TableItemPattern'] = {
                'Row': p.Row, 'Column': p.Column, 'RowSpan': p.RowSpan, 'ColumnSpan': p.ColumnSpan
            }
        except Exception: pass

        try:
            p = element.GetTextPattern()
            patterns['TextPattern'] = {'Text': p.DocumentRange.GetText(256)}
        except Exception: pass

        try:
            p = element.GetTogglePattern()
            patterns['TogglePattern'] = {'ToggleState': str(p.ToggleState)}
        except Exception: pass

        try:
            p = element.GetTransformPattern()
            patterns['TransformPattern'] = {'CanMove': p.CanMove, 'CanResize': p.CanResize, 'CanRotate': p.CanRotate}
        except Exception: pass

        try:
            p = element.GetValuePattern()
            patterns['ValuePattern'] = {'Value': p.Value, 'IsReadOnly': p.IsReadOnly}
        except Exception: pass

        try:
            p = element.GetWindowPattern()
            patterns['WindowPattern'] = {
                'CanMaximize': p.CanMaximize, 'CanMinimize': p.CanMinimize, 'IsModal': p.IsModal,
                'IsTopmost': p.IsTopmost, 'WindowVisualState': str(p.WindowVisualState),
                'WindowInteractionState': str(p.WindowInteractionState)
            }
        except Exception: pass

        info['patterns'] = patterns

        return info

    def get_element_hierarchy(self, element, process_names=None):
        if not element:
            return None
        hierarchy = []
        current = element
        while current:
            info = self.get_element_info(current)
            if info:
                if not process_names or (info.get('process_name') and info['process_name'].lower() in [p.lower() for p in process_names]):
                    hierarchy.append(info)

            try:
                current = current.GetParentControl()
            except Exception:
                current = None
        return hierarchy
