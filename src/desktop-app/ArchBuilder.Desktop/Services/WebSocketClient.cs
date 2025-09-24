using System;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Serilog;

namespace ArchBuilder.Desktop.Services
{
    // Türkçe: Basit yeniden bağlanan WS istemcisi (progress mesajları için)
    public class WebSocketClient : IDisposable
    {
        private ClientWebSocket? _ws;
        private readonly Uri _uri;
        private readonly TimeSpan _reconnectDelay = TimeSpan.FromSeconds(2);
        private CancellationTokenSource? _cts;

        public event Action<string>? OnMessage;
        public event Action<Exception>? OnError;

        public WebSocketClient(string url)
        {
            _uri = new Uri(url);
        }

        public async Task StartAsync(CancellationToken ct = default)
        {
            _cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
            _ = Task.Run(() => LoopAsync(_cts.Token));
        }

        private async Task LoopAsync(CancellationToken ct)
        {
            while (!ct.IsCancellationRequested)
            {
                try
                {
                    _ws?.Dispose();
                    _ws = new ClientWebSocket();
                    await _ws.ConnectAsync(_uri, ct);
                    Log.Information("WS bağlandı: {u}", _uri);

                    var buffer = new byte[8192];
                    while (_ws.State == WebSocketState.Open && !ct.IsCancellationRequested)
                    {
                        var result = await _ws.ReceiveAsync(new ArraySegment<byte>(buffer), ct);
                        if (result.MessageType == WebSocketMessageType.Close)
                        {
                            await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "bye", ct);
                            break;
                        }
                        var msg = Encoding.UTF8.GetString(buffer, 0, result.Count);
                        OnMessage?.Invoke(msg);
                    }
                }
                catch (Exception ex)
                {
                    OnError?.Invoke(ex);
                    Log.Warning(ex, "WS bağlantı hatası, yeniden denenecek");
                }

                await Task.Delay(_reconnectDelay, ct);
            }
        }

        public void Dispose()
        {
            try { _cts?.Cancel(); } catch { }
            try { _ws?.Dispose(); } catch { }
        }
    }
}


