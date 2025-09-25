using Microsoft.VisualStudio.TestTools.UnitTesting;
using FlaUI.Core;
using FlaUI.UIA3;
using FlaUI.Core.AutomationElements;

namespace FlaUI.Generated
{
    [TestClass]
    public class GeneratedTests
    {
        private UIA3Automation automation;
        private Application app;

        [TestInitialize]
        public void Setup()
        {
            automation = new UIA3Automation();
            app = Application.Launch("notepad.exe");
        }

        [TestCleanup]
        public void Teardown()
        {
            app?.Close();
            automation?.Dispose();
        }

        [TestMethod]
        public void TestMethod1()
        {
            // Use the extension method to wait for the editor to appear
            var editor = app.WaitFor(automation, Xpaths.NotepadEditor, 5000);
            Assert.IsNotNull(editor, "The editor should be found.");

            // Type some text into the editor
            var textBox = editor.AsTextBox();
            textBox.Enter("Hello from FlaUI!");
        }
    }
}