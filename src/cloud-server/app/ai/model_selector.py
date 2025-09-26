"""
Gelişmiş AI Model Selector
Dil, karmaşıklık, dosya tipi ve cost optimizasyonu ile model seçimi
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, List, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """AI model providers"""
    OPENAI = "openai"
    VERTEX_AI = "vertex_ai"
    AZURE_OPENAI = "azure_openai"


class TaskComplexity(str, Enum):
    """Task karmaşıklık seviyeleri"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisType(str, Enum):
    """Analiz tipi kategorileri"""
    CREATION = "creation"
    VALIDATION = "validation"
    EXISTING_PROJECT_ANALYSIS = "existing_project_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    CODE_COMPLIANCE = "code_compliance"
    COST_ESTIMATION = "cost_estimation"


class ModelConfig:
    """Model konfigürasyon bilgileri"""
    
    def __init__(
        self,
        provider: ModelProvider,
        model_name: str,
        max_tokens: int,
        cost_per_1k_tokens: float,
        languages: List[str],
        specialties: List[str],
        supports_json: bool = True,
        supports_streaming: bool = True,
        supports_multimodal: bool = False
    ):
        self.provider = provider
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.languages = languages
        self.specialties = specialties
        self.supports_json = supports_json
        self.supports_streaming = supports_streaming
        self.supports_multimodal = supports_multimodal


class AdvancedModelSelector:
    """Gelişmiş AI model seçimi sistemi"""
    
    def __init__(self):
        self.model_configs = {
            # OpenAI Models
            "gpt-4-turbo": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4-1106-preview",
                max_tokens=128000,
                cost_per_1k_tokens=0.03,
                languages=["en", "tr", "de", "fr", "es", "it", "pt", "ru"],
                specialties=["complex_reasoning", "code_generation", "architectural_analysis", "multi_format_parsing"],
                supports_multimodal=True
            ),
            "gpt-4": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4",
                max_tokens=8192,
                cost_per_1k_tokens=0.03,
                languages=["en", "tr", "de", "fr", "es"],
                specialties=["architectural_design", "building_codes", "revit_commands"]
            ),
            "gpt-3.5-turbo": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo-16k",
                max_tokens=16384,
                cost_per_1k_tokens=0.002,
                languages=["en", "tr", "de", "fr", "es"],
                specialties=["simple_tasks", "validation", "document_processing"]
            ),
            
            # Vertex AI Models
            "gemini-1.5-pro": ModelConfig(
                provider=ModelProvider.VERTEX_AI,
                model_name="gemini-1.5-pro",
                max_tokens=32768,
                cost_per_1k_tokens=0.0025,
                languages=["en", "tr", "de", "fr", "es", "it", "pt"],
                specialties=["turkish_documents", "building_codes", "cost_optimization", "regulatory_analysis"],
                supports_multimodal=True
            ),
            "gemini-1.5-flash": ModelConfig(
                provider=ModelProvider.VERTEX_AI,
                model_name="gemini-1.5-flash",
                max_tokens=8192,
                cost_per_1k_tokens=0.00125,
                languages=["en", "tr", "de", "fr", "es"],
                specialties=["fast_processing", "simple_validation", "document_parsing"]
            ),
            "gemini-pro": ModelConfig(
                provider=ModelProvider.VERTEX_AI,
                model_name="gemini-1.0-pro",
                max_tokens=32768,
                cost_per_1k_tokens=0.0025,
                languages=["en", "tr", "de", "fr", "es"],
                specialties=["general_tasks", "architectural_prompts"]
            )
        }
        
        # Cost optimization thresholds
        self.cost_thresholds = {
            TaskComplexity.SIMPLE: 0.005,    # Max $0.005 per 1k tokens
            TaskComplexity.MEDIUM: 0.015,    # Max $0.015 per 1k tokens  
            TaskComplexity.HIGH: 0.050,      # Max $0.050 per 1k tokens
            TaskComplexity.CRITICAL: 1.000   # No cost limit for critical tasks
        }
    
    def select_optimal_model(
        self,
        language: str = "en",
        complexity: TaskComplexity = TaskComplexity.SIMPLE,
        analysis_type: AnalysisType = AnalysisType.CREATION,
        file_format: Optional[str] = None,
        document_type: Optional[str] = None,
        estimated_tokens: int = 1000,
        budget_constraint: Optional[float] = None,
        user_preference: Optional[str] = None,
        region: str = "eu"
    ) -> Dict[str, Any]:
        """
        Optimum model seçimi yapar
        
        Args:
            language: Input dili (tr, en, de, fr, es)
            complexity: Task karmaşıklığı
            analysis_type: Analiz tipi
            file_format: Dosya formatı (dwg, dxf, ifc, rvt, pdf)
            document_type: Dokümantasyon tipi
            estimated_tokens: Tahmini token sayısı
            budget_constraint: Maliyet sınırı (USD)
            user_preference: Kullanıcı tercihi
            region: Bölge (eu, us, tr, asia)
        """
        
        # Dil normalize et
        lang = (language or "en").lower()
        
        # Skorlama sistemi
        model_scores = {}
        
        for model_id, config in self.model_configs.items():
            score = 0.0
            reasons = []
            
            # Dil desteği skoru (kritik)
            if lang in config.languages:
                score += 30
                reasons.append(f"Dil desteği: {lang}")
            else:
                score -= 20
                reasons.append(f"Dil desteği eksik: {lang}")
            
            # Task tipi uygunluğu
            task_bonus = self._calculate_task_compatibility(analysis_type, config)
            score += task_bonus
            if task_bonus > 0:
                reasons.append(f"Task uygunluğu: {analysis_type.value}")
            
            # Karmaşıklık uygunluğu
            complexity_bonus = self._calculate_complexity_compatibility(complexity, config)
            score += complexity_bonus
            if complexity_bonus > 0:
                reasons.append(f"Karmaşıklık uygunluğu: {complexity.value}")
            
            # Cost efficiency
            cost_score = self._calculate_cost_efficiency(
                complexity, config, estimated_tokens, budget_constraint
            )
            score += cost_score
            if cost_score > 0:
                reasons.append(f"Maliyet verimliliği: ${config.cost_per_1k_tokens}/1k")
            
            # Dosya formatı desteği
            format_bonus = self._calculate_format_compatibility(file_format, config)
            score += format_bonus
            if format_bonus > 0:
                reasons.append(f"Format desteği: {file_format}")
            
            # Bölgesel optimizasyon
            region_bonus = self._calculate_regional_optimization(region, config, lang)
            score += region_bonus
            if region_bonus > 0:
                reasons.append(f"Bölgesel optimizasyon: {region}")
            
            # Kullanıcı tercihi
            if user_preference and user_preference.lower() in model_id.lower():
                score += 15
                reasons.append("Kullanıcı tercihi")
            
            model_scores[model_id] = {
                "score": score,
                "config": config,
                "reasons": reasons,
                "estimated_cost": (estimated_tokens / 1000) * config.cost_per_1k_tokens
            }
        
        # En yüksek skorlu modeli seç
        best_model_id = max(model_scores.keys(), key=lambda k: model_scores[k]["score"])
        best_config = model_scores[best_model_id]
        
        # Fallback kontrolü
        if best_config["score"] < 20:  # Minimum threshold
            logger.warning(f"Düşük uyumluluk skoru: {best_config['score']}")
            # Default fallback
            best_model_id = "gpt-4-turbo" if complexity in [TaskComplexity.HIGH, TaskComplexity.CRITICAL] else "gemini-1.5-flash"
            best_config = model_scores[best_model_id]
        
        return {
            "provider": best_config["config"].provider.value,
            "model": best_config["config"].model_name,
            "model_id": best_model_id,
            "confidence": min(best_config["score"] / 100, 1.0),
            "estimated_cost_usd": best_config["estimated_cost"],
            "selection_reasons": best_config["reasons"],
            "metadata": {
                "max_tokens": best_config["config"].max_tokens,
                "supports_json": best_config["config"].supports_json,
                "supports_streaming": best_config["config"].supports_streaming,
                "supports_multimodal": best_config["config"].supports_multimodal,
                "languages": best_config["config"].languages,
                "specialties": best_config["config"].specialties
            },
            "alternatives": self._get_alternatives(model_scores, best_model_id)
        }
    
    def _calculate_task_compatibility(self, analysis_type: AnalysisType, config: ModelConfig) -> float:
        """Task tipi ile model uygunluğunu hesapla"""
        
        compatibility_map = {
            AnalysisType.EXISTING_PROJECT_ANALYSIS: {
                "complex_reasoning": 25,
                "architectural_analysis": 30,
                "revit_commands": 20
            },
            AnalysisType.DOCUMENT_ANALYSIS: {
                "turkish_documents": 30,
                "document_processing": 25,
                "multi_format_parsing": 20
            },
            AnalysisType.CODE_COMPLIANCE: {
                "building_codes": 30,
                "regulatory_analysis": 25,
                "architectural_design": 20
            },
            AnalysisType.CREATION: {
                "architectural_design": 25,
                "code_generation": 20,
                "revit_commands": 25
            },
            AnalysisType.VALIDATION: {
                "validation": 30,
                "simple_validation": 25,
                "building_codes": 20
            }
        }
        
        task_bonuses = compatibility_map.get(analysis_type, {})
        total_bonus = 0
        
        for specialty in config.specialties:
            if specialty in task_bonuses:
                total_bonus += task_bonuses[specialty]
        
        return min(total_bonus, 30)  # Max 30 points
    
    def _calculate_complexity_compatibility(self, complexity: TaskComplexity, config: ModelConfig) -> float:
        """Karmaşıklık ile model uygunluğunu hesapla"""
        
        if complexity == TaskComplexity.CRITICAL:
            # Critical tasks need most powerful models
            if config.provider == ModelProvider.OPENAI and "gpt-4" in config.model_name:
                return 25
            elif "gemini-1.5-pro" in config.model_name:
                return 20
            else:
                return -10
        
        elif complexity == TaskComplexity.HIGH:
            if "gpt-4" in config.model_name or "gemini-1.5-pro" in config.model_name:
                return 20
            elif "gpt-3.5" in config.model_name or "gemini-1.5-flash" in config.model_name:
                return 5
            else:
                return 10
        
        elif complexity == TaskComplexity.MEDIUM:
            if "gpt-3.5" in config.model_name or "gemini" in config.model_name:
                return 15
            else:
                return 10
        
        else:  # SIMPLE
            if "gemini-1.5-flash" in config.model_name or "gpt-3.5" in config.model_name:
                return 20
            else:
                return 5
    
    def _calculate_cost_efficiency(
        self, 
        complexity: TaskComplexity, 
        config: ModelConfig, 
        estimated_tokens: int,
        budget_constraint: Optional[float]
    ) -> float:
        """Maliyet verimliliğini hesapla"""
        
        estimated_cost = (estimated_tokens / 1000) * config.cost_per_1k_tokens
        threshold = self.cost_thresholds.get(complexity, 0.05)
        
        # Budget constraint kontrolü
        if budget_constraint and estimated_cost > budget_constraint:
            return -30  # Budget exceeded
        
        # Cost efficiency scoring
        if estimated_cost <= threshold * 0.5:
            return 20  # Very cost efficient
        elif estimated_cost <= threshold:
            return 10  # Cost efficient
        elif estimated_cost <= threshold * 2:
            return -5   # Expensive but acceptable
        else:
            return -15  # Too expensive
    
    def _calculate_format_compatibility(self, file_format: Optional[str], config: ModelConfig) -> float:
        """Dosya formatı uygunluğunu hesapla"""
        
        if not file_format:
            return 0
        
        format_compatibility = {
            "dwg": {"multi_format_parsing": 15, "architectural_analysis": 10},
            "dxf": {"multi_format_parsing": 15, "architectural_analysis": 10},
            "ifc": {"complex_reasoning": 15, "architectural_analysis": 15},
            "rvt": {"revit_commands": 20, "architectural_analysis": 15},
            "pdf": {"document_processing": 15, "turkish_documents": 10}
        }
        
        format_bonuses = format_compatibility.get(file_format.lower(), {})
        total_bonus = 0
        
        for specialty in config.specialties:
            if specialty in format_bonuses:
                total_bonus += format_bonuses[specialty]
        
        return min(total_bonus, 20)  # Max 20 points
    
    def _calculate_regional_optimization(self, region: str, config: ModelConfig, language: str) -> float:
        """Bölgesel optimizasyon skoru"""
        
        # Turkish region preference for Turkish content
        if region == "tr" and language == "tr":
            if config.provider == ModelProvider.VERTEX_AI:
                return 15  # Google has good Turkish support
            elif "turkish_documents" in config.specialties:
                return 10
        
        # EU region preferences
        elif region == "eu":
            if config.provider == ModelProvider.VERTEX_AI:
                return 5  # Google Cloud EU
            elif config.provider == ModelProvider.OPENAI:
                return 3  # OpenAI global
        
        # US region preferences  
        elif region == "us":
            if config.provider == ModelProvider.OPENAI:
                return 5  # OpenAI US-based
            elif config.provider == ModelProvider.VERTEX_AI:
                return 3  # Google Cloud global
        
        return 0
    
    def _get_alternatives(self, model_scores: Dict, selected_model: str) -> List[Dict]:
        """Alternatif model önerileri"""
        
        sorted_models = sorted(
            model_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )
        
        alternatives = []
        for model_id, data in sorted_models[1:4]:  # Top 3 alternatives
            if model_id != selected_model:
                alternatives.append({
                    "model_id": model_id,
                    "provider": data["config"].provider.value,
                    "model": data["config"].model_name,
                    "score": data["score"],
                    "estimated_cost": data["estimated_cost"],
                    "reason": "Alternative option"
                })
        
        return alternatives
    
    # Legacy compatibility
    def select(self, language: str, complexity: str = "simple") -> Dict[str, str]:
        """Legacy method for backward compatibility"""
        
        # Map old complexity values
        complexity_map = {
            "simple": TaskComplexity.SIMPLE,
            "medium": TaskComplexity.MEDIUM, 
            "high": TaskComplexity.HIGH,
            "critical": TaskComplexity.CRITICAL
        }
        
        mapped_complexity = complexity_map.get(complexity.lower(), TaskComplexity.SIMPLE)
        
        result = self.select_optimal_model(
            language=language,
            complexity=mapped_complexity
        )
        
        # Return legacy format
        return {
            "provider": result["provider"],
            "model": result["model"]
        }


# Global instance
model_selector = AdvancedModelSelector()


# Backward compatibility
class ModelSelector(AdvancedModelSelector):
    """Legacy ModelSelector class for compatibility"""
    pass


