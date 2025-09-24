using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Polly;
using Polly.Retry;
using Serilog;

namespace ArchBuilder.Desktop.Services
{
    // Türkçe: Sağlam HTTP istemci — retry, timeout ve standart başlıklar
    public class ApiClient : IDisposable
    {
        private readonly HttpClient _http;
        private readonly AsyncRetryPolicy<HttpResponseMessage> _retryPolicy;
        private readonly JsonSerializerOptions _jsonOptions;

        public string BaseUrl { get; }
        public string? ApiKey { get; set; }
        public string? BearerToken { get; set; }

        public ApiClient(string baseUrl, TimeSpan? timeout = null)
        {
            BaseUrl = baseUrl.TrimEnd('/');
            _http = new HttpClient
            {
                Timeout = timeout ?? TimeSpan.FromSeconds(20)
            };

            _retryPolicy = Policy
                .HandleResult<HttpResponseMessage>(r => (int)r.StatusCode >= 500 || (int)r.StatusCode == 429)
                .WaitAndRetryAsync(3, i => TimeSpan.FromMilliseconds(350 * i),
                    (result, ts, retry, ctx) =>
                    {
                        Log.Warning("HTTP yeniden deneme #{retry} — durum {status}", retry, (int)result.Result.StatusCode);
                    });

            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                WriteIndented = false
            };
        }

        private void ApplyDefaultHeaders(HttpRequestMessage req, string? correlationId)
        {
            if (!string.IsNullOrWhiteSpace(BearerToken))
            {
                req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", BearerToken);
            }
            if (!string.IsNullOrWhiteSpace(ApiKey))
            {
                req.Headers.Add("X-API-Key", ApiKey);
            }
            if (!string.IsNullOrWhiteSpace(correlationId))
            {
                req.Headers.Add("X-Correlation-ID", correlationId);
            }
            req.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
        }

        public async Task<T> GetAsync<T>(string path, string? correlationId = null, CancellationToken ct = default)
        {
            var url = BaseUrl + path;
            using var req = new HttpRequestMessage(HttpMethod.Get, url);
            ApplyDefaultHeaders(req, correlationId);

            var res = await _retryPolicy.ExecuteAsync(() => _http.SendAsync(req, ct));
            await EnsureSuccess(res);
            var json = await res.Content.ReadAsStringAsync(ct);
            return JsonSerializer.Deserialize<T>(json, _jsonOptions)!;
        }

        public async Task<TOut> PostAsync<TIn, TOut>(string path, TIn payload, string? correlationId = null, CancellationToken ct = default)
        {
            var url = BaseUrl + path;
            var body = JsonSerializer.Serialize(payload, _jsonOptions);
            using var req = new HttpRequestMessage(HttpMethod.Post, url)
            {
                Content = new StringContent(body, Encoding.UTF8, "application/json")
            };
            ApplyDefaultHeaders(req, correlationId);

            var res = await _retryPolicy.ExecuteAsync(() => _http.SendAsync(req, ct));
            await EnsureSuccess(res);
            var json = await res.Content.ReadAsStringAsync(ct);
            return JsonSerializer.Deserialize<TOut>(json, _jsonOptions)!;
        }

        private static async Task EnsureSuccess(HttpResponseMessage res)
        {
            if (res.IsSuccessStatusCode) return;
            var body = await res.Content.ReadAsStringAsync();
            throw new HttpRequestException($"HTTP {(int)res.StatusCode}: {body}");
        }

        public void Dispose()
        {
            _http.Dispose();
        }
    }
}

