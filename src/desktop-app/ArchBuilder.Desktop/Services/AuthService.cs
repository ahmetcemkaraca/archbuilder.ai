using System;
using System.Threading;
using System.Threading.Tasks;

namespace ArchBuilder.Desktop.Services
{
    // Türkçe: Auth servis — login/refresh ve token yönetimi
    public class AuthService
    {
        private readonly ApiClient _apiClient;

        public AuthService(ApiClient apiClient)
        {
            _apiClient = apiClient;
        }

        public async Task<AuthTokens> LoginAsync(string email, string password, CancellationToken ct = default)
        {
            var req = new LoginRequest { email = email, password = password };
            var res = await _apiClient.PostAsync<LoginRequest, AuthTokenResponse>("/v1/auth/login", req, null, ct);
            var tokens = new AuthTokens
            {
                AccessToken = res.data?.accessToken ?? string.Empty,
                RefreshToken = res.data?.refreshToken ?? string.Empty,
                ExpiresAtUtc = DateTime.UtcNow.AddSeconds(res.data?.expiresInSeconds ?? 0)
            };
            return tokens;
        }

        public async Task<AuthTokens> RefreshAsync(string refreshToken, CancellationToken ct = default)
        {
            var req = new RefreshRequest { token = refreshToken };
            var res = await _apiClient.PostAsync<RefreshRequest, AuthTokenResponse>("/v1/auth/refresh", req, null, ct);
            var tokens = new AuthTokens
            {
                AccessToken = res.data?.accessToken ?? string.Empty,
                RefreshToken = res.data?.refreshToken ?? refreshToken,
                ExpiresAtUtc = DateTime.UtcNow.AddSeconds(res.data?.expiresInSeconds ?? 0)
            };
            return tokens;
        }
    }

    public class LoginRequest { public string email { get; set; } = string.Empty; public string password { get; set; } = string.Empty; }
    public class RefreshRequest { public string token { get; set; } = string.Empty; }

    public class AuthTokenResponse
    {
        public bool success { get; set; }
        public AuthTokenData? data { get; set; }
    }

    public class AuthTokenData
    {
        public string accessToken { get; set; } = string.Empty;
        public string refreshToken { get; set; } = string.Empty;
        public int expiresInSeconds { get; set; }
    }

    public class AuthTokens
    {
        public string AccessToken { get; set; } = string.Empty;
        public string RefreshToken { get; set; } = string.Empty;
        public DateTime ExpiresAtUtc { get; set; }
        public bool IsExpired() => DateTime.UtcNow >= ExpiresAtUtc.AddSeconds(-30);
    }
}


