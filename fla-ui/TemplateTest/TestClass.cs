using Microsoft.VisualStudio.TestTools.UnitTesting;
using FlaUI.Core;
using FlaUI.UIA3;
using FlaUI.Core.AutomationElements;

namespace TestAutomationSuite
{
    [TestClass]
    public class TestModule
    {
        private UIA3Automation automation;
        private Application app;

        public TestModule(TestContext testContext)
        {
            Logger.TestContext = testContext;
        }
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
        public void Run()
        {
            Logger.LogInfo("Starting Notepad test");
            // Use the extension method to wait for the editor to appear
            var editor = app.WaitFor(automation, Xpaths.NotepadEditor, 5000);
            Assert.IsNotNull(editor, "The editor should be found.");

            // Type some text into the editor
            var textBox = editor.AsTextBox();
            textBox.Enter("Hello from FlaUI!");
        }
    }
}