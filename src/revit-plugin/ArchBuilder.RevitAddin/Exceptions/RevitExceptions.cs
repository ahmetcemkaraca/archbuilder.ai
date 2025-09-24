using System;
using System.Collections.Generic;

namespace ArchBuilder.RevitAddin.Exceptions
{
    /// <summary>
    /// RevitAutoPlan taban istisna sınıfı. Türkçe mesaj destekler, korelasyon kimliği içerir.
    /// </summary>
    public abstract class RevitAutoPlanException : Exception
    {
        public string CorrelationId { get; }
        public string ErrorCode { get; }
        public Dictionary<string, object> Context { get; }
        public DateTime TimestampUtc { get; }

        protected RevitAutoPlanException(
            string message,
            string errorCode,
            string correlationId,
            Exception innerException = null,
            Dictionary<string, object> context = null) : base(message, innerException)
        {
            ErrorCode = errorCode;
            CorrelationId = correlationId;
            Context = context ?? new Dictionary<string, object>();
            TimestampUtc = DateTime.UtcNow;
        }

        public override string ToString()
        {
            return $"[{ErrorCode}] {Message} (CorrelationId={CorrelationId}, Timestamp={TimestampUtc:O})";
        }
    }

    public class RevitAPIException : RevitAutoPlanException
    {
        public string RevitVersion { get; }
        public string DocumentTitle { get; }

        public RevitAPIException(
            string message,
            string correlationId,
            string revitVersion = null,
            string documentTitle = null,
            Exception innerException = null)
            : base(message, "RVT_001", correlationId, innerException)
        {
            RevitVersion = revitVersion;
            DocumentTitle = documentTitle;
        }
    }

    public class RevitTransactionFailedException : RevitAutoPlanException
    {
        public string TransactionName { get; }

        public RevitTransactionFailedException(
            string transactionName,
            string correlationId,
            Exception innerException = null)
            : base($"Revit transaction '{transactionName}' failed", "RVT_002", correlationId, innerException)
        {
            TransactionName = transactionName;
        }
    }
}


