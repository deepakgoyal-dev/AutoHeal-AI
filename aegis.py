"""
AutoHeal AI - Backward Compatibility Alias
Redirects legacy 'aegis' package imports directly to 'detector'.
"""

import sys
import detector

# Register module alias in sys.modules
sys.modules["aegis"] = detector

from detector import (
    PipelineConfig,
    CorruptionDetector,
    SelfHealingEngine,
    HealingLedger,
    HealingAction,
    PlainEnglishInsightEngine,
    VisualAnalyticsGenerator,
    AutoHealPipeline,
    CorruptedDataGenerator,
    ExploratoryDataAnalyzer,
    FeatureEngineer,
    AegisPipeline
)

__all__ = [
    "PipelineConfig",
    "CorruptionDetector",
    "SelfHealingEngine",
    "HealingLedger",
    "HealingAction",
    "PlainEnglishInsightEngine",
    "VisualAnalyticsGenerator",
    "AutoHealPipeline",
    "CorruptedDataGenerator",
    "ExploratoryDataAnalyzer",
    "FeatureEngineer",
    "AegisPipeline"
]
