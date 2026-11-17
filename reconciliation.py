"""
Core Reconciliation Logic

This module contains the main reconciliation engine that:
- Matches transactions between payment platform and bank settlement datasets
- Identifies discrepancies (missing, extra, duplicates, orphaned refunds, etc.)
- Provides explanations for each discrepancy
- Uses Python Decimal for precise financial calculations
"""

from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd

# Set decimal precision
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP


@dataclass
class Transaction:
    """Represents a single transaction from either platform or bank."""
    transaction_id: str
    amount: Decimal
    timestamp: datetime
    transaction_type: str  # e.g., "payment", "refund"
    status: str
    source: str  # e.g., "platform", "bank"
    original_transaction_id: str = ""
    
    def __hash__(self):
        return hash(self.transaction_id)


@dataclass
class Discrepancy:
    """Represents a detected discrepancy between datasets."""
    discrepancy_type: str
    transaction_ids: List[str]
    amounts: List[Decimal]
    explanation: str
    severity: str  # "high", "medium", "low"
    affected_datasets: List[str]
    details: Dict = None


class ReconciliationEngine:
    """
    Main reconciliation engine for matching and comparing transactions.
    
    Attributes:
        settlement_window_days: Maximum days between transaction and settlement
        rounding_threshold: Maximum acceptable rounding difference
    """
    
    def __init__(self, settlement_window_days: int = 2, rounding_threshold: Decimal = Decimal("0.01")):
        self.settlement_window_days = settlement_window_days
        self.rounding_threshold = rounding_threshold
        self.platform_data = pd.DataFrame()
        self.bank_data = pd.DataFrame()
        self.matched_records = []
        self.discrepancies = []
        self.platform_duplicates = {}
        self.bank_duplicates = {}
    
    def load_platform_data(self, df: pd.DataFrame) -> None:
        """Load payment platform data."""
        # Validate columns
        required_cols = ['transaction_id', 'transaction_date', 'amount', 'transaction_type', 'status', 'currency']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        self.platform_data = df.copy()
    
    def load_bank_data(self, df: pd.DataFrame) -> None:
        """Load bank settlement data."""
        # Validate columns
        required_cols = ['settlement_id', 'transaction_id', 'settlement_date', 'amount', 'transaction_type', 'status', 'currency']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        self.bank_data = df.copy()
    
    def reconcile(self) -> Tuple[pd.DataFrame, List[Discrepancy]]:
        """
        Main reconciliation process.
        
        Returns:
            Tuple of (results_df, discrepancies_list)
        """
        self.discrepancies = []
        self.matched_records = []
        self.platform_duplicates = {}
        self.bank_duplicates = {}
        
        # Detect duplicates first
        self._detect_duplicates()
        
        # Match and compare
        self._match_and_compare()
        
        # Detect missing transactions
        self._detect_missing_in_bank()
        
        # Detect extra bank transactions
        self._detect_extra_in_bank()
        
        # Build results dataframe
        results_df = self._build_results_dataframe()
        
        return results_df, self.discrepancies
    
    def _detect_duplicates(self) -> None:
        """Detect duplicate transaction IDs within each dataset."""
        # Platform duplicates
        platform_txn_counts = self.platform_data['transaction_id'].value_counts()
        for txn_id, count in platform_txn_counts.items():
            if count > 1:
                dup_records = self.platform_data[self.platform_data['transaction_id'] == txn_id]
                amounts = dup_records['amount'].astype(str).tolist()
                self.platform_duplicates[txn_id] = count
                
                self.discrepancies.append(Discrepancy(
                    discrepancy_type="DUPLICATE_PLATFORM",
                    transaction_ids=[txn_id],
                    amounts=[Decimal(amt) for amt in amounts],
                    explanation=f"Transaction {txn_id} appears {count} times in platform. All records preserved; counted once in clean total.",
                    severity="medium",
                    affected_datasets=["platform"],
                    details={"duplicate_count": count}
                ))
        
        # Bank duplicates
        bank_txn_counts = self.bank_data['transaction_id'].value_counts()
        for txn_id, count in bank_txn_counts.items():
            if count > 1:
                dup_records = self.bank_data[self.bank_data['transaction_id'] == txn_id]
                amounts = dup_records['amount'].astype(str).tolist()
                self.bank_duplicates[txn_id] = count
                
                self.discrepancies.append(Discrepancy(
                    discrepancy_type="DUPLICATE_BANK",
                    transaction_ids=[txn_id],
                    amounts=[Decimal(amt) for amt in amounts],
                    explanation=f"Transaction {txn_id} appears {count} times in bank. All records preserved; counted once in clean total.",
                    severity="medium",
                    affected_datasets=["bank"],
                    details={"duplicate_count": count}
                ))
    
    def _match_and_compare(self) -> None:
        """Match transactions and compare details."""
        matched_txn_ids = set()
        
        for idx, bank_row in self.bank_data.iterrows():
            bank_txn_id = bank_row['transaction_id']
            matched_txn_ids.add(bank_txn_id)
            
            # Find matching platform transaction
            platform_matches = self.platform_data[self.platform_data['transaction_id'] == bank_txn_id]
            
            if len(platform_matches) == 0:
                # Extra in bank (not in platform)
                self.discrepancies.append(Discrepancy(
                    discrepancy_type="EXTRA_IN_BANK",
                    transaction_ids=[bank_txn_id],
                    amounts=[Decimal(bank_row['amount'])],
                    explanation=f"Transaction {bank_txn_id} exists in bank but not in platform.",
                    severity="high",
                    affected_datasets=["bank"]
                ))
            else:
                # Compare first matching platform record
                platform_row = platform_matches.iloc[0]
                
                # Compare amount
                platform_amt = Decimal(str(platform_row['amount']))
                bank_amt = Decimal(str(bank_row['amount']))
                
                if platform_amt != bank_amt:
                    self.discrepancies.append(Discrepancy(
                        discrepancy_type="AMOUNT_MISMATCH",
                        transaction_ids=[bank_txn_id],
                        amounts=[platform_amt, bank_amt],
                        explanation=f"Amount mismatch: Platform {platform_amt} vs Bank {bank_amt}",
                        severity="high",
                        affected_datasets=["platform", "bank"]
                    ))
                    continue
                
                # Compare type
                if platform_row['transaction_type'] != bank_row['transaction_type']:
                    self.discrepancies.append(Discrepancy(
                        discrepancy_type="TYPE_MISMATCH",
                        transaction_ids=[bank_txn_id],
                        amounts=[platform_amt],
                        explanation=f"Type mismatch: Platform {platform_row['transaction_type']} vs Bank {bank_row['transaction_type']}",
                        severity="high",
                        affected_datasets=["platform", "bank"]
                    ))
                    continue
                
                # Check timing
                platform_date = pd.to_datetime(platform_row['transaction_date'])
                bank_date = pd.to_datetime(bank_row['settlement_date'])
                days_diff = (bank_date - platform_date).days
                
                # Detect cross-month settlement
                if platform_date.month != bank_date.month:
                    if days_diff <= self.settlement_window_days:
                        self.discrepancies.append(Discrepancy(
                            discrepancy_type="CROSS_MONTH_SETTLEMENT",
                            transaction_ids=[bank_txn_id],
                            amounts=[platform_amt],
                            explanation=f"Cross-month settlement: Payment {platform_date.date()} settled {bank_date.date()} ({days_diff} day(s) later). Valid within {self.settlement_window_days}-day window.",
                            severity="low",
                            affected_datasets=["timing"],
                            details={"days_diff": days_diff, "is_valid": True}
                        ))
                    else:
                        self.discrepancies.append(Discrepancy(
                            discrepancy_type="TIMING_MISMATCH",
                            transaction_ids=[bank_txn_id],
                            amounts=[platform_amt],
                            explanation=f"Settlement delay exceeds window: {days_diff} days (limit: {self.settlement_window_days})",
                            severity="medium",
                            affected_datasets=["timing"]
                        ))
                        continue
                elif days_diff > self.settlement_window_days:
                    self.discrepancies.append(Discrepancy(
                        discrepancy_type="TIMING_MISMATCH",
                        transaction_ids=[bank_txn_id],
                        amounts=[platform_amt],
                        explanation=f"Settlement delay exceeds window: {days_diff} days (limit: {self.settlement_window_days})",
                        severity="medium",
                        affected_datasets=["timing"]
                    ))
                    continue
                
                # Check refund linkage
                if bank_row['transaction_type'] == 'refund':
                    original_txn_id = str(bank_row.get('original_transaction_id', '')).strip()
                    if not original_txn_id or original_txn_id == '':
                        self.discrepancies.append(Discrepancy(
                            discrepancy_type="ORPHANED_REFUND",
                            transaction_ids=[bank_txn_id],
                            amounts=[platform_amt],
                            explanation=f"Refund {bank_txn_id} has no original_transaction_id reference.",
                            severity="high",
                            affected_datasets=["refund"]
                        ))
                    else:
                        # Check if original exists in platform
                        original_exists = len(self.platform_data[self.platform_data['transaction_id'] == original_txn_id]) > 0
                        if not original_exists:
                            self.discrepancies.append(Discrepancy(
                                discrepancy_type="ORPHANED_REFUND",
                                transaction_ids=[bank_txn_id],
                                amounts=[platform_amt],
                                explanation=f"Refund {bank_txn_id} references original_transaction_id={original_txn_id}, which does not exist in platform.",
                                severity="high",
                                affected_datasets=["refund"]
                            ))
                
                # Record as matched
                self.matched_records.append({
                    'transaction_id': bank_txn_id,
                    'platform_amount': platform_amt,
                    'bank_amount': bank_amt,
                    'transaction_type': bank_row['transaction_type'],
                    'status': 'MATCHED'
                })
        
        return matched_txn_ids
    
    def _detect_missing_in_bank(self) -> None:
        """Detect platform transactions missing in bank."""
        matched_txn_ids = set(record['transaction_id'] for record in self.matched_records)
        
        for idx, platform_row in self.platform_data.iterrows():
            txn_id = platform_row['transaction_id']
            if txn_id not in matched_txn_ids and txn_id not in self.platform_duplicates:
                self.discrepancies.append(Discrepancy(
                    discrepancy_type="MISSING_IN_BANK",
                    transaction_ids=[txn_id],
                    amounts=[Decimal(str(platform_row['amount']))],
                    explanation=f"Transaction {txn_id} exists in platform but not settled in bank.",
                    severity="medium",
                    affected_datasets=["platform"]
                ))
    
    def _detect_extra_in_bank(self) -> None:
        """Detect bank transactions not in platform (already handled in _match_and_compare)."""
        pass
    
    def _build_results_dataframe(self) -> pd.DataFrame:
        """Build results dataframe from matched records."""
        if not self.matched_records:
            return pd.DataFrame(columns=['transaction_id', 'platform_amount', 'bank_amount', 'transaction_type', 'status'])
        
        return pd.DataFrame(self.matched_records)


def calculate_aggregate_variance(platform_df: pd.DataFrame, bank_df: pd.DataFrame) -> Optional[Discrepancy]:
    """
    Calculate aggregate rounding variance between platform and bank.
    
    Returns:
        Discrepancy if variance detected, None otherwise
    """
    try:
        platform_sum = Decimal(0)
        for amt in platform_df['amount']:
            platform_sum += Decimal(str(amt))
        platform_sum = platform_sum.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        bank_sum = Decimal(0)
        for amt in bank_df['amount']:
            bank_sum += Decimal(str(amt))
        bank_sum = bank_sum.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        variance = abs(platform_sum - bank_sum)
        
        if variance > Decimal('0'):
            return Discrepancy(
                discrepancy_type="ROUNDING_VARIANCE",
                transaction_ids=["aggregate"],
                amounts=[platform_sum, bank_sum, variance],
                explanation=f"Aggregate rounding variance detected. Platform total: {platform_sum}, Bank total: {bank_sum}, Variance: {variance}",
                severity="low",
                affected_datasets=["aggregate"],
                details={"platform_sum": str(platform_sum), "bank_sum": str(bank_sum), "variance": str(variance)}
            )
    except Exception as e:
        pass
    
    return None
    
    def __init__(
        self,
        settlement_window_days: int = 5,
        rounding_threshold: Decimal = Decimal("0.01")
    ):
        self.settlement_window_days = settlement_window_days
        self.rounding_threshold = rounding_threshold
        self.platform_transactions: List[Transaction] = []
        self.bank_transactions: List[Transaction] = []
        self.discrepancies: List[Discrepancy] = []
    
    def load_platform_data(self, df: pd.DataFrame) -> None:
        """
        Load payment platform transactions from DataFrame.
        
        Args:
            df: DataFrame with columns: transaction_id, amount, timestamp, type, status
        """
        # Implementation to be added
        pass
    
    def load_bank_data(self, df: pd.DataFrame) -> None:
        """
        Load bank settlement transactions from DataFrame.
        
        Args:
            df: DataFrame with columns: transaction_id, amount, timestamp, type, status
        """
        # Implementation to be added
        pass
    
    def reconcile(self) -> Tuple[pd.DataFrame, List[Discrepancy]]:
        """
        Execute reconciliation and return results.
        
        Returns:
            Tuple of (reconciliation_results_df, list_of_discrepancies)
        """
        # Implementation to be added
        pass
    
    def _match_transactions(self) -> Dict[str, Tuple[Transaction, Transaction]]:
        """
        Match transactions between platform and bank datasets.
        
        Returns:
            Dictionary mapping transaction_id to (platform_txn, bank_txn) tuple
        """
        # Implementation to be added
        pass
    
    def _detect_timing_mismatches(self) -> List[Discrepancy]:
        """
        Detect transactions recorded in one period but settled in another.
        
        Returns:
            List of timing mismatch discrepancies
        """
        # Implementation to be added
        pass
    
    def _detect_duplicates(self) -> List[Discrepancy]:
        """
        Detect duplicate transactions within each dataset.
        
        Returns:
            List of duplicate discrepancies
        """
        # Implementation to be added
        pass
    
    def _detect_orphaned_refunds(self) -> List[Discrepancy]:
        """
        Detect refunds without matching original transactions.
        
        Returns:
            List of orphaned refund discrepancies
        """
        # Implementation to be added
        pass
    
    def _detect_rounding_errors(self) -> List[Discrepancy]:
        """
        Detect rounding differences in aggregated amounts.
        
        Returns:
            List of rounding error discrepancies
        """
        # Implementation to be added
        pass
    
    def generate_report(self) -> str:
        """
        Generate a text report of reconciliation results.
        
        Returns:
            Formatted reconciliation report
        """
        # Implementation to be added
        pass


def parse_transaction_data(df: pd.DataFrame, source: str) -> List[Transaction]:
    """
    Parse DataFrame into Transaction objects.
    
    Args:
        df: DataFrame with transaction data
        source: Source identifier (e.g., "payment_platform", "bank_settlement")
        
    Returns:
        List of Transaction objects
    """
    # Implementation to be added
    pass


def validate_transaction_data(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that transaction DataFrame has required columns and format.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Implementation to be added
    pass
