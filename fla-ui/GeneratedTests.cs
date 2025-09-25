using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Conditions;
using FlaUI.UIA3;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using System.Diagnostics;

namespace FlaUI.Generated
{
    [TestClass]
    public class GeneratedTests
    {
        private readonly UIA3Automation _automation = new UIA3Automation();

        [TestCleanup]
        public void Cleanup()
        {
            _automation.Dispose();
        }

        [TestMethod]
        public void GeneratedTest()
        {
            // Test code will be generated here
        }
    }
}