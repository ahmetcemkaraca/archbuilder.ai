from __future__ import annotations

import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


@dataclass
class RAGMetrics:
    """TR: RAG metrics veri yapısı"""
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    response_time: float
    confidence_score: float
    query_complexity: str
    timestamp: datetime


@dataclass
class RAGTestScenario:
    """TR: RAG test senaryosu"""
    id: str
    name: str
    query: str
    expected_documents: List[str]
    expected_answer: str
    context: Dict[str, Any]
    difficulty: str  # TR: easy, medium, hard


class RAGMetricsService:
    """TR: RAG metrics ve test harness servisi - P15-T1, P15-T2"""
    
    def __init__(self):
        self._metrics_history: List[RAGMetrics] = []
        self._test_scenarios: List[RAGTestScenario] = []
        self._load_test_scenarios()
    
    def _load_test_scenarios(self) -> None:
        """TR: Test senaryolarını yükle - P15-T2"""
        try:
            # TR: Temel test senaryoları
            scenarios = [
                RAGTestScenario(
                    id="scenario_001",
                    name="TR: Basit mimari terim sorusu",
                    query="Revit'te duvar oluşturma nasıl yapılır?",
                    expected_documents=["revit_wall_creation.pdf", "basic_revit_guide.pdf"],
                    expected_answer="Revit'te duvar oluşturmak için Wall komutunu kullanabilirsiniz",
                    context={"building_type": "residential", "tool": "revit"},
                    difficulty="easy"
                ),
                RAGTestScenario(
                    id="scenario_002",
                    name="TR: Kompleks bina kodları sorusu",
                    query="Türkiye'de konut yapıları için minimum oda alanı gereksinimleri nelerdir?",
                    expected_documents=["turkish_building_codes.pdf", "residential_standards.pdf"],
                    expected_answer="Türkiye'de konut yapıları için minimum oda alanı 5m² olmalıdır",
                    context={"region": "TR", "building_type": "residential", "code_type": "area"},
                    difficulty="medium"
                ),
                RAGTestScenario(
                    id="scenario_003",
                    name="TR: Karmaşık geometri analizi",
                    query="Çok katlı bina için optimal yapısal sistem seçimi nasıl yapılır?",
                    expected_documents=["structural_systems.pdf", "multi_story_design.pdf", "engineering_analysis.pdf"],
                    expected_answer="Çok katlı binalar için betonarme veya çelik yapı sistemleri önerilir",
                    context={"building_type": "commercial", "floors": "multi", "analysis_type": "structural"},
                    difficulty="hard"
                ),
                RAGTestScenario(
                    id="scenario_004",
                    name="TR: Dynamo script optimizasyonu",
                    query="Dynamo'da büyük veri setleri için performans optimizasyonu nasıl yapılır?",
                    expected_documents=["dynamo_performance.pdf", "large_datasets.pdf", "optimization_techniques.pdf"],
                    expected_answer="Dynamo'da performans için DataShapes ve List.Clean kullanılmalı",
                    context={"tool": "dynamo", "topic": "performance", "data_size": "large"},
                    difficulty="hard"
                ),
                RAGTestScenario(
                    id="scenario_005",
                    name="TR: Basit malzeme seçimi",
                    query="Konut yapısı için hangi beton sınıfı kullanılmalı?",
                    expected_documents=["concrete_classes.pdf", "residential_materials.pdf"],
                    expected_answer="Konut yapıları için C25/30 beton sınıfı yeterlidir",
                    context={"building_type": "residential", "material": "concrete"},
                    difficulty="easy"
                )
            ]
            
            self._test_scenarios = scenarios
            logger.info(f"TR: {len(scenarios)} test senaryosu yüklendi")
            
        except Exception as e:
            logger.error(f"TR: Test senaryoları yükleme hatası: {e}")
            self._test_scenarios = []
    
    async def calculate_precision_recall(
        self,
        retrieved_documents: List[str],
        relevant_documents: List[str]
    ) -> Tuple[float, float]:
        """TR: Precision ve Recall hesapla - P15-T1"""
        try:
            if not retrieved_documents:
                return 0.0, 0.0
            
            # TR: Intersection hesapla
            relevant_retrieved = set(retrieved_documents) & set(relevant_documents)
            
            # TR: Precision = relevant retrieved / total retrieved
            precision = len(relevant_retrieved) / len(retrieved_documents) if retrieved_documents else 0.0
            
            # TR: Recall = relevant retrieved / total relevant
            recall = len(relevant_retrieved) / len(relevant_documents) if relevant_documents else 0.0
            
            return precision, recall
            
        except Exception as e:
            logger.error(f"TR: Precision/Recall hesaplama hatası: {e}")
            return 0.0, 0.0
    
    def calculate_f1_score(self, precision: float, recall: float) -> float:
        """TR: F1 Score hesapla"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def calculate_accuracy(self, correct_answers: int, total_answers: int) -> float:
        """TR: Accuracy hesapla"""
        if total_answers == 0:
            return 0.0
        return correct_answers / total_answers
    
    async def run_test_scenario(
        self,
        scenario: RAGTestScenario,
        rag_client: Any  # TR: RAG client interface
    ) -> RAGMetrics:
        """TR: Tek test senaryosu çalıştır"""
        try:
            start_time = datetime.now()
            
            # TR: RAG query çalıştır
            rag_response = await rag_client.query(
                query=scenario.query,
                context=scenario.context,
                max_results=10
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # TR: Retrieved documents
            retrieved_docs = [doc.get("id", "") for doc in rag_response.get("documents", [])]
            
            # TR: Metrics hesapla
            precision, recall = await self.calculate_precision_recall(
                retrieved_docs, scenario.expected_documents
            )
            
            f1_score = self.calculate_f1_score(precision, recall)
            
            # TR: Answer accuracy (basit string matching)
            predicted_answer = rag_response.get("answer", "")
            answer_accuracy = 1.0 if scenario.expected_answer.lower() in predicted_answer.lower() else 0.0
            
            # TR: Confidence score (RAG response'tan)
            confidence_score = rag_response.get("confidence", 0.5)
            
            metrics = RAGMetrics(
                precision=precision,
                recall=recall,
                f1_score=f1_score,
                accuracy=answer_accuracy,
                response_time=response_time,
                confidence_score=confidence_score,
                query_complexity=scenario.difficulty,
                timestamp=datetime.now()
            )
            
            # TR: Metrics'i history'ye ekle
            self._metrics_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"TR: Test senaryosu çalıştırma hatası: {e}")
            # TR: Hata durumunda default metrics döndür
            return RAGMetrics(
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                accuracy=0.0,
                response_time=0.0,
                confidence_score=0.0,
                query_complexity=scenario.difficulty,
                timestamp=datetime.now()
            )
    
    async def run_comprehensive_tests(
        self,
        rag_client: Any,
        difficulty_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """TR: Kapsamlı RAG testleri çalıştır"""
        try:
            # TR: Test senaryolarını filtrele
            scenarios_to_run = self._test_scenarios
            if difficulty_filter:
                scenarios_to_run = [s for s in scenarios_to_run if s.difficulty == difficulty_filter]
            
            logger.info(f"TR: {len(scenarios_to_run)} test senaryosu çalıştırılıyor")
            
            # TR: Paralel olarak test senaryolarını çalıştır
            tasks = [
                self.run_test_scenario(scenario, rag_client)
                for scenario in scenarios_to_run
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # TR: Sonuçları analiz et
            valid_results = [r for r in results if isinstance(r, RAGMetrics)]
            failed_count = len(results) - len(valid_results)
            
            if not valid_results:
                return {
                    "success": False,
                    "error": "TR: Tüm test senaryoları başarısız",
                    "total_scenarios": len(scenarios_to_run),
                    "failed_count": failed_count
                }
            
            # TR: Aggregate metrics hesapla
            aggregate_metrics = self._calculate_aggregate_metrics(valid_results)
            
            # TR: Difficulty bazlı analiz
            difficulty_analysis = self._analyze_by_difficulty(valid_results)
            
            return {
                "success": True,
                "total_scenarios": len(scenarios_to_run),
                "successful_scenarios": len(valid_results),
                "failed_scenarios": failed_count,
                "aggregate_metrics": aggregate_metrics,
                "difficulty_analysis": difficulty_analysis,
                "individual_results": [
                    {
                        "scenario_id": scenarios_to_run[i].id,
                        "scenario_name": scenarios_to_run[i].name,
                        "metrics": {
                            "precision": r.precision,
                            "recall": r.recall,
                            "f1_score": r.f1_score,
                            "accuracy": r.accuracy,
                            "response_time": r.response_time,
                            "confidence_score": r.confidence_score
                        }
                    }
                    for i, r in enumerate(valid_results)
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"TR: Kapsamlı test çalıştırma hatası: {e}")
            return {
                "success": False,
                "error": f"TR: Test çalıştırma hatası: {str(e)}"
            }
    
    def _calculate_aggregate_metrics(self, metrics_list: List[RAGMetrics]) -> Dict[str, Any]:
        """TR: Aggregate metrics hesapla"""
        if not metrics_list:
            return {}
        
        return {
            "precision": {
                "mean": statistics.mean([m.precision for m in metrics_list]),
                "median": statistics.median([m.precision for m in metrics_list]),
                "std": statistics.stdev([m.precision for m in metrics_list]) if len(metrics_list) > 1 else 0.0
            },
            "recall": {
                "mean": statistics.mean([m.recall for m in metrics_list]),
                "median": statistics.median([m.recall for m in metrics_list]),
                "std": statistics.stdev([m.recall for m in metrics_list]) if len(metrics_list) > 1 else 0.0
            },
            "f1_score": {
                "mean": statistics.mean([m.f1_score for m in metrics_list]),
                "median": statistics.median([m.f1_score for m in metrics_list]),
                "std": statistics.stdev([m.f1_score for m in metrics_list]) if len(metrics_list) > 1 else 0.0
            },
            "accuracy": {
                "mean": statistics.mean([m.accuracy for m in metrics_list]),
                "median": statistics.median([m.accuracy for m in metrics_list]),
                "std": statistics.stdev([m.accuracy for m in metrics_list]) if len(metrics_list) > 1 else 0.0
            },
            "response_time": {
                "mean": statistics.mean([m.response_time for m in metrics_list]),
                "median": statistics.median([m.response_time for m in metrics_list]),
                "std": statistics.stdev([m.response_time for m in metrics_list]) if len(metrics_list) > 1 else 0.0
            },
            "confidence_score": {
                "mean": statistics.mean([m.confidence_score for m in metrics_list]),
                "median": statistics.median([m.confidence_score for m in metrics_list]),
                "std": statistics.stdev([m.confidence_score for m in metrics_list]) if len(metrics_list) > 1 else 0.0
            }
        }
    
    def _analyze_by_difficulty(self, metrics_list: List[RAGMetrics]) -> Dict[str, Any]:
        """TR: Difficulty bazlı analiz"""
        difficulty_groups = {}
        
        for metrics in metrics_list:
            difficulty = metrics.query_complexity
            if difficulty not in difficulty_groups:
                difficulty_groups[difficulty] = []
            difficulty_groups[difficulty].append(metrics)
        
        analysis = {}
        for difficulty, group_metrics in difficulty_groups.items():
            analysis[difficulty] = {
                "count": len(group_metrics),
                "avg_precision": statistics.mean([m.precision for m in group_metrics]),
                "avg_recall": statistics.mean([m.recall for m in group_metrics]),
                "avg_f1_score": statistics.mean([m.f1_score for m in group_metrics]),
                "avg_accuracy": statistics.mean([m.accuracy for m in group_metrics]),
                "avg_response_time": statistics.mean([m.response_time for m in group_metrics])
            }
        
        return analysis
    
    def get_metrics_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """TR: Metrics geçmişini getir"""
        recent_metrics = self._metrics_history[-limit:] if self._metrics_history else []
        
        return [
            {
                "precision": m.precision,
                "recall": m.recall,
                "f1_score": m.f1_score,
                "accuracy": m.accuracy,
                "response_time": m.response_time,
                "confidence_score": m.confidence_score,
                "query_complexity": m.query_complexity,
                "timestamp": m.timestamp.isoformat()
            }
            for m in recent_metrics
        ]
    
    def get_test_scenarios(self) -> List[Dict[str, Any]]:
        """TR: Test senaryolarını getir"""
        return [
            {
                "id": s.id,
                "name": s.name,
                "query": s.query,
                "expected_documents": s.expected_documents,
                "expected_answer": s.expected_answer,
                "context": s.context,
                "difficulty": s.difficulty
            }
            for s in self._test_scenarios
        ]
