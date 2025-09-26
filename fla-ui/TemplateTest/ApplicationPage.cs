using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;

namespace TestAutomationSuite
{
    public class ApplicationPage
    {
        private readonly UIA3Automation automation;
        private readonly Application app;

        public ApplicationPage(UIA3Automation automation, Application app)
        {
            this.automation = automation;
            this.app = app;
        }

        public TextBox Editor => app.WaitFor(automation, Xpaths.NotepadEditor, 5000).AsTextBox();

        public void TypeInEditor(string text)
        {
            Editor.Enter(text);
        }
    }
}