"""
Sample Data Generator

This module generates realistic sample datasets with intentional discrepancies
to test the reconciliation engine. It includes all mandatory test scenarios:
1. Cross-month settlement (payment in November, settled in December)
2. Rounding differences in aggregated amounts
3. Duplicate entries
4. Orphaned refunds
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Tuple, List
import pandas as pd
import os
import numpy as np


def generate_sample_data(random_seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate sample payment platform and bank settlement data.
    
    Returns:
        Tuple of (platform_df, bank_df) DataFrames with test scenarios
    """
    np.random.seed(random_seed)
    
    platform_records = generate_platform_transactions()
    bank_records = generate_bank_transactions()
    
    platform_df = pd.DataFrame(platform_records)
    bank_df = pd.DataFrame(bank_records)
    
    return platform_df, bank_df


def generate_platform_transactions() -> List[dict]:
    """
    Generate sample payment platform transactions.
    
    Returns:
        List of transaction dictionaries
    """
    records = []
    
    # SCENARIO 1: Cross-month settlement (Nov 30 → Dec 1)
    records.append({
        'transaction_id': 'TXN20241130001',
        'transaction_date': '2024-11-30 10:15:00',
        'amount': '3500.50',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    
    # SCENARIO 2: Rounding (3 x ₹0.005)
    records.append({
        'transaction_id': 'TXN20241110001',
        'transaction_date': '2024-11-10 08:00:00',
        'amount': '0.005',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    records.append({
        'transaction_id': 'TXN20241110002',
        'transaction_date': '2024-11-10 08:01:00',
        'amount': '0.005',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    records.append({
        'transaction_id': 'TXN20241110003',
        'transaction_date': '2024-11-10 08:02:00',
        'amount': '0.005',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    
    # SCENARIO 3: Duplicate in platform
    records.append({
        'transaction_id': 'TXN20241115001',
        'transaction_date': '2024-11-15 14:30:00',
        'amount': '5000.00',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    records.append({
        'transaction_id': 'TXN20241115001',
        'transaction_date': '2024-11-15 14:30:00',
        'amount': '5000.00',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    
    # SCENARIO 4: Orphaned refund (original_transaction_id doesn't exist)
    records.append({
        'transaction_id': 'TXN20241120002',
        'transaction_date': '2024-11-20 12:00:00',
        'amount': '500.00',
        'transaction_type': 'refund',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': 'TXN20241115099'
    })
    
    # Normal transactions (realistic dataset)
    normal_transactions = [
        {'txn_id': 'TXN20241101001', 'date': '2024-11-01 09:30:00', 'amt': '1000.00', 'type': 'payment'},
        {'txn_id': 'TXN20241102001', 'date': '2024-11-02 10:00:00', 'amt': '2500.50', 'type': 'payment'},
        {'txn_id': 'TXN20241103001', 'date': '2024-11-03 14:45:00', 'amt': '750.25', 'type': 'payment'},
        {'txn_id': 'TXN20241105001', 'date': '2024-11-05 11:20:00', 'amt': '3200.00', 'type': 'payment'},
        {'txn_id': 'TXN20241106001', 'date': '2024-11-06 16:15:00', 'amt': '450.75', 'type': 'payment'},
        {'txn_id': 'TXN20241108001', 'date': '2024-11-08 13:30:00', 'amt': '5500.00', 'type': 'payment'},
        {'txn_id': 'TXN20241109001', 'date': '2024-11-09 09:45:00', 'amt': '1200.00', 'type': 'payment'},
        {'txn_id': 'TXN20241112001', 'date': '2024-11-12 15:00:00', 'amt': '2000.00', 'type': 'payment'},
        {'txn_id': 'TXN20241114001', 'date': '2024-11-14 10:30:00', 'amt': '800.50', 'type': 'payment'},
        {'txn_id': 'TXN20241118001', 'date': '2024-11-18 12:15:00', 'amt': '1500.00', 'type': 'refund', 'orig': 'TXN20241108001'},
        {'txn_id': 'TXN20241119001', 'date': '2024-11-19 14:00:00', 'amt': '3300.00', 'type': 'payment'},
        {'txn_id': 'TXN20241122001', 'date': '2024-11-22 11:00:00', 'amt': '900.00', 'type': 'payment'},
    ]
    
    for tx in normal_transactions:
        records.append({
            'transaction_id': tx['txn_id'],
            'transaction_date': tx['date'],
            'amount': tx['amt'],
            'transaction_type': tx['type'],
            'status': 'settled',
            'currency': 'INR',
            'original_transaction_id': tx.get('orig', '')
        })
    
    return records


def generate_bank_transactions() -> List[dict]:
    """
    Generate sample bank settlement transactions.
    
    Returns:
        List of transaction dictionaries
    """
    records = []
    settle_id = 1
    
    # SCENARIO 1: Cross-month settlement (Dec 1, settled)
    records.append({
        'settlement_id': f'SETTLE202412{str(settle_id).zfill(3)}',
        'transaction_id': 'TXN20241130001',
        'settlement_date': '2024-12-01 08:45:00',
        'amount': '3500.50',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    settle_id += 1
    
    # SCENARIO 2: Rounding (3 x ₹0.01 after rounding)
    records.append({
        'settlement_id': f'SETTLE202411{str(settle_id).zfill(3)}',
        'transaction_id': 'TXN20241110001',
        'settlement_date': '2024-11-11 10:00:00',
        'amount': '0.01',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    settle_id += 1
    records.append({
        'settlement_id': f'SETTLE202411{str(settle_id).zfill(3)}',
        'transaction_id': 'TXN20241110002',
        'settlement_date': '2024-11-11 10:01:00',
        'amount': '0.01',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    settle_id += 1
    records.append({
        'settlement_id': f'SETTLE202411{str(settle_id).zfill(3)}',
        'transaction_id': 'TXN20241110003',
        'settlement_date': '2024-11-11 10:02:00',
        'amount': '0.01',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    settle_id += 1
    
    # SCENARIO 3: Only one duplicate in bank (TXN20241115001 appears once)
    records.append({
        'settlement_id': f'SETTLE202411{str(settle_id).zfill(3)}',
        'transaction_id': 'TXN20241115001',
        'settlement_date': '2024-11-16 22:30:00',
        'amount': '5000.00',
        'transaction_type': 'payment',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': ''
    })
    settle_id += 1
    
    # SCENARIO 4: Orphaned refund (same non-existent original_transaction_id)
    records.append({
        'settlement_id': f'SETTLE202411{str(settle_id).zfill(3)}',
        'transaction_id': 'TXN20241120002',
        'settlement_date': '2024-11-21 22:15:00',
        'amount': '500.00',
        'transaction_type': 'refund',
        'status': 'settled',
        'currency': 'INR',
        'original_transaction_id': 'TXN20241115099'
    })
    settle_id += 1
    
    # Normal settlements
    normal_settlements = [
        {'txn_id': 'TXN20241101001', 'date': '2024-11-02 22:30:00', 'amt': '1000.00', 'type': 'payment'},
        {'txn_id': 'TXN20241102001', 'date': '2024-11-03 08:45:00', 'amt': '2500.50', 'type': 'payment'},
        {'txn_id': 'TXN20241103001', 'date': '2024-11-04 23:59:00', 'amt': '750.25', 'type': 'payment'},
        {'txn_id': 'TXN20241105001', 'date': '2024-11-06 22:15:00', 'amt': '3200.00', 'type': 'payment'},
        {'txn_id': 'TXN20241106001', 'date': '2024-11-07 10:00:00', 'amt': '450.75', 'type': 'payment'},
        {'txn_id': 'TXN20241108001', 'date': '2024-11-09 22:30:00', 'amt': '5500.00', 'type': 'payment'},
        {'txn_id': 'TXN20241109001', 'date': '2024-11-10 08:15:00', 'amt': '1200.00', 'type': 'payment'},
        {'txn_id': 'TXN20241112001', 'date': '2024-11-13 22:00:00', 'amt': '2000.00', 'type': 'payment'},
        {'txn_id': 'TXN20241114001', 'date': '2024-11-15 10:30:00', 'amt': '800.50', 'type': 'payment'},
        {'txn_id': 'TXN20241118001', 'date': '2024-11-19 22:15:00', 'amt': '1500.00', 'type': 'refund'},
        {'txn_id': 'TXN20241119001', 'date': '2024-11-20 14:00:00', 'amt': '3300.00', 'type': 'payment'},
        {'txn_id': 'TXN20241122001', 'date': '2024-11-23 11:00:00', 'amt': '900.00', 'type': 'payment'},
    ]
    
    for tx in normal_settlements:
        records.append({
            'settlement_id': f'SETTLE202411{str(settle_id).zfill(3)}',
            'transaction_id': tx['txn_id'],
            'settlement_date': tx['date'],
            'amount': tx['amt'],
            'transaction_type': tx['type'],
            'status': 'settled',
            'currency': 'INR',
            'original_transaction_id': ''
        })
        settle_id += 1
    
    return records


def export_sample_data(platform_df: pd.DataFrame, bank_df: pd.DataFrame, 
                       output_dir: str = "data") -> Tuple[str, str]:
    """
    Export generated sample data to CSV files.
    
    Args:
        platform_df: Payment platform transactions DataFrame
        bank_df: Bank settlement transactions DataFrame
        output_dir: Directory to save CSV files
        
    Returns:
        Tuple of (platform_file_path, bank_file_path)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    platform_file = os.path.join(output_dir, 'payment_platform_202411.csv')
    bank_file = os.path.join(output_dir, 'bank_settlement_202411.csv')
    
    platform_df.to_csv(platform_file, index=False)
    bank_df.to_csv(bank_file, index=False)
    
    return platform_file, bank_file


if __name__ == "__main__":
    print("Generating sample data...")
    platform_df, bank_df = generate_sample_data()
    platform_file, bank_file = export_sample_data(platform_df, bank_df)
    print(f"Platform data exported: {platform_file}")
    print(f"Bank data exported: {bank_file}")
    print(f"Platform records: {len(platform_df)}")
    print(f"Bank records: {len(bank_df)}")
    print("Sample data generated successfully!")
