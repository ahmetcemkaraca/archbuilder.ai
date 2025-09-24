using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using ArchBuilder.RevitAddin.Services;

namespace ArchBuilder.RevitAddin.Commands
{
    /// <summary>
    /// 'Phase 9' fazını güvence altına alır, aktif görünüm fazını ayarlar ve isteğe bağlı toplu atama yapar.
    /// UI mesajları Türkçedir.
    /// </summary>
    [Transaction(TransactionMode.Manual)]
    public class InitializePhaseNineCommand : IExternalCommand
    {
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var uiapp = commandData.Application;
                var uidoc = uiapp.ActiveUIDocument;
                var doc = uidoc?.Document;
                if (doc == null)
                {
                    message = Resources.Strings.Error_NoActiveDocument;
                    return Result.Failed;
                }

                // Basit korelasyon kimliği üret ve Journal'a yaz (loglama)
                var correlationId = $"RVT_{DateTime.UtcNow:yyyyMMddHHmmss}_{Guid.NewGuid():N}";
                uiapp.Application.WriteJournalComment($"[Phase9] Start - CorrelationId={correlationId}", false);

                // Revit sürüm kontrolü (hedef: 2026)
                var revitVersion = uiapp.Application.VersionNumber;
                if (string.IsNullOrWhiteSpace(revitVersion) || string.Compare(revitVersion, "2026", StringComparison.Ordinal) < 0)
                {
                    TaskDialog.Show(
                        Resources.Strings.Phase9_Title,
                        string.Format(Resources.Strings.Warn_MinVersion, revitVersion, correlationId));
                }

                var phaseManager = new PhaseManager();
                // Fazı güvence altına al
                var phase9 = phaseManager.EnsurePhase(doc, "Phase 9");

                // Aktif görünümü faza ayarla
                var activeView = doc.ActiveView;
                if (activeView == null)
                {
                    message = "Aktif görünüm bulunamadı.";
                    return Result.Failed;
                }

                // Görünüm fazını ayarla (güvenli)
                try
                {
                    phaseManager.SetViewPhase(activeView, phase9);
                }
                catch (Exception setViewEx)
                {
                    uiapp.Application.WriteJournalComment($"[Phase9] SetViewPhase error: {setViewEx.Message}", false);
                    TaskDialog.Show(Resources.Strings.Phase9_Title, string.Format(Resources.Strings.Error_SetViewPhase, setViewEx.Message, correlationId));
                }

                // İsteğe bağlı: yaygın kategorileri Phase 9'a ata (duvar, kapı, pencere, zemin)
                var categories = new List<BuiltInCategory>
                {
                    BuiltInCategory.OST_Walls,
                    BuiltInCategory.OST_Doors,
                    BuiltInCategory.OST_Windows,
                    BuiltInCategory.OST_Floors
                };

                int updated = phaseManager.BulkAssignElementsToPhase(doc, categories, phase9);

                // Kullanıcıya bilgi ver
                TaskDialog.Show(
                    Resources.Strings.Phase9_Title,
                    string.Format(Resources.Strings.Phase9_Info, correlationId, updated));

                uiapp.Application.WriteJournalComment($"[Phase9] Completed - CorrelationId={correlationId} Updated={updated}", false);

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                // Özel istisnaları kullanıcıya anlaşılır şekilde ilet
                message = $"Phase 9 başlatma hatası: {ex.Message}";
                return Result.Failed;
            }
        }
    }
}


