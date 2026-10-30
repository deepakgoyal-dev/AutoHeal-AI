"""
AegisData AI - Realistic Corrupted Enterprise Data Generator
Synthesizes high-fidelity enterprise datasets seeded with real-world data degradation modes.
"""

import random
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class CorruptedDataGenerator:
    """
    Generates realistic messy enterprise transaction datasets with multi-vector corruption.
    """

    @staticmethod
    def generate_ecommerce_dataset(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
        """
        Synthesizes an e-commerce order ledger with 12 real-world corruption modes.
        """
        random.seed(seed)
        np.random.seed(seed)

        categories = ["Electronics", "Home & Kitchen", "Apparel", "Beauty & Care", "Sports & Outdoors"]
        regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
        payment_methods = ["Credit Card", "PayPal", "Bank Wire", "Apple Pay"]

        data = []
        base_date = datetime(2023, 1, 1)

        for i in range(n_rows):
            order_id = f"ORD-{10000 + i}"
            customer_id = f"CUST-{random.randint(100, 400)}"
            category = random.choice(categories)
            region = random.choice(regions)
            payment = random.choice(payment_methods)

            # Correlated numerical values
            if category == "Electronics":
                price = round(random.uniform(150.0, 1200.0), 2)
                units = random.randint(1, 4)
            elif category == "Apparel":
                price = round(random.uniform(20.0, 120.0), 2)
                units = random.randint(1, 8)
            else:
                price = round(random.uniform(15.0, 350.0), 2)
                units = random.randint(1, 5)

            discount_pct = round(random.uniform(0.0, 30.0), 1)
            shipping_days = random.randint(1, 7)
            order_date = base_date + timedelta(days=random.randint(0, 360), hours=random.randint(0, 23))
            customer_rating = round(random.uniform(3.0, 5.0), 1)

            data.append({
                " Order_ID ": order_id,  # Header whitespace
                "Customer_ID": customer_id,
                "Transaction_Date": order_date,
                "Product_Category": category,
                "Sales_Region": region,
                "Unit_Price": price,
                "Quantity_Ordered": units,
                "Discount_Rate": discount_pct,
                "Shipping_Days": shipping_days,
                "Payment_Method": payment,
                "Customer_Rating": customer_rating
            })

        df = pd.DataFrame(data).astype(object)

        # ----------------- INJECT MULTI-VECTOR CORRUPTIONS ----------------- #

        # 1. Currency string formatting & noise on Unit_Price
        for idx in range(0, n_rows, 5):
            val = df.at[idx, "Unit_Price"]
            if idx % 15 == 0:
                df.at[idx, "Unit_Price"] = f"${val:,.2f}"
            elif idx % 20 == 0:
                df.at[idx, "Unit_Price"] = f"€ {val:,.2f}"
            elif idx % 25 == 0:
                df.at[idx, "Unit_Price"] = f"{val:,.2f} USD"

        # 2. Hidden sentinel nulls across multiple columns
        sentinels = ["N/A", "-999", "??", "missing", "None", "null", ""]
        for idx in range(3, n_rows, 11):
            df.at[idx, "Unit_Price"] = random.choice(sentinels)
        for idx in range(7, n_rows, 14):
            df.at[idx, "Customer_Rating"] = random.choice(["-999", "N/A", "undefined"])
        for idx in range(5, n_rows, 17):
            df.at[idx, "Discount_Rate"] = random.choice(["??", "null", ""])

        # 3. Percentage strings on Discount_Rate
        for idx in range(2, n_rows, 4):
            val = df.at[idx, "Discount_Rate"]
            if val not in sentinels and not pd.isna(val):
                df.at[idx, "Discount_Rate"] = f" {val}% "

        # 4. Multi-format heterogeneous Timestamps
        for idx in range(n_rows):
            dt = df.at[idx, "Transaction_Date"]
            if isinstance(dt, datetime):
                r = idx % 5
                if r == 0:
                    df.at[idx, "Transaction_Date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                elif r == 1:
                    df.at[idx, "Transaction_Date"] = dt.strftime("%d/%m/%Y")
                elif r == 2:
                    df.at[idx, "Transaction_Date"] = dt.strftime("%b %d, %Y")
                elif r == 3:
                    df.at[idx, "Transaction_Date"] = str(int(dt.timestamp()))
                else:
                    df.at[idx, "Transaction_Date"] = dt.strftime("%Y/%m/%d")

        # 5. Categorical typos & drift
        typo_map = {
            "North America": ["North-America", "north america", "N. America", "North Amerca"],
            "Electronics": ["Electronicss", "electrnics", "ELECTR"],
            "Credit Card": ["Credit-Card", "credit card", "CC"]
        }
        for idx in range(1, n_rows, 18):
            df.at[idx, "Sales_Region"] = random.choice(typo_map["North America"])
        for idx in range(4, n_rows, 22):
            df.at[idx, "Product_Category"] = random.choice(typo_map["Electronics"])

        # 6. Catastrophic Outliers
        outlier_indices = [12, 65, 148, 230, 380]
        for oi in outlier_indices:
            if oi < n_rows:
                df.at[oi, "Unit_Price"] = round(random.uniform(25000.0, 95000.0), 2)
                df.at[oi, "Shipping_Days"] = random.randint(180, 450)

        # 7. Exact Duplicate Records
        dupe_rows = df.iloc[10:15].copy()
        df = pd.concat([df, dupe_rows], ignore_index=True)

        return df

    @staticmethod
    def generate_healthcare_dataset(n_rows: int = 350, seed: int = 101) -> pd.DataFrame:
        """
        Synthesizes clinical patient health records with sensor missingness and lab anomalies.
        """
        random.seed(seed)
        np.random.seed(seed)

        data = []
        for i in range(n_rows):
            patient_id = f"PAT-{20000 + i}"
            age = random.randint(18, 85)
            gender = random.choice(["M", "F", "Other"])
            systolic_bp = round(random.gauss(122, 14), 1)
            cholesterol = round(random.gauss(200, 32), 1)
            bmi = round(random.gauss(26.5, 4.2), 1)
            outcome = "Normal" if systolic_bp < 135 and cholesterol < 220 else "Elevated"

            data.append({
                "patient_id": patient_id,
                "age_years": age,
                "gender": gender,
                "systolic_bp_mmhg": systolic_bp,
                "cholesterol_mg_dl": cholesterol,
                "body_mass_index": bmi,
                "clinical_assessment": outcome
            })

        df = pd.DataFrame(data).astype(object)

        # Inject anomalies
        # Impossible age outlier
        df.at[8, "age_years"] = 380
        df.at[42, "systolic_bp_mmhg"] = 999.0
        # Sentinels
        df.at[15, "body_mass_index"] = "N/A"
        df.at[29, "cholesterol_mg_dl"] = "-999"
        # Typos
        df.at[55, "clinical_assessment"] = "Elevatedd"
        df.at[70, "clinical_assessment"] = "normal"

        return df
