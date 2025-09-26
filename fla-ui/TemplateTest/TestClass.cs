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
            
            var applicationPage = new ApplicationPage(automation, app);

            // Use the application page to interact with the application
            Assert.IsNotNull(applicationPage.Editor, "The editor should be found.");
            applicationPage.TypeInEditor("Hello from FlaUI!");
        }
    }
}