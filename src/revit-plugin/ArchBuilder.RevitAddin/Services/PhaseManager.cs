using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Architecture;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Faz (Phase) yönetimi: oluşturma, listeleme, görünüm ve eleman atama işlemleri.
    /// Tüm yorumlar Türkçedir; kod/identifiers İngilizcedir.
    /// </summary>
    public class PhaseManager
    {
        /// <summary>
        /// Belgede adı verilen fazı güvenli şekilde sağlar. Yoksa oluşturur.
        /// </summary>
        public Phase EnsurePhase(Document document, string phaseName, int? sequenceIndex = null)
        {
            if (document == null) throw new ArgumentNullException(nameof(document));
            if (string.IsNullOrWhiteSpace(phaseName)) throw new ArgumentException("Phase name cannot be empty", nameof(phaseName));

            // Mevcut fazı bul
            var existing = GetAllPhases(document).FirstOrDefault(p => string.Equals(p.Name, phaseName, StringComparison.OrdinalIgnoreCase));
            if (existing != null)
            {
                return existing;
            }

            // Yeni faz oluştur (Transaction gerekir)
            using (var tx = new Transaction(document, $"Create Phase '{phaseName}'"))
            {
                tx.Start();

                // Revit API: Phase.Create(Document)
                var newPhaseId = Phase.Create(document);
                var phase = document.GetElement(newPhaseId) as Phase;
                if (phase == null)
                {
                    tx.RollBack();
                    throw new InvalidOperationException("Failed to create Phase.");
                }

                // İsim ayarla
                phase.Name = phaseName;

                // Sıra indexi istenirse ayarla (mümkün olduğunca)
                if (sequenceIndex.HasValue)
                {
                    try
                    {
                        var all = document.Phases; // PhaseArray
                        // PhaseArray sıralaması kontrolü (salt okunur olabilir). Bu nedenle noop; fazlar Revit UI üzerinden yeniden sıralanır.
                        // Burada yalnızca isim set edilir; sıralama garanti edilmez.
                    }
                    catch
                    {
                        // Yoksay: bazı sürümlerde programatik sıralama desteklenmez.
                    }
                }

                tx.Commit();
                return phase;
            }
        }

        /// <summary>
        /// Belgede tanımlı tüm fazları sıraya göre döndürür.
        /// </summary>
        public IList<Phase> GetAllPhases(Document document)
        {
            if (document == null) throw new ArgumentNullException(nameof(document));

            var phases = new List<Phase>();
            var phaseArray = document.Phases; // PhaseArray
            for (int i = 0; i < phaseArray.Size; i++)
            {
                var p = phaseArray.get_Item(i);
                if (p != null) phases.Add(p);
            }
            // PhaseArray zaten sıralıdır; yine de isimle stabil sıralama ekleyelim
            return phases.OrderBy(p => p.SequenceNumber).ThenBy(p => p.Name).ToList();
        }

        /// <summary>
        /// Görünümün faz ve faz filtresini ayarlar.
        /// </summary>
        public void SetViewPhase(View view, Phase phase, PhaseFilter phaseFilter = null)
        {
            if (view == null) throw new ArgumentNullException(nameof(view));
            if (phase == null) throw new ArgumentNullException(nameof(phase));

            var doc = view.Document;
            using (var tx = new Transaction(doc, $"Set View Phase '{view.Name}' -> '{phase.Name}'"))
            {
                tx.Start();

                // VIEW_PHASE
                var pPhase = view.get_Parameter(BuiltInParameter.VIEW_PHASE);
                if (pPhase != null && !pPhase.IsReadOnly)
                {
                    pPhase.Set(phase.Id);
                }

                // VIEW_PHASE_FILTER
                if (phaseFilter == null)
                {
                    // Uygun bir varsayılan faz filtresi bul: "Show Complete" varsa onu kullan
                    phaseFilter = new FilteredElementCollector(doc)
                        .OfClass(typeof(PhaseFilter))
                        .Cast<PhaseFilter>()
                        .FirstOrDefault(f => string.Equals(f.Name, "Show Complete", StringComparison.OrdinalIgnoreCase))
                        ?? new FilteredElementCollector(doc)
                            .OfClass(typeof(PhaseFilter))
                            .Cast<PhaseFilter>()
                            .FirstOrDefault();
                }

                if (phaseFilter != null)
                {
                    var pFilter = view.get_Parameter(BuiltInParameter.VIEW_PHASE_FILTER);
                    if (pFilter != null && !pFilter.IsReadOnly)
                    {
                        pFilter.Set(phaseFilter.Id);
                    }
                }

                tx.Commit();
            }
        }

        /// <summary>
        /// Bir elemanın oluşturulduğu ve yıkıldığı fazları ayarlar.
        /// </summary>
        public void SetElementPhases(Element element, Phase createdPhase, Phase demolishedPhase = null)
        {
            if (element == null) throw new ArgumentNullException(nameof(element));
            if (createdPhase == null) throw new ArgumentNullException(nameof(createdPhase));

            var doc = element.Document;
            using (var tx = new Transaction(doc, $"Set Element Phases {element.Id.IntegerValue}"))
            {
                tx.Start();

                var pCreated = element.get_Parameter(BuiltInParameter.PHASE_CREATED);
                if (pCreated != null && !pCreated.IsReadOnly)
                {
                    pCreated.Set(createdPhase.Id);
                }

                var pDemo = element.get_Parameter(BuiltInParameter.PHASE_DEMOLISHED);
                if (demolishedPhase != null && pDemo != null && !pDemo.IsReadOnly)
                {
                    pDemo.Set(demolishedPhase.Id);
                }

                tx.Commit();
            }
        }

        /// <summary>
        /// Belirli kategorilerdeki tüm elemanları topluca hedef faza atar.
        /// </summary>
        public int BulkAssignElementsToPhase(Document document, IList<BuiltInCategory> categories, Phase createdPhase, Phase demolishedPhase = null)
        {
            if (document == null) throw new ArgumentNullException(nameof(document));
            if (categories == null || categories.Count == 0) throw new ArgumentException("Categories cannot be empty", nameof(categories));
            if (createdPhase == null) throw new ArgumentNullException(nameof(createdPhase));

            // Kategorilerdeki tüm elemanları topla
            var catFilters = categories.Select(c => new ElementCategoryFilter(c)).Cast<ElementFilter>().ToList();
            var orFilter = new LogicalOrFilter(catFilters);

            var elements = new FilteredElementCollector(document)
                .WhereElementIsNotElementType()
                .WherePasses(orFilter)
                .ToElements();

            int updated = 0;
            using (var tx = new Transaction(document, $"Bulk Assign Phase '{createdPhase.Name}'"))
            {
                tx.Start();

                foreach (var el in elements)
                {
                    var pCreated = el.get_Parameter(BuiltInParameter.PHASE_CREATED);
                    if (pCreated != null && !pCreated.IsReadOnly)
                    {
                        pCreated.Set(createdPhase.Id);
                        updated++;
                    }

                    if (demolishedPhase != null)
                    {
                        var pDemo = el.get_Parameter(BuiltInParameter.PHASE_DEMOLISHED);
                        if (pDemo != null && !pDemo.IsReadOnly)
                        {
                            pDemo.Set(demolishedPhase.Id);
                        }
                    }
                }

                tx.Commit();
            }

            return updated;
        }
    }
}


