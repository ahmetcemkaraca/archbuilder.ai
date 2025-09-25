using Autodesk.Revit.DB;
using System;
using System.Collections.Generic;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Interface for Revit transaction management
    /// </summary>
    public interface ITransactionService
    {
        /// <summary>
        /// Execute operation within a transaction with automatic rollback on failure
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="transactionName">Name of the transaction</param>
        /// <param name="operation">Operation to execute</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>True if transaction succeeded</returns>
        bool ExecuteTransaction(Document document, string transactionName, Action<Transaction> operation, string correlationId);

        /// <summary>
        /// Execute operation within a transaction with result
        /// </summary>
        /// <typeparam name="T">Return type</typeparam>
        /// <param name="document">Revit document</param>
        /// <param name="transactionName">Name of the transaction</param>
        /// <param name="operation">Operation to execute</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Result of the operation or default if failed</returns>
        T ExecuteTransaction<T>(Document document, string transactionName, Func<Transaction, T> operation, string correlationId);

        /// <summary>
        /// Create a new transaction with logging
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="transactionName">Name of the transaction</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Transaction wrapper</returns>
        ITransactionWrapper CreateTransaction(Document document, string transactionName, string correlationId);

        /// <summary>
        /// Validate elements before transaction commit
        /// </summary>
        /// <param name="elements">Elements to validate</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Validation result</returns>
        ValidationResult ValidateElements(IEnumerable<Element> elements, string correlationId);
    }

    /// <summary>
    /// Transaction wrapper interface
    /// </summary>
    public interface ITransactionWrapper : IDisposable
    {
        /// <summary>
        /// Start the transaction
        /// </summary>
        /// <returns>True if started successfully</returns>
        bool Start();

        /// <summary>
        /// Commit the transaction
        /// </summary>
        /// <returns>True if committed successfully</returns>
        bool Commit();

        /// <summary>
        /// Rollback the transaction
        /// </summary>
        void Rollback();

        /// <summary>
        /// Check if transaction is active
        /// </summary>
        bool IsActive { get; }

        /// <summary>
        /// Get the underlying Revit transaction
        /// </summary>
        Transaction Transaction { get; }
    }

    /// <summary>
    /// Validation result for element validation
    /// </summary>
    public class ValidationResult
    {
        public bool IsValid { get; set; }
        public List<string> Errors { get; set; } = new List<string>();
        public List<string> Warnings { get; set; } = new List<string>();
        public int ElementCount { get; set; }
    }
}
