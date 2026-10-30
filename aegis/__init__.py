"""
AutoHeal AI - Autonomous Self-Healing Data Pipeline & Plain-English Analytics Engine
"""

from .config import PipelineConfig
from .detector import CorruptionDetector
from .healer import SelfHealingEngine
from .ledger import HealingLedger, HealingAction
from .insights import PlainEnglishInsightEngine
from .visualizer import VisualAnalyticsGenerator
from .pipeline import AutoHealPipeline
from .mock_data import CorruptedDataGenerator

__all__ = [
    "PipelineConfig",
    "CorruptionDetector",
    "SelfHealingEngine",
    "HealingLedger",
    "HealingAction",
    "PlainEnglishInsightEngine",
    "VisualAnalyticsGenerator",
    "AutoHealPipeline",
    "CorruptedDataGenerator"
]

# Backward compatibility alias
AegisPipeline = AutoHealPipeline
