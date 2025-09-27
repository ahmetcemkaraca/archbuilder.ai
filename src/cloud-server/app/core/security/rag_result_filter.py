"""
RAG Result Filter for ArchBuilder.AI
RAG result filters - P44-T2
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog
from datetime import datetime, timedelta

logger = structlog.get_logger(__name__)


class FilterType(Enum):
    """Types of RAG result filters"""

    CONTENT_SAFETY = "content_safety"
    ACCURACY_VALIDATION = "accuracy_validation"
    RELEVANCE_CHECK = "relevance_check"
    BIAS_DETECTION = "bias_detection"
    HALLUCINATION_PREVENTION = "hallucination_prevention"
    SOURCE_VERIFICATION = "source_verification"


class RiskLevel(Enum):
    """Risk levels for filtered content"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FilterResult:
    """Result of content filtering"""

    passed: bool
    filter_type: FilterType
    confidence: float
    risk_level: RiskLevel
    issues: List[str]
    recommendations: List[str]
    filtered_content: Optional[str] = None


@dataclass
class RAGResult:
    """RAG result data structure"""

    content: str
    sources: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime


class ContentSafetyFilter:
    """Filters content for safety and appropriateness"""

    def __init__(self):
        self.harmful_patterns = [
            # Violence and harm
            r'\b(kill|murder|assassinate|destroy|harm|hurt|violence|violent)\b',
            r'\b(weapon|gun|knife|bomb|explosive|poison)\b',
            r'\b(death|die|dying|suicide|self-harm)\b',
            # Hate speech and discrimination
            r'\b(hate|racist|sexist|homophobic|discriminatory)\b',
            r'\b(superior|inferior|master|slave)\b',
            r'\b(genocide|ethnic cleansing|holocaust)\b',
            # Illegal activities
            r'\b(illegal|unlawful|criminal|fraud|scam|theft|robbery)\b',
            r'\b(drug|narcotic|addiction|overdose)\b',
            r'\b(terrorism|terrorist|extremist)\b',
            # Inappropriate content
            r'\b(sexual|pornographic|explicit|adult)\b',
            r'\b(harassment|stalking|abuse|molestation)\b',
            # Dangerous instructions
            r'\b(how to (kill|murder|harm|hurt|poison))\b',
            r'\b(make (bomb|explosive|weapon|poison))\b',
            r'\b(instructions for (violence|harm|illegal))\b',
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.harmful_patterns
        ]

    def filter(self, content: str) -> FilterResult:
        """Filter content for safety"""
        issues = []
        risk_level = RiskLevel.LOW
        confidence = 1.0

        # Check for harmful patterns
        for pattern in self.compiled_patterns:
            matches = pattern.findall(content)
            if matches:
                issues.append(f"Detected harmful content: {matches}")
                confidence -= 0.2
                risk_level = RiskLevel.HIGH

        # Check content length and complexity
        if len(content) > 10000:  # Very long content
            issues.append("Content is unusually long")
            confidence -= 0.1

        # Check for repeated patterns (potential spam)
        words = content.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        repeated_words = [word for word, count in word_counts.items() if count > 10]
        if repeated_words:
            issues.append(f"Excessive repetition detected: {repeated_words}")
            confidence -= 0.3
            risk_level = RiskLevel.MEDIUM

        # Determine if content passed
        passed = len(issues) == 0 and confidence > 0.5

        recommendations = []
        if not passed:
            recommendations.append("Content contains potentially harmful material")
            recommendations.append("Review content for safety before use")

        return FilterResult(
            passed=passed,
            filter_type=FilterType.CONTENT_SAFETY,
            confidence=confidence,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
        )


class AccuracyValidationFilter:
    """Validates accuracy of RAG results"""

    def __init__(self):
        self.accuracy_indicators = [
            # Confidence indicators
            r'\b(confident|certain|definitely|absolutely|100%)\b',
            r'\b(guaranteed|assured|confirmed|verified)\b',
            # Uncertainty indicators
            r'\b(might|maybe|possibly|perhaps|likely|probably)\b',
            r'\b(uncertain|unclear|unknown|unverified)\b',
            r'\b(according to|based on|sources suggest)\b',
            # Factual claims
            r'\b(studies show|research indicates|data proves)\b',
            r'\b(statistics|percentages|numbers|figures)\b',
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.accuracy_indicators
        ]

    def filter(self, content: str, sources: List[Dict[str, Any]]) -> FilterResult:
        """Validate accuracy of content"""
        issues = []
        confidence = 1.0
        risk_level = RiskLevel.LOW

        # Check for unsupported claims
        unsupported_claims = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(content)
            for match in matches:
                if 'confident' in match.lower() or 'certain' in match.lower():
                    # High confidence claims need strong sources
                    if not self._has_strong_sources(sources):
                        unsupported_claims.append(match)
                        confidence -= 0.3
                        risk_level = RiskLevel.MEDIUM

        if unsupported_claims:
            issues.append(f"Unsupported high-confidence claims: {unsupported_claims}")

        # Check source quality
        source_issues = self._validate_sources(sources)
        if source_issues:
            issues.extend(source_issues)
            confidence -= 0.2
            risk_level = RiskLevel.MEDIUM

        # Check for contradictory information
        contradictions = self._detect_contradictions(content)
        if contradictions:
            issues.append(f"Contradictory information detected: {contradictions}")
            confidence -= 0.4
            risk_level = RiskLevel.HIGH

        passed = len(issues) == 0 and confidence > 0.6

        recommendations = []
        if not passed:
            recommendations.append("Verify claims with reliable sources")
            recommendations.append("Reduce confidence level for uncertain information")

        return FilterResult(
            passed=passed,
            filter_type=FilterType.ACCURACY_VALIDATION,
            confidence=confidence,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
        )

    def _has_strong_sources(self, sources: List[Dict[str, Any]]) -> bool:
        """Check if content has strong, reliable sources"""
        if not sources:
            return False

        strong_source_indicators = [
            'peer-reviewed',
            'academic',
            'scholarly',
            'research',
            'official',
            'government',
            'institutional',
        ]

        for source in sources:
            source_text = str(source).lower()
            if any(indicator in source_text for indicator in strong_source_indicators):
                return True

        return False

    def _validate_sources(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Validate source quality"""
        issues = []

        if not sources:
            issues.append("No sources provided")
            return issues

        for i, source in enumerate(sources):
            if not isinstance(source, dict):
                issues.append(f"Source {i} is not properly formatted")
                continue

            # Check for required fields
            required_fields = ['title', 'url', 'author', 'date']
            missing_fields = [field for field in required_fields if field not in source]
            if missing_fields:
                issues.append(f"Source {i} missing fields: {missing_fields}")

        return issues

    def _detect_contradictions(self, content: str) -> List[str]:
        """Detect contradictory statements"""
        contradictions = []

        # Simple contradiction patterns
        contradiction_pairs = [
            (r'\b(always|never|all|none)\b', r'\b(sometimes|often|some|many)\b'),
            (r'\b(increase|rise|grow)\b', r'\b(decrease|fall|decline)\b'),
            (
                r'\b(proven|confirmed|verified)\b',
                r'\b(unproven|unconfirmed|disputed)\b',
            ),
        ]

        for positive, negative in contradiction_pairs:
            if re.search(positive, content, re.IGNORECASE) and re.search(
                negative, content, re.IGNORECASE
            ):
                contradictions.append(f"Contradiction: {positive} vs {negative}")

        return contradictions


class BiasDetectionFilter:
    """Detects bias in RAG results"""

    def __init__(self):
        self.bias_indicators = [
            # Gender bias
            r'\b(he should|she should|men are|women are)\b',
            r'\b(typical (man|woman|male|female))\b',
            # Racial bias
            r'\b(race|ethnicity|skin color|nationality)\b',
            r'\b(stereotypical|typical (black|white|asian|hispanic))\b',
            # Age bias
            r'\b(too old|too young|elderly|youth)\b',
            r'\b(age-appropriate|age-inappropriate)\b',
            # Socioeconomic bias
            r'\b(poor|rich|wealthy|poverty|affluent)\b',
            r'\b(educated|uneducated|intelligent|stupid)\b',
            # Political bias
            r'\b(liberal|conservative|left|right|political)\b',
            r'\b(government|politics|policy|political)\b',
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.bias_indicators
        ]

    def filter(self, content: str) -> FilterResult:
        """Detect bias in content"""
        issues = []
        confidence = 1.0
        risk_level = RiskLevel.LOW

        # Check for bias indicators
        bias_matches = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(content)
            if matches:
                bias_matches.extend(matches)
                confidence -= 0.1
                risk_level = RiskLevel.MEDIUM

        if bias_matches:
            issues.append(f"Potential bias detected: {bias_matches}")

        # Check for balanced representation
        balance_issues = self._check_balance(content)
        if balance_issues:
            issues.extend(balance_issues)
            confidence -= 0.2
            risk_level = RiskLevel.MEDIUM

        passed = len(issues) == 0 and confidence > 0.7

        recommendations = []
        if not passed:
            recommendations.append("Review content for potential bias")
            recommendations.append("Ensure balanced representation")

        return FilterResult(
            passed=passed,
            filter_type=FilterType.BIAS_DETECTION,
            confidence=confidence,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
        )

    def _check_balance(self, content: str) -> List[str]:
        """Check for balanced representation"""
        issues = []

        # Check gender balance
        male_pronouns = len(
            re.findall(r'\b(he|him|his|himself)\b', content, re.IGNORECASE)
        )
        female_pronouns = len(
            re.findall(r'\b(she|her|hers|herself)\b', content, re.IGNORECASE)
        )

        if male_pronouns > 0 and female_pronouns == 0:
            issues.append("Content heavily favors male pronouns")
        elif female_pronouns > 0 and male_pronouns == 0:
            issues.append("Content heavily favors female pronouns")

        return issues


class HallucinationPreventionFilter:
    """Prevents AI hallucinations in RAG results"""

    def __init__(self):
        self.hallucination_indicators = [
            # Overly specific claims
            r'\b(exactly|precisely|specifically)\s+\d+\b',
            r'\b(studies show|research proves|data confirms)\b',
            # Made-up statistics
            r'\b\d+%\s+(of|in|for|with)\b',
            r'\b(according to|based on)\s+(studies|research|data)\b',
            # Unverifiable claims
            r'\b(experts say|scientists agree|studies confirm)\b',
            r'\b(widely known|commonly accepted|universally recognized)\b',
        ]

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.hallucination_indicators
        ]

    def filter(self, content: str, sources: List[Dict[str, Any]]) -> FilterResult:
        """Prevent hallucinations in content"""
        issues = []
        confidence = 1.0
        risk_level = RiskLevel.LOW

        # Check for hallucination indicators
        hallucination_matches = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(content)
            if matches:
                hallucination_matches.extend(matches)
                confidence -= 0.2
                risk_level = RiskLevel.MEDIUM

        if hallucination_matches:
            issues.append(
                f"Potential hallucination indicators: {hallucination_matches}"
            )

        # Check for unsupported specific claims
        specific_claims = self._find_specific_claims(content)
        if specific_claims and not self._verify_claims_with_sources(
            specific_claims, sources
        ):
            issues.append("Unsupported specific claims detected")
            confidence -= 0.3
            risk_level = RiskLevel.HIGH

        # Check for made-up statistics
        statistics = self._extract_statistics(content)
        if statistics and not self._verify_statistics(statistics, sources):
            issues.append("Unverified statistics detected")
            confidence -= 0.4
            risk_level = RiskLevel.HIGH

        passed = len(issues) == 0 and confidence > 0.6

        recommendations = []
        if not passed:
            recommendations.append("Verify all specific claims with sources")
            recommendations.append("Remove or qualify unverified statistics")

        return FilterResult(
            passed=passed,
            filter_type=FilterType.HALLUCINATION_PREVENTION,
            confidence=confidence,
            risk_level=risk_level,
            issues=issues,
            recommendations=recommendations,
        )

    def _find_specific_claims(self, content: str) -> List[str]:
        """Find specific claims that need verification"""
        specific_patterns = [
            r'\b\d+\s+(percent|%)\s+(of|in|for)\b',
            r'\b(studies show|research indicates|data reveals)\b',
            r'\b(according to|based on)\s+(studies|research|data)\b',
        ]

        claims = []
        for pattern in specific_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            claims.extend(matches)

        return claims

    def _verify_claims_with_sources(
        self, claims: List[str], sources: List[Dict[str, Any]]
    ) -> bool:
        """Verify claims against sources"""
        if not sources:
            return False

        # Simple verification - check if sources contain relevant information
        source_text = ' '.join(str(source) for source in sources).lower()

        for claim in claims:
            claim_words = claim.lower().split()
            if not any(word in source_text for word in claim_words if len(word) > 3):
                return False

        return True

    def _extract_statistics(self, content: str) -> List[str]:
        """Extract statistics from content"""
        stat_patterns = [
            r'\b\d+%\b',
            r'\b\d+\s+(percent|percentage)\b',
            r'\b\d+\s+(of|in|for)\s+\d+\b',
        ]

        statistics = []
        for pattern in stat_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            statistics.extend(matches)

        return statistics

    def _verify_statistics(
        self, statistics: List[str], sources: List[Dict[str, Any]]
    ) -> bool:
        """Verify statistics against sources"""
        if not sources:
            return False

        source_text = ' '.join(str(source) for source in sources)

        for stat in statistics:
            if stat not in source_text:
                return False

        return True


class RAGResultFilter:
    """Main RAG result filter orchestrator"""

    def __init__(self):
        self.content_safety_filter = ContentSafetyFilter()
        self.accuracy_filter = AccuracyValidationFilter()
        self.bias_filter = BiasDetectionFilter()
        self.hallucination_filter = HallucinationPreventionFilter()

    async def filter_rag_result(self, rag_result: RAGResult) -> Dict[str, Any]:
        """Filter a RAG result through all filters"""
        logger.info("Filtering RAG result", content_length=len(rag_result.content))

        filter_results = []

        # Apply content safety filter
        safety_result = self.content_safety_filter.filter(rag_result.content)
        filter_results.append(safety_result)

        # Apply accuracy validation filter
        accuracy_result = self.accuracy_filter.filter(
            rag_result.content, rag_result.sources
        )
        filter_results.append(accuracy_result)

        # Apply bias detection filter
        bias_result = self.bias_filter.filter(rag_result.content)
        filter_results.append(bias_result)

        # Apply hallucination prevention filter
        hallucination_result = self.hallucination_filter.filter(
            rag_result.content, rag_result.sources
        )
        filter_results.append(hallucination_result)

        # Determine overall result
        overall_passed = all(result.passed for result in filter_results)
        overall_confidence = sum(result.confidence for result in filter_results) / len(
            filter_results
        )

        # Determine overall risk level
        risk_levels = [result.risk_level for result in filter_results]
        if RiskLevel.CRITICAL in risk_levels:
            overall_risk = RiskLevel.CRITICAL
        elif RiskLevel.HIGH in risk_levels:
            overall_risk = RiskLevel.HIGH
        elif RiskLevel.MEDIUM in risk_levels:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW

        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []

        for result in filter_results:
            all_issues.extend(result.issues)
            all_recommendations.extend(result.recommendations)

        # Create filtered content if needed
        filtered_content = None
        if not overall_passed:
            filtered_content = self._create_filtered_content(
                rag_result.content, filter_results
            )

        return {
            'passed': overall_passed,
            'confidence': overall_confidence,
            'risk_level': overall_risk.value,
            'filter_results': [
                {
                    'filter_type': result.filter_type.value,
                    'passed': result.passed,
                    'confidence': result.confidence,
                    'risk_level': result.risk_level.value,
                    'issues': result.issues,
                    'recommendations': result.recommendations,
                }
                for result in filter_results
            ],
            'issues': all_issues,
            'recommendations': all_recommendations,
            'filtered_content': filtered_content,
        }

    def _create_filtered_content(
        self, original_content: str, filter_results: List[FilterResult]
    ) -> str:
        """Create filtered version of content"""
        # For now, return original content with warnings
        # In a real implementation, this would remove or modify problematic sections
        warnings = []
        for result in filter_results:
            if not result.passed:
                warnings.append(
                    f"[{result.filter_type.value.upper()}] {', '.join(result.issues)}"
                )

        if warnings:
            return (
                f"[FILTERED CONTENT - {len(warnings)} issues detected]\n\n"
                + original_content
            )
        else:
            return original_content


# Global filter instance
_rag_filter = RAGResultFilter()


async def filter_rag_result(rag_result: RAGResult) -> Dict[str, Any]:
    """Filter a RAG result"""
    return await _rag_filter.filter_rag_result(rag_result)
