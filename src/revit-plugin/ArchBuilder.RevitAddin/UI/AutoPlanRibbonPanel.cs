using System.Reflection;
using Autodesk.Revit.UI;

namespace ArchBuilder.RevitAddin.UI
{
    /// <summary>
    /// Ribbon panel oluşturur ve komutları ekler. Türkçe ipuçları içerir.
    /// </summary>
    public static class AutoPlanRibbonPanel
    {
        public static void Create(UIControlledApplication application)
        {
            var panel = application.CreateRibbonPanel("AutoPlan AI");

            // Phase 9 başlatma düğmesi
            var phaseBtnData = new PushButtonData(
                "InitializePhaseNine",
                "Phase\n9",
                Assembly.GetExecutingAssembly().Location,
                "ArchBuilder.RevitAddin.Commands.InitializePhaseNineCommand");

            phaseBtnData.ToolTip = Resources.Strings.Ribbon_Phase9_Tooltip;

            panel.AddItem(phaseBtnData);
        }
    }
}


