using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace ArchBuilder.Desktop.Models
{
    /// <summary>
    /// Revit model verileri
    /// </summary>
    public class RevitModelData
    {
        [Required]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        
        [Required]
        public string ProjectName { get; set; } = string.Empty;
        
        public string RevitVersion { get; set; } = string.Empty;
        
        public DateTime ExtractedAt { get; set; } = DateTime.UtcNow;
        
        public string DocumentTitle { get; set; } = string.Empty;
        
        // Element verileri
        public List<WallData> Walls { get; set; } = new();
        public List<DoorData> Doors { get; set; } = new();
        public List<WindowData> Windows { get; set; } = new();
        public List<RoomData> Rooms { get; set; } = new();
        public List<FloorData> Floors { get; set; } = new();
        public List<RoofData> Roofs { get; set; } = new();
        
        // Model metadata
        public ModelMetadata Metadata { get; set; } = new();
        
        // Geometry bounds
        public BoundingBox3D ModelBounds { get; set; } = new();
    }

    /// <summary>
    /// Lokal olarak kaydedilmiş Revit verisi
    /// </summary>
    public class LocalRevitData
    {
        public string CorrelationId { get; set; } = string.Empty;
        public DateTime SavedAt { get; set; }
        public string ProjectName { get; set; } = string.Empty;
        public string RevitVersion { get; set; } = string.Empty;
        public string DataHash { get; set; } = string.Empty;
        public bool CompressionUsed { get; set; }
        public RevitModelData ModelData { get; set; } = new();
    }

    /// <summary>
    /// Duvar verisi
    /// </summary>
    public class WallData
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public Point3D StartPoint { get; set; } = new();
        public Point3D EndPoint { get; set; } = new();
        public double Height { get; set; }
        public double Thickness { get; set; }
        public string WallType { get; set; } = string.Empty;
        public string Level { get; set; } = string.Empty;
        public bool IsStructural { get; set; }
        public bool IsRoomBounding { get; set; } = true;
        public string WallFunction { get; set; } = string.Empty;
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// Kapı verisi
    /// </summary>
    public class DoorData
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public Point3D Location { get; set; } = new();
        public string HostWallId { get; set; } = string.Empty;
        public double Width { get; set; }
        public double Height { get; set; }
        public string DoorType { get; set; } = string.Empty;
        public double Rotation { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// Pencere verisi
    /// </summary>
    public class WindowData
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public Point3D Location { get; set; } = new();
        public string HostWallId { get; set; } = string.Empty;
        public double Width { get; set; }
        public double Height { get; set; }
        public string WindowType { get; set; } = string.Empty;
        public double SillHeight { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// Oda verisi
    /// </summary>
    public class RoomData
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Number { get; set; } = string.Empty;
        public Point3D Location { get; set; } = new();
        public double Area { get; set; }
        public double Volume { get; set; }
        public string Level { get; set; } = string.Empty;
        public List<Point3D> Boundary { get; set; } = new();
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// Döşeme verisi
    /// </summary>
    public class FloorData
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string FloorType { get; set; } = string.Empty;
        public string Level { get; set; } = string.Empty;
        public double Thickness { get; set; }
        public double Area { get; set; }
        public List<Point3D> Outline { get; set; } = new();
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// Çatı verisi
    /// </summary>
    public class RoofData
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string RoofType { get; set; } = string.Empty;
        public double Area { get; set; }
        public List<Point3D> Outline { get; set; } = new();
        public Dictionary<string, object> Parameters { get; set; } = new();
    }

    /// <summary>
    /// 3D nokta
    /// </summary>
    public class Point3D
    {
        public double X { get; set; }
        public double Y { get; set; }
        public double Z { get; set; }

        public Point3D() { }
        public Point3D(double x, double y, double z = 0)
        {
            X = x; Y = y; Z = z;
        }
    }

    /// <summary>
    /// 3D sınırlayıcı kutu
    /// </summary>
    public class BoundingBox3D
    {
        public Point3D Min { get; set; } = new();
        public Point3D Max { get; set; } = new();
        
        public double Width => Max.X - Min.X;
        public double Height => Max.Y - Min.Y;
        public double Depth => Max.Z - Min.Z;
    }

    /// <summary>
    /// Model metadata bilgileri
    /// </summary>
    public class ModelMetadata
    {
        public string Author { get; set; } = string.Empty;
        public DateTime LastSaved { get; set; }
        public string Units { get; set; } = string.Empty;
        public int TotalElements { get; set; }
        public Dictionary<string, int> ElementCounts { get; set; } = new();
        public Dictionary<string, object> ProjectInfo { get; set; } = new();
    }

    /// <summary>
    /// Lokal veri işlem sonucu
    /// </summary>
    public class LocalDataResult
    {
        public bool Success { get; set; }
        public string CorrelationId { get; set; } = string.Empty;
        public string FilePath { get; set; } = string.Empty;
        public string DataHash { get; set; } = string.Empty;
        public long SizeBytes { get; set; }
        public long? OriginalSizeBytes { get; set; }
        public double? CompressionRatio { get; set; }
        public string Message { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    /// <summary>
    /// Lokal veri dosya bilgisi
    /// </summary>
    public class LocalDataInfo
    {
        public string FilePath { get; set; } = string.Empty;
        public string FileName { get; set; } = string.Empty;
        public long SizeBytes { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime LastModified { get; set; }
    }

    /// <summary>
    /// Cloud upload sonucu
    /// </summary>
    public class CloudUploadResult
    {
        public bool Success { get; set; }
        public string RemotePath { get; set; } = string.Empty;
        public string ETag { get; set; } = string.Empty;
        public long SizeBytes { get; set; }
        public TimeSpan UploadDuration { get; set; }
        public string Message { get; set; } = string.Empty;
        public Dictionary<string, object> Metadata { get; set; } = new();
    }

    /// <summary>
    /// Cloud download sonucu
    /// </summary>
    public class CloudDownloadResult
    {
        public bool Success { get; set; }
        public string LocalPath { get; set; } = string.Empty;
        public long SizeBytes { get; set; }
        public TimeSpan DownloadDuration { get; set; }
        public string Message { get; set; } = string.Empty;
        public string ETag { get; set; } = string.Empty;
    }

    /// <summary>
    /// Cloud sync sonucu
    /// </summary>
    public class CloudSyncResult
    {
        public bool Success { get; set; }
        public string CorrelationId { get; set; } = string.Empty;
        public string LocalPath { get; set; } = string.Empty;
        public string RemotePath { get; set; } = string.Empty;
        public SyncDirection Direction { get; set; }
        public long SizeBytes { get; set; }
        public TimeSpan Duration { get; set; }
        public string Message { get; set; } = string.Empty;
        public bool DataIntegrityVerified { get; set; }
    }

    /// <summary>
    /// Storage kullanım bilgileri
    /// </summary>
    public class StorageUsageInfo
    {
        public long TotalSpaceBytes { get; set; }
        public long UsedSpaceBytes { get; set; }
        public long AvailableSpaceBytes { get; set; }
        public int FileCount { get; set; }
        public DateTime LastUpdated { get; set; }
    }

    /// <summary>
    /// Upload seçenekleri
    /// </summary>
    public class UploadOptions
    {
        public bool OverwriteExisting { get; set; } = false;
        public Dictionary<string, string> Metadata { get; set; } = new();
        public bool VerifyIntegrity { get; set; } = true;
        public TimeSpan? Timeout { get; set; }
    }

    /// <summary>
    /// Sync seçenekleri
    /// </summary>
    public class SyncOptions
    {
        public bool CompressBeforeUpload { get; set; } = true;
        public bool VerifyIntegrity { get; set; } = true;
        public bool DeleteLocalAfterUpload { get; set; } = false;
        public bool CreateBackup { get; set; } = true;
        public Dictionary<string, string> Tags { get; set; } = new();
    }

    /// <summary>
    /// Sync yönü
    /// </summary>
    public enum SyncDirection
    {
        ToCloud,
        FromCloud,
        Bidirectional
    }
}