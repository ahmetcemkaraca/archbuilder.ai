using Autodesk.Revit.DB;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Service for managing Revit transactions with logging and validation
    /// </summary>
    public class TransactionService : ITransactionService
    {
        private readonly ILogger<TransactionService> _logger;
        private readonly IValidationService _validationService;

        public TransactionService(ILogger<TransactionService> logger, IValidationService validationService)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _validationService = validationService ?? throw new ArgumentNullException(nameof(validationService));
        }

        /// <summary>
        /// Execute operation within a transaction with automatic rollback on failure
        /// </summary>
        public bool ExecuteTransaction(Document document, string transactionName, Action<Transaction> operation, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (string.IsNullOrEmpty(transactionName))
                throw new ArgumentException("Transaction name cannot be null or empty", nameof(transactionName));
            if (operation == null)
                throw new ArgumentNullException(nameof(operation));

            using var scope = _logger.BeginScope("ExecuteTransaction {TransactionName} {CorrelationId}", transactionName, correlationId);

            try
            {
                _logger.LogInformation("Starting transaction: {TransactionName}", transactionName);

                using var transaction = new Transaction(document, transactionName);
                
                if (!transaction.Start())
                {
                    _logger.LogError("Failed to start transaction: {TransactionName}", transactionName);
                    return false;
                }

                try
                {
                    operation(transaction);
                    
                    if (transaction.Commit() != TransactionStatus.Committed)
                    {
                        _logger.LogError("Failed to commit transaction: {TransactionName}", transactionName);
                        return false;
                    }

                    _logger.LogInformation("Transaction completed successfully: {TransactionName}", transactionName);
                    return true;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error during transaction execution: {TransactionName}", transactionName);
                    transaction.RollBack();
                    return false;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error in transaction: {TransactionName}", transactionName);
                return false;
            }
        }

        /// <summary>
        /// Execute operation within a transaction with result
        /// </summary>
        public T ExecuteTransaction<T>(Document document, string transactionName, Func<Transaction, T> operation, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (string.IsNullOrEmpty(transactionName))
                throw new ArgumentException("Transaction name cannot be null or empty", nameof(transactionName));
            if (operation == null)
                throw new ArgumentNullException(nameof(operation));

            using var scope = _logger.BeginScope("ExecuteTransaction<T> {TransactionName} {CorrelationId}", transactionName, correlationId);

            try
            {
                _logger.LogInformation("Starting transaction with result: {TransactionName}", transactionName);

                using var transaction = new Transaction(document, transactionName);
                
                if (!transaction.Start())
                {
                    _logger.LogError("Failed to start transaction: {TransactionName}", transactionName);
                    return default(T);
                }

                try
                {
                    var result = operation(transaction);
                    
                    if (transaction.Commit() != TransactionStatus.Committed)
                    {
                        _logger.LogError("Failed to commit transaction: {TransactionName}", transactionName);
                        return default(T);
                    }

                    _logger.LogInformation("Transaction with result completed successfully: {TransactionName}", transactionName);
                    return result;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error during transaction execution: {TransactionName}", transactionName);
                    transaction.RollBack();
                    return default(T);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error in transaction: {TransactionName}", transactionName);
                return default(T);
            }
        }

        /// <summary>
        /// Create a new transaction with logging
        /// </summary>
        public ITransactionWrapper CreateTransaction(Document document, string transactionName, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (string.IsNullOrEmpty(transactionName))
                throw new ArgumentException("Transaction name cannot be null or empty", nameof(transactionName));

            return new TransactionWrapper(document, transactionName, correlationId, _logger);
        }

        /// <summary>
        /// Validate elements before transaction commit
        /// </summary>
        public ValidationResult ValidateElements(IEnumerable<Element> elements, string correlationId)
        {
            if (elements == null)
                throw new ArgumentNullException(nameof(elements));

            var result = new ValidationResult
            {
                ElementCount = elements.Count()
            };

            try
            {
                _logger.LogInformation("Validating {ElementCount} elements", result.ElementCount);

                foreach (var element in elements)
                {
                    if (element == null)
                    {
                        result.Errors.Add("Null element found in collection");
                        continue;
                    }

                    // Basic element validation
                    if (!element.IsValidObject)
                    {
                        result.Errors.Add($"Element {element.Id} is not valid");
                    }

                    // Additional validation through validation service
                    var elementValidation = _validationService.ValidateElement(element, correlationId);
                    if (!elementValidation.IsValid)
                    {
                        result.Errors.AddRange(elementValidation.Errors);
                    }
                    result.Warnings.AddRange(elementValidation.Warnings);
                }

                result.IsValid = result.Errors.Count == 0;

                _logger.LogInformation("Element validation completed. Valid: {IsValid}, Errors: {ErrorCount}, Warnings: {WarningCount}", 
                    result.IsValid, result.Errors.Count, result.Warnings.Count);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during element validation");
                result.Errors.Add($"Validation error: {ex.Message}");
                result.IsValid = false;
                return result;
            }
        }
    }

    /// <summary>
    /// Transaction wrapper implementation
    /// </summary>
    public class TransactionWrapper : ITransactionWrapper
    {
        private readonly Document _document;
        private readonly string _transactionName;
        private readonly string _correlationId;
        private readonly ILogger _logger;
        private bool _disposed = false;

        public TransactionWrapper(Document document, string transactionName, string correlationId, ILogger logger)
        {
            _document = document ?? throw new ArgumentNullException(nameof(document));
            _transactionName = transactionName ?? throw new ArgumentNullException(nameof(transactionName));
            _correlationId = correlationId ?? throw new ArgumentNullException(nameof(correlationId));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            Transaction = new Transaction(_document, _transactionName);
        }

        public Transaction Transaction { get; private set; }
        public bool IsActive => Transaction?.HasStarted() == true && Transaction?.HasEnded() == false;

        public bool Start()
        {
            if (Transaction == null)
                return false;

            try
            {
                var result = Transaction.Start();
                if (result)
                {
                    _logger.LogInformation("Transaction started: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
                }
                else
                {
                    _logger.LogError("Failed to start transaction: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
                }
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Exception starting transaction: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
                return false;
            }
        }

        public bool Commit()
        {
            if (Transaction == null || !IsActive)
                return false;

            try
            {
                var status = Transaction.Commit();
                var success = status == TransactionStatus.Committed;
                
                if (success)
                {
                    _logger.LogInformation("Transaction committed successfully: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
                }
                else
                {
                    _logger.LogError("Failed to commit transaction: {TransactionName} {CorrelationId} Status: {Status}", _transactionName, _correlationId, status);
                }
                
                return success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Exception committing transaction: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
                return false;
            }
        }

        public void Rollback()
        {
            if (Transaction == null || !IsActive)
                return;

            try
            {
                Transaction.RollBack();
                _logger.LogInformation("Transaction rolled back: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Exception rolling back transaction: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
            }
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                try
                {
                    if (Transaction != null && IsActive)
                    {
                        Rollback();
                    }
                    
                    Transaction?.Dispose();
                    Transaction = null;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Exception disposing transaction: {TransactionName} {CorrelationId}", _transactionName, _correlationId);
                }
                finally
                {
                    _disposed = true;
                }
            }
        }
    }
}
