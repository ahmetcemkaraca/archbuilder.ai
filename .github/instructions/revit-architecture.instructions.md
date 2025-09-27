---
applyTo: "src/revit-plugin/**/*.cs,src/desktop-app/**/*.cs,src/revit-plugin/**/*Service*.cs,src/revit-plugin/**/*Repository*.cs,src/revit-plugin/**/*Model*.cs"
description: Revit Architecture role — element creation, family management, BIM model structure, geometric operations for ArchBuilder.AI with direct Revit API only.
---

# Revit Architecture Development Guidelines

## Core Principles
As Revit Architecture Developer:
- **REVIT API ONLY**: Use direct Revit API calls for all geometry and element creation
- **NO EXTERNAL ENGINES**: No Dynamo, pyRevit or other external script engines - keep it simple
- **NO AI PROCESSING**: Focus on executing validated layouts from Cloud API Server
- Design efficient element creation patterns with proper transactions and rollback mechanisms
- Implement comprehensive family management and parameter handling systems  
- Create robust geometric validation and constraint checking algorithms
- Build sophisticated BIM model structure with proper element relationships and spatial hierarchy
- Maintain data integrity through proper transaction management and error handling
- Implement performance optimization for large-scale architectural projects
- Follow existing ElementCreationService patterns in the codebase

## Transaction Management Pattern
Follow the existing pattern used in ElementCreationService:

```csharp
public class RevitTransactionManager
{
    private readonly ILogger<RevitTransactionManager> _logger;
    
    public RevitTransactionManager(ILogger<RevitTransactionManager> logger)
    {
        _logger = logger;
    }
    
    public T ExecuteInTransaction<T>(
        Document document, 
        string transactionName, 
        Func<Transaction, T> operation, 
        string correlationId = null)
    {
        using var transaction = new Transaction(document, transactionName);
        transaction.Start();
        
        try
        {
            _logger.LogInformation("Transaction başlatıldı: {TransactionName}", 
                transactionName, correlation_id: correlationId);
            
            var result = operation(transaction);
            
            if (transaction.Commit() == TransactionStatus.Committed)
            {
                _logger.LogInformation("Transaction başarılı: {TransactionName}", 
                    transactionName, correlation_id: correlationId);
                return result;
            }
            else
            {
                _logger.LogWarning("Transaction commit başarısız: {TransactionName}", 
                    transactionName, correlation_id: correlationId);
                throw new InvalidOperationException($"Transaction {transactionName} commit başarısız");
            }
        }
        catch (Exception ex)
        {
            transaction.RollBack();
            _logger.LogError(ex, "Transaction hata ile geri alındı: {TransactionName}", 
                transactionName, correlation_id: correlationId);
            throw;
        }
    }
}
```

## Element Creation Patterns

### Wall Creation with Revit API
```csharp
public class AdvancedElementCreationService : IElementCreationService
{
    private readonly ILogger<AdvancedElementCreationService> _logger;
    private readonly ITransactionService _transactionService;
    private readonly FamilyManager _familyManager;
    
    public AdvancedElementCreationService(
        ILogger<AdvancedElementCreationService> logger,
        ITransactionService transactionService,
        FamilyManager familyManager)
    {
        _logger = logger;
        _transactionService = transactionService;
        _familyManager = familyManager;
    }
    
    public List<Wall> CreateComplexWalls(
        Document document, 
        List<WallDefinition> wallDefinitions, 
        string correlationId)
    {
        var createdWalls = new List<Wall>();
        
        var result = _transactionService.ExecuteTransaction(document, "Create Complex Walls", transaction =>
        {
            foreach (var wallDef in wallDefinitions)
            {
                try
                {
                    Wall wall;
                    
                    // Handle different wall types with direct Revit API
                    if (wallDef.IsCurved && wallDef.CurvePoints?.Count > 2)
                    {
                        // Create curved wall using Revit API
                        wall = CreateCurvedWall(document, wallDef, correlationId);
                    }
                    else if (wallDef.HasComplexProfile)
                    {
                        // Create wall with custom profile
                        wall = CreateProfileWall(document, wallDef, correlationId);
                    }
                    else
                    {
                        // Standard straight wall
                        wall = CreateStraightWall(document, wallDef, correlationId);
                    }
                    
                    if (wall != null)
                    {
                        // Apply advanced parameters
                        ApplyWallParameters(wall, wallDef.Parameters);
                        
                        // Handle wall joins and connections
                        HandleWallConnections(document, wall, wallDef.JoinBehavior);
                        
                        createdWalls.Add(wall);
                        
                        _logger.LogDebug("Karmaşık duvar oluşturuldu", 
                            wall_id: wall.Id.IntegerValue,
                            wall_type: wallDef.WallTypeName,
                            is_curved: wallDef.IsCurved,
                            correlation_id: correlationId);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Karmaşık duvar oluşturma hatası", 
                        wall_definition: wallDef.ToString(),
                        correlation_id: correlationId);
                }
            }
        }, correlationId);
        
        return createdWalls;
    }
    
    private Wall CreateCurvedWall(Document document, WallDefinition wallDef, string correlationId)
    {
        try
        {
            // Create curve from points using Revit API geometry
            var curve = CreateCurveFromPoints(wallDef.CurvePoints);
            
            if (curve == null)
            {
                _logger.LogWarning("Eğrisel duvar için curve oluşturulamadı", correlation_id: correlationId);
                return null;
            }
            
            var wallType = GetWallType(document, wallDef.WallTypeName);
            var level = GetLevel(document, wallDef.LevelName);
            
            // Use Revit API to create curved wall
            var wall = Wall.Create(document, curve, wallType.Id, level.Id, 
                wallDef.Height, 0, false, false);
            
            _logger.LogDebug("Eğrisel duvar oluşturuldu", 
                wall_id: wall?.Id.IntegerValue,
                curve_type: curve.GetType().Name,
                correlation_id: correlationId);
            
            return wall;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Eğrisel duvar oluşturma hatası", correlation_id: correlationId);
            return null;
        }
    }
    
    private Curve CreateCurveFromPoints(List<XYZ> points)
    {
        if (points == null || points.Count < 2)
            return null;
        
        try
        {
            if (points.Count == 2)
            {
                // Simple line
                return Line.CreateBound(points[0], points[1]);
            }
            else if (points.Count == 3)
            {
                // Arc through 3 points
                return Arc.Create(points[0], points[2], points[1]);
            }
            else
            {
                // Spline or complex curve - use NurbSpline
                var nurbs = NurbSpline.CreateCurve(points);
                return nurbs;
            }
        }
        catch (Exception ex)
        {
            // Fallback to line between first and last points
            return Line.CreateBound(points[0], points[points.Count - 1]);
        }
    }
}
```

### Family Management System
```csharp
public class EnhancedFamilyManager
{
    private readonly Document document;
    private readonly ILogger<EnhancedFamilyManager> _logger;
    private readonly Dictionary<string, FamilySymbol> familyCache;
    private readonly ITransactionService _transactionService;
    
    public EnhancedFamilyManager(
        Document document, 
        ITransactionService transactionService,
        ILogger<EnhancedFamilyManager> logger)
    {
        this.document = document;
        this._transactionService = transactionService;
        _logger = logger;
        familyCache = new Dictionary<string, FamilySymbol>();
        
        InitializeFamilyCache();
    }
    
    public async Task<FamilySymbol> GetFamilySymbolAsync(
        string familyName, 
        string typeName = null, 
        string correlationId = null)
    {
        var key = GenerateFamilyKey(familyName, typeName);
        
        _logger.LogDebug("Family symbol aranıyor", 
            family_name: familyName, 
            type_name: typeName, 
            correlation_id: correlationId);
        
        // Cache kontrolü
        if (familyCache.TryGetValue(key, out var cachedSymbol) && IsSymbolValid(cachedSymbol))
        {
            _logger.LogDebug("Family symbol cache'den bulundu", 
                family_key: key, 
                correlation_id: correlationId);
            return cachedSymbol;
        }
        
        // Document'te arama
        var familySymbol = SearchFamilyInDocument(familyName, typeName, correlationId);
        
        if (familySymbol == null)
        {
            // Kütüphaneden yükleme
            familySymbol = await LoadFamilyFromLibrary(familyName, typeName, correlationId);
        }
        
        if (familySymbol != null)
        {
            // Symbol'ü aktive et
            await EnsureFamilySymbolActive(familySymbol, correlationId);
            
            // Cache'e ekle
            familyCache[key] = familySymbol;
            
            _logger.LogInformation("Family symbol başarıyla alındı", 
                family_name: familyName,
                type_name: typeName,
                symbol_id: familySymbol.Id.IntegerValue,
                correlation_id: correlationId);
        }
        else
        {
            _logger.LogWarning("Family symbol bulunamadı", 
                family_name: familyName,
                type_name: typeName,
                correlation_id: correlationId);
        }
        
        return familySymbol;
    }
    
    private async Task<FamilySymbol> LoadFamilyFromLibrary(
        string familyName, 
        string typeName, 
        string correlationId)
    {
        try
        {
            var familyPath = await GetFamilyPathAsync(familyName, correlationId);
            if (string.IsNullOrEmpty(familyPath) || !File.Exists(familyPath))
            {
                _logger.LogWarning("Family dosyası bulunamadı", 
                    family_name: familyName, 
                    expected_path: familyPath,
                    correlation_id: correlationId);
                return null;
            }
            
            return _transactionService.ExecuteTransaction(document, 
                $"Load Family: {familyName}",
                transaction =>
                {
                    var loadOptions = new ArchBuilderFamilyLoadOptions(_logger, correlationId);
                    
                    if (document.LoadFamily(familyPath, loadOptions, out Family family))
                    {
                        _logger.LogInformation("Family başarıyla yüklendi", 
                            family_name: familyName,
                            family_path: familyPath,
                            family_id: family.Id.IntegerValue,
                            correlation_id: correlationId);
                        
                        // Symbol arama
                        var symbolIds = family.GetFamilySymbolIds();
                        foreach (var symbolId in symbolIds)
                        {
                            var symbol = document.GetElement(symbolId) as FamilySymbol;
                            if (typeName == null || symbol.Name.Equals(typeName, StringComparison.OrdinalIgnoreCase))
                            {
                                return symbol;
                            }
                        }
                        
                        _logger.LogWarning("Family yüklendi ancak istenen tip bulunamadı", 
                            family_name: familyName,
                            type_name: typeName,
                            available_types: symbolIds.Count,
                            correlation_id: correlationId);
                    }
                    else
                    {
                        _logger.LogError("Family yüklenemedi", 
                            family_name: familyName,
                            family_path: familyPath,
                            correlation_id: correlationId);
                    }
                    
                    return null;
                },
                correlationId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Family yükleme hatası", 
                family_name: familyName, 
                correlation_id: correlationId);
            return null;
        }
    }
}

public class ArchBuilderFamilyLoadOptions : IFamilyLoadOptions
{
    private readonly ILogger _logger;
    private readonly string _correlationId;
    
    public ArchBuilderFamilyLoadOptions(ILogger logger, string correlationId)
    {
        _logger = logger;
        _correlationId = correlationId;
    }
    
    public bool OnFamilyFound(bool familyInUse, out bool overwriteParameterValues)
    {
        overwriteParameterValues = true;
        _logger.LogDebug("Family zaten kullanımda, parametreler üzerine yazılacak", 
            correlation_id: _correlationId);
        return true;
    }
    
    public bool OnSharedFamilyFound(
        Family sharedFamily, 
        bool familyInUse, 
        out FamilySource source, 
        out bool overwriteParameterValues)
    {
        source = FamilySource.Family;
        overwriteParameterValues = true;
        _logger.LogDebug("Paylaşılan family bulundu, kullanılacak", 
            shared_family_name: sharedFamily.Name,
            correlation_id: _correlationId);
        return true;
    }
}
```

## Geometric Validation System
```csharp
public class RevitGeometricValidator
{
    private readonly ILogger<RevitGeometricValidator> _logger;
    
    public RevitGeometricValidator(ILogger<RevitGeometricValidator> logger)
    {
        _logger = logger;
    }
    
    public ValidationResult ValidateLayout(LayoutResult layout, string correlationId)
    {
        var result = new ValidationResult { IsValid = true };
        
        _logger.LogInformation("Layout geometrik doğrulama başlatılıyor", 
            wall_count: layout.Walls?.Count ?? 0,
            door_count: layout.Doors?.Count ?? 0,
            window_count: layout.Windows?.Count ?? 0,
            room_count: layout.Rooms?.Count ?? 0,
            correlation_id: correlationId);
        
        try
        {
            // 1. Wall intersection validation
            var wallErrors = ValidateWallIntersections(layout.Walls, correlationId);
            result.Errors.AddRange(wallErrors);
            
            // 2. Room geometry validation
            var roomErrors = ValidateRoomGeometry(layout.Rooms, correlationId);
            result.Errors.AddRange(roomErrors);
            
            // 3. Door and window placement validation
            var openingErrors = ValidateOpeningPlacements(layout.Doors, layout.Windows, layout.Walls, correlationId);
            result.Errors.AddRange(openingErrors);
            
            // 4. Building code compliance
            var codeErrors = ValidateBuildingCodeCompliance(layout, correlationId);
            result.Errors.AddRange(codeErrors);
            
            // 5. Revit API limitations check
            var apiLimitErrors = ValidateRevitAPILimitations(layout, correlationId);
            result.Errors.AddRange(apiLimitErrors);
            
            result.IsValid = result.Errors.Count == 0;
            result.Confidence = CalculateGeometricConfidence(layout, result.Errors.Count);
            
            _logger.LogInformation("Layout geometrik doğrulama tamamlandı", 
                is_valid: result.IsValid,
                error_count: result.Errors.Count,
                confidence: result.Confidence,
                correlation_id: correlationId);
            
            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Geometrik doğrulama hatası", correlation_id: correlationId);
            result.IsValid = false;
            result.Errors.Add($"Doğrulama hatası: {ex.Message}");
            return result;
        }
    }
    
    private List<string> ValidateRevitAPILimitations(LayoutResult layout, string correlationId)
    {
        var errors = new List<string>();
        
        // Check curve complexity limits
        foreach (var wall in layout.Walls?.Where(w => w.IsCurved) ?? Enumerable.Empty<WallDefinition>())
        {
            if (wall.CurvePoints?.Count > 100)
            {
                errors.Add($"Duvar {wall.Id}: Çok fazla eğri noktası ({wall.CurvePoints.Count}). Revit API limiti: 100");
            }
            
            // Check curve continuity
            if (wall.CurvePoints?.Count >= 3)
            {
                for (int i = 1; i < wall.CurvePoints.Count - 1; i++)
                {
                    var dist = wall.CurvePoints[i].DistanceTo(wall.CurvePoints[i - 1]);
                    if (dist < 0.01) // 1cm minimum distance
                    {
                        errors.Add($"Duvar {wall.Id}: Çok yakın eğri noktaları tespit edildi (indeks: {i})");
                    }
                }
            }
        }
        
        // Check element count limits
        var totalElements = (layout.Walls?.Count ?? 0) + 
                          (layout.Doors?.Count ?? 0) + 
                          (layout.Windows?.Count ?? 0) + 
                          (layout.Rooms?.Count ?? 0);
        
        if (totalElements > 10000)
        {
            errors.Add($"Toplam element sayısı çok yüksek: {totalElements}. Performans sorunları yaşanabilir.");
        }
        
        return errors;
    }
}
```

## Performance Optimization Strategies
```csharp
public class PerformanceOptimizedCreation
{
    private readonly Document document;
    private readonly ILogger<PerformanceOptimizedCreation> _logger;
    
    public async Task<ElementCreationResult> CreateElementsBatch(
        List<ElementDefinition> elements, 
        string correlationId)
    {
        _logger.LogInformation("Batch element oluşturma başlatıldı", 
            element_count: elements.Count,
            correlation_id: correlationId);
        
        var result = new ElementCreationResult();
        var stopwatch = Stopwatch.StartNew();
        
        try
        {
            // Group elements by type for optimized creation
            var elementGroups = elements.GroupBy(e => e.ElementType).ToList();
            
            // Pre-load all required families to avoid multiple transactions
            await PreloadRequiredFamilies(elements, correlationId);
            
            // Cache frequently used elements
            CacheCommonElements();
            
            foreach (var group in elementGroups)
            {
                switch (group.Key)
                {
                    case ElementType.Wall:
                        var walls = await CreateWallsBatchOptimized(group.Cast<WallDefinition>().ToList(), correlationId);
                        result.CreatedElements.AddRange(walls);
                        break;
                        
                    case ElementType.Door:
                        var doors = await CreateDoorsBatchOptimized(group.Cast<DoorDefinition>().ToList(), correlationId);
                        result.CreatedElements.AddRange(doors);
                        break;
                        
                    case ElementType.Window:
                        var windows = await CreateWindowsBatchOptimized(group.Cast<WindowDefinition>().ToList(), correlationId);
                        result.CreatedElements.AddRange(windows);
                        break;
                }
                
                // Memory cleanup for large batches
                if (result.CreatedElements.Count % 500 == 0)
                {
                    GC.Collect();
                    GC.WaitForPendingFinalizers();
                }
            }
            
            stopwatch.Stop();
            result.ExecutionTimeMs = stopwatch.ElapsedMilliseconds;
            result.Success = true;
            
            _logger.LogInformation("Batch element oluşturma tamamlandı", 
                total_elements: result.CreatedElements.Count,
                execution_time_ms: result.ExecutionTimeMs,
                elements_per_second: Math.Round(result.CreatedElements.Count / (stopwatch.ElapsedMilliseconds / 1000.0), 2),
                correlation_id: correlationId);
            
            return result;
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "Batch element oluşturma hatası", correlation_id: correlationId);
            
            result.Success = false;
            result.ErrorMessage = ex.Message;
            return result;
        }
    }
}
```

## Modern Revit API Features
```csharp
public class ModernRevitFeatures
{
    private readonly Document document;
    private readonly ILogger<ModernRevitFeatures> _logger;
    
    // Toposolid creation (Revit 2024+)
    public async Task<Toposolid> CreateAdvancedToposolid(
        ToposolidDefinition definition, 
        string correlationId)
    {
        _logger.LogInformation("Gelişmiş Toposolid oluşturuluyor", correlation_id: correlationId);
        
        try
        {
            var topoType = GetOrCreateToposolidType(definition.TypeName);
            var level = GetLevel(definition.LevelId);
            
            Toposolid toposolid;
            
            if (definition.CurveLoops?.Any() == true && definition.Points?.Any() == true)
            {
                // Combined creation method
                toposolid = Toposolid.Create(
                    document, 
                    definition.CurveLoops, 
                    definition.Points, 
                    topoType.Id, 
                    level.Id);
            }
            else if (definition.CurveLoops?.Any() == true)
            {
                // Curve-based creation
                toposolid = Toposolid.Create(
                    document, 
                    definition.CurveLoops, 
                    topoType.Id, 
                    level.Id);
            }
            else if (definition.Points?.Any() == true)
            {
                // Point-based creation
                toposolid = Toposolid.Create(
                    document, 
                    definition.Points, 
                    topoType.Id, 
                    level.Id);
            }
            else
            {
                throw new ArgumentException("Toposolid tanımı için curve loops veya points gerekli");
            }
            
            _logger.LogInformation("Gelişmiş Toposolid başarıyla oluşturuldu", 
                toposolid_id: toposolid.Id.IntegerValue,
                correlation_id: correlationId);
            
            return toposolid;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Gelişmiş Toposolid oluşturma hatası", correlation_id: correlationId);
            throw;
        }
    }
    
    // DirectShape with geometry (for complex shapes)
    public DirectShape CreateComplexGeometryWithDirectShape(
        List<GeometryObject> geometryObjects, 
        string correlationId)
    {
        try
        {
            var directShape = DirectShape.CreateElement(
                document, 
                new ElementId(BuiltInCategory.OST_GenericModel));
            
            // Set geometry
            directShape.SetShape(geometryObjects);
            
            _logger.LogInformation("DirectShape ile karmaşık geometri oluşturuldu", 
                shape_id: directShape.Id.IntegerValue,
                geometry_count: geometryObjects.Count,
                correlation_id: correlationId);
            
            return directShape;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "DirectShape oluşturma hatası", correlation_id: correlationId);
            throw;
        }
    }
}
```

## Key Integration Points & Best Practices

### 1. **Revit API Only** 
- Use direct Revit API for all operations
- No external engines (Dynamo, pyRevit, etc.)
- Leverage modern Revit API features (Toposolid, DirectShape, etc.)

### 2. **Transaction Management**
- Wrap all operations in proper transactions
- Use correlation IDs for tracking
- Implement rollback strategies

### 3. **Performance Optimization**
- Batch operations where possible
- Cache frequently used elements
- Memory management for large projects

### 4. **Error Handling**
- Comprehensive logging with English comments
- Graceful fallbacks for complex geometry
- Validation before creation

### 5. **Modern API Features**
- Toposolid for complex topography
- DirectShape for organic geometry
- Enhanced family management
- Improved geometric validation

### 6. **Project Consistency**
- Follow existing ElementCreationService patterns
- Use established dependency injection
- Maintain logging standards
- Consistent parameter handling