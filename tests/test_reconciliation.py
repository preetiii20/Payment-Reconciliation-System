"""
Reconciliation Tests

Unit and integration tests for the reconciliation engine.
Tests cover all mandatory scenarios:
1. Cross-month settlement (payment in November, settled in December)
2. Rounding differences in aggregated amounts
3. Duplicate entries
4. Orphaned refunds
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
from reconciliation import ReconciliationEngine, calculate_aggregate_variance
from data_generator import generate_sample_data


class TestReconciliationEngine:
    """Tests for the main ReconciliationEngine class."""
    
    def test_engine_initialization(self):
        """Test that reconciliation engine initializes correctly."""
        engine = ReconciliationEngine(settlement_window_days=2, rounding_threshold=Decimal("0.01"))
        assert engine.settlement_window_days == 2
        assert engine.rounding_threshold == Decimal("0.01")
        assert len(engine.platform_data) == 0
        assert len(engine.bank_data) == 0
    
    def test_load_platform_data(self):
        """Test loading platform transaction data."""
        engine = ReconciliationEngine()
        
        data = {
            'transaction_id': ['TXN001'],
            'transaction_date': ['2024-11-15 10:00:00'],
            'amount': ['1000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        df = pd.DataFrame(data)
        
        engine.load_platform_data(df)
        assert len(engine.platform_data) == 1
        assert engine.platform_data.iloc[0]['transaction_id'] == 'TXN001'
    
    def test_load_bank_data(self):
        """Test loading bank settlement data."""
        engine = ReconciliationEngine()
        
        data = {
            'settlement_id': ['SETTLE001'],
            'transaction_id': ['TXN001'],
            'settlement_date': ['2024-11-16 10:00:00'],
            'amount': ['1000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        df = pd.DataFrame(data)
        
        engine.load_bank_data(df)
        assert len(engine.bank_data) == 1
        assert engine.bank_data.iloc[0]['settlement_id'] == 'SETTLE001'


class TestMandatoryScenarios:
    """Tests for each mandatory reconciliation scenario."""
    
    def test_cross_month_settlement(self):
        """
        Scenario 1: Payment recorded in November but settled in December.
        Verify that timing differences are correctly identified.
        """
        engine = ReconciliationEngine(settlement_window_days=2)
        
        platform_data = {
            'transaction_id': ['TXN20241130001'],
            'transaction_date': ['2024-11-30 10:15:00'],
            'amount': ['3500.50'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        bank_data = {
            'settlement_id': ['SETTLE202412001'],
            'transaction_id': ['TXN20241130001'],
            'settlement_date': ['2024-12-01 08:45:00'],
            'amount': ['3500.50'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        cross_month = [d for d in discrepancies if d.discrepancy_type == 'CROSS_MONTH_SETTLEMENT']
        assert len(cross_month) > 0, "Cross-month settlement should be detected"
        assert cross_month[0].severity == 'low', "Cross-month should be low severity (valid)"
    
    def test_rounding_differences(self):
        """
        Scenario 2: Rounding difference in aggregated amounts.
        Verify that small discrepancies after aggregation are detected.
        """
        engine = ReconciliationEngine()
        
        platform_data = {
            'transaction_id': ['TXN20241110001', 'TXN20241110002', 'TXN20241110003'],
            'transaction_date': ['2024-11-10 08:00:00', '2024-11-10 08:01:00', '2024-11-10 08:02:00'],
            'amount': ['0.005', '0.005', '0.005'],
            'transaction_type': ['payment', 'payment', 'payment'],
            'status': ['settled', 'settled', 'settled'],
            'currency': ['INR', 'INR', 'INR'],
            'original_transaction_id': ['', '', '']
        }
        
        bank_data = {
            'settlement_id': ['SETTLE202411001', 'SETTLE202411002', 'SETTLE202411003'],
            'transaction_id': ['TXN20241110001', 'TXN20241110002', 'TXN20241110003'],
            'settlement_date': ['2024-11-11 10:00:00', '2024-11-11 10:01:00', '2024-11-11 10:02:00'],
            'amount': ['0.01', '0.01', '0.01'],
            'transaction_type': ['payment', 'payment', 'payment'],
            'status': ['settled', 'settled', 'settled'],
            'currency': ['INR', 'INR', 'INR'],
            'original_transaction_id': ['', '', '']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        amount_mismatches = [d for d in discrepancies if d.discrepancy_type == 'AMOUNT_MISMATCH']
        assert len(amount_mismatches) == 3, "Rounding differences should create amount mismatches"
    
    def test_duplicate_entries(self):
        """
        Scenario 3: Duplicate entries.
        Verify that duplicates are detected and preserved.
        """
        engine = ReconciliationEngine()
        
        platform_data = {
            'transaction_id': ['TXN20241115001', 'TXN20241115001'],
            'transaction_date': ['2024-11-15 14:30:00', '2024-11-15 14:30:00'],
            'amount': ['5000.00', '5000.00'],
            'transaction_type': ['payment', 'payment'],
            'status': ['settled', 'settled'],
            'currency': ['INR', 'INR'],
            'original_transaction_id': ['', '']
        }
        
        bank_data = {
            'settlement_id': ['SETTLE202411001'],
            'transaction_id': ['TXN20241115001'],
            'settlement_date': ['2024-11-16 22:30:00'],
            'amount': ['5000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        duplicates = [d for d in discrepancies if d.discrepancy_type == 'DUPLICATE_PLATFORM']
        assert len(duplicates) > 0, "Duplicates should be detected"
        assert duplicates[0].severity == 'medium', "Duplicate should be medium severity"
    
    def test_orphaned_refund(self):
        """
        Scenario 4: Orphaned refund.
        Verify that refunds with non-existent original_transaction_id are detected.
        """
        engine = ReconciliationEngine()
        
        platform_data = {
            'transaction_id': ['TXN20241120002'],
            'transaction_date': ['2024-11-20 12:00:00'],
            'amount': ['500.00'],
            'transaction_type': ['refund'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['TXN20241115099']  # Doesn't exist
        }
        
        bank_data = {
            'settlement_id': ['SETTLE202411001'],
            'transaction_id': ['TXN20241120002'],
            'settlement_date': ['2024-11-21 22:15:00'],
            'amount': ['500.00'],
            'transaction_type': ['refund'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['TXN20241115099']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        orphaned = [d for d in discrepancies if d.discrepancy_type == 'ORPHANED_REFUND']
        assert len(orphaned) > 0, "Orphaned refund should be detected"
        assert orphaned[0].severity == 'high', "Orphaned refund should be high severity"


class TestDiscrepancyDetection:
    """Tests for individual discrepancy detection methods."""
    
    def test_missing_transaction_detection(self):
        """Test detection of transactions missing in bank."""
        engine = ReconciliationEngine()
        
        platform_data = {
            'transaction_id': ['TXN001'],
            'transaction_date': ['2024-11-15 10:00:00'],
            'amount': ['1000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        bank_data = {
            'settlement_id': ['SETTLE001'],
            'transaction_id': ['TXN999'],
            'settlement_date': ['2024-11-16 10:00:00'],
            'amount': ['2000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        missing = [d for d in discrepancies if d.discrepancy_type == 'MISSING_IN_BANK']
        assert len(missing) > 0, "Missing transaction should be detected"
    
    def test_extra_bank_transaction_detection(self):
        """Test detection of extra bank transactions not in platform."""
        engine = ReconciliationEngine()
        
        platform_data = {
            'transaction_id': ['TXN001'],
            'transaction_date': ['2024-11-15 10:00:00'],
            'amount': ['1000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        bank_data = {
            'settlement_id': ['SETTLE001'],
            'transaction_id': ['TXN999'],
            'settlement_date': ['2024-11-16 10:00:00'],
            'amount': ['2000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        extra = [d for d in discrepancies if d.discrepancy_type == 'EXTRA_IN_BANK']
        assert len(extra) > 0, "Extra bank transaction should be detected"
    
    def test_amount_mismatch_detection(self):
        """Test detection of amount mismatches."""
        engine = ReconciliationEngine()
        
        platform_data = {
            'transaction_id': ['TXN001'],
            'transaction_date': ['2024-11-15 10:00:00'],
            'amount': ['1000.00'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        bank_data = {
            'settlement_id': ['SETTLE001'],
            'transaction_id': ['TXN001'],
            'settlement_date': ['2024-11-16 10:00:00'],
            'amount': ['1000.50'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        mismatch = [d for d in discrepancies if d.discrepancy_type == 'AMOUNT_MISMATCH']
        assert len(mismatch) > 0, "Amount mismatch should be detected"


class TestDecimalArithmetic:
    """Tests for Decimal arithmetic and precision."""
    
    def test_decimal_precision_in_amounts(self):
        """Test that Decimal is used correctly for amounts."""
        engine = ReconciliationEngine()
        
        platform_data = {
            'transaction_id': ['TXN001'],
            'transaction_date': ['2024-11-15 10:00:00'],
            'amount': ['1000.50'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        bank_data = {
            'settlement_id': ['SETTLE001'],
            'transaction_id': ['TXN001'],
            'settlement_date': ['2024-11-16 10:00:00'],
            'amount': ['1000.50'],
            'transaction_type': ['payment'],
            'status': ['settled'],
            'currency': ['INR'],
            'original_transaction_id': ['']
        }
        
        engine.load_platform_data(pd.DataFrame(platform_data))
        engine.load_bank_data(pd.DataFrame(bank_data))
        results, discrepancies = engine.reconcile()
        
        # Should match perfectly with Decimal
        assert len(results) == 1, "Transaction should match with Decimal precision"
        assert len([d for d in discrepancies if d.discrepancy_type == 'AMOUNT_MISMATCH']) == 0


class TestIntegration:
    """Integration tests using generated sample data."""
    
    def test_full_reconciliation_with_sample_data(self):
        """Test full reconciliation using generated sample data."""
        platform_df, bank_df = generate_sample_data()
        
        engine = ReconciliationEngine(settlement_window_days=2)
        engine.load_platform_data(platform_df)
        engine.load_bank_data(bank_df)
        results, discrepancies = engine.reconcile()
        
        assert len(results) > 0, "Should have matched records"
        assert len(discrepancies) > 0, "Should have detected discrepancies"
    
    def test_mandatory_scenarios_in_sample_data(self):
        """Verify all 4 mandatory scenarios are in sample data."""
        platform_df, bank_df = generate_sample_data()
        
        engine = ReconciliationEngine(settlement_window_days=2)
        engine.load_platform_data(platform_df)
        engine.load_bank_data(bank_df)
        results, discrepancies = engine.reconcile()
        
        # Check for each scenario
        has_cross_month = any(d.discrepancy_type == 'CROSS_MONTH_SETTLEMENT' for d in discrepancies)
        has_rounding = any(d.discrepancy_type == 'AMOUNT_MISMATCH' for d in discrepancies)
        has_duplicate = any('DUPLICATE' in d.discrepancy_type for d in discrepancies)
        has_orphaned = any(d.discrepancy_type == 'ORPHANED_REFUND' for d in discrepancies)
        
        assert has_cross_month, "Sample data should have cross-month settlement"
        assert has_rounding, "Sample data should have rounding issue"
        assert has_duplicate, "Sample data should have duplicate"
        assert has_orphaned, "Sample data should have orphaned refund"
        """
        Scenario 3: Duplicate entry in one dataset.
        Verify that duplicates are identified and flagged.
        """
        # Implementation to be added
        pass
    
    def test_orphaned_refunds(self):
        """
        Scenario 4: Refund without matching original transaction.
        Verify that refunds without matching payments are flagged.
        """
        # Implementation to be added
        pass


class TestDiscrepancyDetection:
    """Tests for individual discrepancy detection methods."""
    
    def test_detect_missing_transactions(self):
        """Test detection of transactions in platform but not in bank."""
        # Implementation to be added
        pass
    
    def test_detect_extra_transactions(self):
        """Test detection of transactions in bank but not in platform."""
        # Implementation to be added
        pass
    
    def test_detect_amount_mismatches(self):
        """Test detection of same transaction ID with different amounts."""
        # Implementation to be added
        pass


class TestDataValidation:
    """Tests for data validation functions."""
    
    def test_validate_required_columns(self):
        """Test that validation checks for required columns."""
        # Implementation to be added
        pass
    
    def test_validate_data_types(self):
        """Test that validation checks for correct data types."""
        # Implementation to be added
        pass
    
    def test_handle_malformed_data(self):
        """Test that engine handles malformed data gracefully."""
        # Implementation to be added
        pass


class TestDecimalPrecision:
    """Tests for Decimal precision in financial calculations."""
    
    def test_decimal_arithmetic(self):
        """Test that Decimal arithmetic is precise for financial amounts."""
        # Implementation to be added
        pass
    
    def test_aggregation_rounding(self):
        """Test that aggregation correctly handles rounding."""
        # Implementation to be added
        pass


# Integration tests
class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_reconciliation_workflow(self):
        """Test complete reconciliation from data load to report generation."""
        # Implementation to be added
        pass
    
    def test_reconciliation_with_sample_data(self):
        """Test reconciliation using generated sample data."""
        # Implementation to be added
        pass
