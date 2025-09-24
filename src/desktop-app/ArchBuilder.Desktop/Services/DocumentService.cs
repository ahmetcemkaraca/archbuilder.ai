using System;
using System.IO;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;

namespace ArchBuilder.Desktop.Services
{
    // Türkçe: Basit chunked upload akışı (init/chunk/complete) ve ilerleme geri çağrısı
    public class DocumentService
    {
        private readonly ApiClient _api;
        public DocumentService(ApiClient api) { _api = api; }

        public async Task UploadFileAsync(string filePath, IProgress<double>? progress = null, string? correlationId = null, CancellationToken ct = default)
        {
            var fileName = Path.GetFileName(filePath);
            var fileSize = new FileInfo(filePath).Length;
            var uploadId = await _api.PostAsync<object, UploadInitResponse>("/v1/storage/upload/init", new { fileName, fileSize }, correlationId, ct);

            const int chunkSize = 1024 * 1024; // 1 MB
            var buffer = new byte[chunkSize];
            long sent = 0;

            using var stream = File.OpenRead(filePath);
            using var sha256 = SHA256.Create();
            int read;
            while ((read = await stream.ReadAsync(buffer, 0, buffer.Length, ct)) > 0)
            {
                sent += read;
                var chunk = new byte[read];
                Array.Copy(buffer, chunk, read);
                var base64 = Convert.ToBase64String(chunk);
                await _api.PostAsync<object, StandardResponse>("/v1/storage/upload/chunk", new { uploadId = uploadId.data.id, data = base64 }, correlationId, ct);
                progress?.Report((double)sent / fileSize);
            }

            var hash = BitConverter.ToString(sha256.ComputeHash(File.ReadAllBytes(filePath))).Replace("-", "").ToLowerInvariant();
            await _api.PostAsync<object, StandardResponse>("/v1/storage/upload/complete", new { uploadId = uploadId.data.id, sha256 = hash }, correlationId, ct);
        }
    }

    public class UploadInitResponse { public bool success { get; set; } public UploadInitData data { get; set; } = new UploadInitData(); }
    public class UploadInitData { public string id { get; set; } = string.Empty; }
    public class StandardResponse { public bool success { get; set; } public object? data { get; set; } }
}


