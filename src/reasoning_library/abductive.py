"""
Abductive Reasoning Module.

This module provides functions for abductive reasoning
(inference to the best explanation),
including hypothesis generation and evaluation from observations.
"""

import re
from typing import Any, Dict, List, Optional

from collections import defaultdict

from .core import ReasoningChain, curry, tool_spec
from .exceptions import ValidationError
from .validation import validate_string_list, validate_hypotheses_list
from .constants import (
    # Input validation limits
    MAX_OBSERVATION_LENGTH,
    MAX_CONTEXT_LENGTH,

    # Confidence calculation parameters
    BASE_CONFIDENCE_ABDUCTIVE,
    BASE_CONFIDENCE_TEMPLATE_HYPOTHESIS,

    # Simplicity and specificity factors
    SIMPLICITY_ASSUMPTION_PENALTY,
    SPECIFICITY_PREDICTIONS_MINIMUM,
    EVIDENCE_SUPPORT_MULTIPLIER,

    # Confidence boundaries
    CONFIDENCE_MIN,
    CONFIDENCE_MAX,

    # Evidence support thresholds
    EVIDENCE_SUPPORT_HIGH_THRESHOLD,
    EVIDENCE_SUPPORT_MODERATE_THRESHOLD,

    # Text processing limits
    KEYWORD_EXTRACTION_OBSERVATION_LIMIT,
    KEYWORD_EXTRACTION_CONTEXT_LIMIT,
    DOMAIN_DETECTION_LIMIT,
    KEYWORD_LENGTH_LIMIT,
    COMPONENT_LENGTH_LIMIT,
    ISSUE_LENGTH_LIMIT,
    HYPOTHESIS_TEXT_HARD_LIMIT,

    # Hypothesis generation parameters
    MAX_HYPOTHESES_DEFAULT,
    MAX_THEMES_RETURNED,
    THEME_FREQUENCY_THRESHOLD,
    MAX_TEMPLATE_KEYWORDS,

    # Input validation constants
    MIN_KEYWORD_LENGTH,
)


def _validate_and_sanitize_input_size(
    observations: List[str],
    context: Optional[str] = None,
    max_observation_length: int = MAX_OBSERVATION_LENGTH,
    max_context_length: int = MAX_CONTEXT_LENGTH
) -> tuple[List[str], Optional[str]]:
    """
    Validate and sanitize input sizes to prevent DoS attacks from large strings.

    This function applies size limits BEFORE any processing operations to prevent
    memory exhaustion and performance degradation from maliciously large inputs.

    Args:
        observations (List[str]): List of observations to validate and truncate
        context (Optional[str]): Additional context to validate and truncate
        max_observation_length (int): Maximum length for each observation
        max_context_length (int): Maximum length for context string

    Returns:
        tuple[List[str], Optional[str]]: Sanitized observations and context

    Security:
        - Prevents DoS attacks from extremely large strings
        - Applies limits early, before any string processing
        - Maintains backward compatibility with reasonable defaults
    """
    if not observations:
        return [], context

    # Validate and truncate each observation
    sanitized_observations = []
    for obs in observations:
        if not isinstance(obs, str):
            obs = str(obs)
        # Truncate if too long to prevent memory issues
        if len(obs) > max_observation_length:
            obs = obs[:max_observation_length].strip()
        sanitized_observations.append(obs)

    # Validate and truncate context
    if context is not None:
        if not isinstance(context, str):
            context = str(context)
        if len(context) > max_context_length:
            context = context[:max_context_length].strip()

    return sanitized_observations, context


def _validate_confidence_value(confidence: Any, hypothesis_index: Optional[int] = None) -> float:
    """
    Validate and normalize confidence value to prevent type coercion vulnerabilities.

    Args:
        confidence (Any): The confidence value to validate
        hypothesis_index (Optional[int]): Index of hypothesis for error messages

    Returns:
        float: Validated and normalized confidence value (0.0 - 1.0)

    Raises:
        TypeError: If confidence is not a numeric type
        ValueError: If confidence cannot be converted to a valid range
    """
    hypothesis_ref = f" (hypothesis #{hypothesis_index})" if hypothesis_index is not None else ""

    # Check type - must be numeric
    if not isinstance(confidence, (int, float)):
        raise ValidationError(
            f"Confidence value '{confidence}' must be numeric (int or float), got {type(confidence).__name__}{hypothesis_ref}"
        )

    # Check for NaN or infinity
    if isinstance(confidence, float):
        if confidence != confidence:  # NaN check
            raise ValidationError(f"Confidence cannot be NaN{hypothesis_ref}")
        if confidence in (float('inf'), float('-inf')):
            raise ValidationError(f"Confidence cannot be infinite{hypothesis_ref}")

    # Convert to float and clamp to valid range [0.0, 1.0]
    try:
        normalized_confidence = float(confidence)
        # Clamp to valid range
        normalized_confidence = max(CONFIDENCE_MIN, min(CONFIDENCE_MAX, normalized_confidence))
        return normalized_confidence
    except (ValueError, OverflowError) as e:
        raise ValidationError(f"Confidence value '{confidence}' is invalid{hypothesis_ref}: {e}")


def _calculate_hypothesis_confidence(
    hypothesis: Dict[str, Any],
    total_observations: int,
    explained_observations: int,
    assumption_count: int,
    base_confidence: float = BASE_CONFIDENCE_ABDUCTIVE,
) -> float:
    """
    Calculate confidence score for a hypothesis.

    Args:
        hypothesis (Dict): The hypothesis to evaluate
        total_observations (int): Total number of observations to explain
        explained_observations (int): Number of observations explained by this
            hypothesis
        assumption_count (int): Number of assumptions required
        base_confidence (float): Base confidence level

    Returns:
        float: Confidence score (0.0 - 1.0)
    """
    # Coverage factor: how many observations are explained
    coverage_factor = (
        explained_observations / total_observations
        if total_observations > 0 else CONFIDENCE_MIN
    )

    # Simplicity factor: prefer hypotheses with fewer assumptions (Occam's razor)
    simplicity_factor = 1.0 / (1.0 + SIMPLICITY_ASSUMPTION_PENALTY * assumption_count)

    # Specificity factor: more specific hypotheses get higher confidence
    specificity_factor = min(CONFIDENCE_MAX, len(hypothesis.get("testable_predictions", [])) / SPECIFICITY_PREDICTIONS_MINIMUM)

    # Calculate final confidence
    confidence = (
        base_confidence * coverage_factor * simplicity_factor * specificity_factor
    )

    return min(CONFIDENCE_MAX, max(CONFIDENCE_MIN, confidence))


def _extract_keywords(text: str) -> List[str]:
    """
    Extract relevant keywords from text for hypothesis generation.

    Args:
        text (str): Text to analyze

    Returns:
        List[str]: List of relevant keywords
    """
    # Simple keyword extraction - remove common words and extract meaningful terms
    common_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with',
        'to', 'for', 'o', 'as', 'by', 'that', 'this', 'it', 'from', 'are', 'be', 'was',
        'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'very', 'really'
    }

    # Convert to lowercase and extract words safely without ReDoS vulnerability
    # Fixed pattern prevents catastrophic backtracking by avoiding complex \b boundaries
    # This is a safer, non - backtracking alternative to r'\b\w+\b'
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())

    # Filter out common words and short words
    keywords = [word for word in words if word not in common_words and len(word) > MIN_KEYWORD_LENGTH]

    # Prioritize more meaningful keywords by removing less informative ones
    less_informative = {'about', 'like', 'just', 'then', 'than', 'some', 'more', 'most'}
    keywords = [word for word in keywords if word not in less_informative]

    # Return unique keywords while preserving some order (longer and earlier words first)
    unique_keywords = []
    seen = set()
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)

    # Sort by length (longer first) and position, to prioritize more meaningful terms
    unique_keywords.sort(key=lambda w: (-len(w), keywords.index(w)))

    return unique_keywords[:MAX_TEMPLATE_KEYWORDS]  # Limit to max keywords


def _extract_keywords_with_context(
    observations: List[str],
    context: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Extract meaningful phrases with context, not just individual words.

    Args:
        observations (List[str]): List of observations to analyze
        context (Optional[str]): Additional context information

    Returns:
        Dict[str, List[str]]: Dictionary with actions, components, and issues
    """
    # SECURITY: Apply input size validation BEFORE any processing to prevent DoS attacks
    observations, context = _validate_and_sanitize_input_size(
        observations, context,
        max_observation_length=KEYWORD_EXTRACTION_OBSERVATION_LIMIT,  # Smaller limit for keyword extraction
        max_context_length=KEYWORD_EXTRACTION_CONTEXT_LIMIT
    )

    # Combine all text with size limits already applied
    text = " ".join(observations).lower()
    if context:
        text += " " + context.lower()

    words = text.split()

    # Action detection with context
    actions = []
    for i, word in enumerate(words):
        if word in ["deploy", "deployment", "update", "restart", "change"]:
            # Look for modifiers like "recent" or "code"
            modifier = ""
            if i > 0 and words[i - 1] in ["recent", "code", "new"]:
                modifier = words[i - 1] + " "
            actions.append(f"{modifier}{word}")

    # Component detection
    components = []
    for word in words:
        if word in ["server", "database", "cache", "api", "network", "application"]:
            components.append(word)

    # Issue detection with context
    issues = []
    for i, word in enumerate(words):
        if word in ["cpu", "memory", "disk", "network"]:
            # Look for percentage or "at X%"
            if i + 1 < len(words) and "%" in words[i + 1]:
                issues.append(f"high {word.upper()} usage")
            elif i > 0 and words[i - 1] in ["high", "low"]:
                issues.append(f"{words[i - 1]} {word.upper()}")
            else:
                issues.append(f"high {word.upper()} usage")
        elif word in ["slow", "slowly"]:
            if i > 0 and words[i - 1] == "responding":
                issues.append("slow response times")
            else:
                issues.append("performance issues")
        elif word in ["error", "errors", "crash", "failure"]:
            issues.append(f"{word}s")

    return {
        "actions": actions if actions else ["recent change"],
        "components": components if components else ["system"],
        "issues": issues if issues else ["performance issue"],
    }


# Domain - specific templates for hypothesis generation
# Each domain contains:
# - keywords: List of keywords that trigger this domain
# - templates: List of template strings with {action}, {component},
#   and {issue} placeholders
DOMAIN_TEMPLATES = {
    "debugging": {
        "keywords": [
            "deploy", "code", "server", "database", "cpu", "memory", "slow", "error"
        ],
        "templates": [
            "{action} introduced {issue} in {component}",
            "{component} experiencing {issue} due to {action}",
            "Performance regression in {component} from {action} causing {issue}",
            "{action} causing {component} resource exhaustion due to {issue}",
        ]
    },
    "system": {
        "keywords": ["connection", "network", "timeout", "latency", "load"],
        "templates": [
            "Network or connection {issue} affecting {component}",
            "Load balancing problem causing {issue} in {component}",
            "{component} contention due to {action} causing {issue}"
        ]
    }
}


def _find_common_themes(observations: List[str]) -> List[str]:
    """
    Find common themes and patterns across observations.

    Args:
        observations (List[str]): List of observations

    Returns:
        List[str]: Common themes found
    """
    all_keywords = []
    for obs in observations:
        all_keywords.extend(_extract_keywords(obs))

    # Count keyword frequency
    keyword_freq = defaultdict(int)
    for keyword in all_keywords:
        keyword_freq[keyword] += 1

    # Return keywords that appear in multiple observations
    common_themes = [kw for kw, freq in keyword_freq.items() if freq >= THEME_FREQUENCY_THRESHOLD]

    # Sort by frequency
    common_themes.sort(key=lambda x: keyword_freq[x], reverse=True)

    return common_themes[:MAX_THEMES_RETURNED]  # Return top N themes


def _generate_single_cause_hypothesis(
    common_themes: List[str],
    observations_count: int
) -> Optional[Dict[str, Any]]:
    """
    Generate a single-cause hypothesis explaining all observations.

    Args:
        common_themes: List of common themes found in observations
        observations_count: Number of observations to explain

    Returns:
        Optional[Dict]: Single-cause hypothesis or None if no themes
    """
    if not common_themes:
        return None

    primary_theme = common_themes[0]
    single_cause = {
        "hypothesis": f"The observations are caused by {primary_theme}",
        "explains": list(range(observations_count)),
        "confidence": 0.0,  # Will be calculated
        "assumptions": [f"{primary_theme} is the primary cause"],
        "testable_predictions": [
            f"Removing {primary_theme} should stop the observations",
            f"Changing {primary_theme} should change the observations"
        ],
        "type": "single_cause",
        "theme": primary_theme
    }
    single_cause["confidence"] = _calculate_hypothesis_confidence(
        single_cause, observations_count, observations_count, 1
    )
    return single_cause


def _generate_multiple_causes_hypothesis(
    common_themes: List[str],
    observations_count: int
) -> Optional[Dict[str, Any]]:
    """
    Generate a multiple-causes hypothesis explaining all observations.

    Args:
        common_themes: List of common themes found in observations
        observations_count: Number of observations to explain

    Returns:
        Optional[Dict]: Multiple-causes hypothesis or None if insufficient themes
    """
    if len(common_themes) < 2:
        return None

    multiple_causes = {
        "hypothesis": (
            f"Multiple factors are contributing: {', '.join(common_themes[:3])}"
        ),
        "explains": list(range(observations_count)),
        "confidence": 0.0,  # Will be calculated
        "assumptions": [
            f"{theme} is a contributing factor" for theme in common_themes[:3]
        ],
        "testable_predictions": [
            "Addressing each factor should reduce corresponding observations",
            "Combined intervention should have greater effect than individual"
        ],
        "type": "multiple_causes",
        "themes": common_themes[:3]
    }
    multiple_causes["confidence"] = _calculate_hypothesis_confidence(
        multiple_causes, observations_count, observations_count, len(common_themes[:3])
    )
    return multiple_causes


def _generate_causal_chain_hypothesis(
    observations_count: int
) -> Optional[Dict[str, Any]]:
    """
    Generate a causal chain hypothesis explaining observations as a progression.

    Args:
        observations_count: Number of observations to explain

    Returns:
        Optional[Dict]: Causal chain hypothesis or None if insufficient observations
    """
    if observations_count < 2:
        return None

    causal_chain = {
        "hypothesis": "The observations represent a causal chain or progression",
        "explains": list(range(observations_count)),
        "confidence": 0.0,  # Will be calculated
        "assumptions": [
            "Observations occur in a temporal sequence",
            "Earlier observations influence later ones"
        ],
        "testable_predictions": [
            "Intervening early should prevent later observations",
            "Reversing the order should change outcomes"
        ],
        "type": "causal_chain"
    }
    causal_chain["confidence"] = _calculate_hypothesis_confidence(
        causal_chain, observations_count, observations_count, 2
    )
    return causal_chain


def _sanitize_template_input(text: str) -> str:
    """
    SECURE: Remove dangerous characters to prevent template injection attacks.

    This function sanitizes user input before using it in template.format() calls
    to prevent template injection vulnerabilities that could lead to code execution
    or information disclosure.

    Args:
        text: Input text to sanitize

    Returns:
        str: Sanitized text safe for template formatting

    Security:
        - Removes curly braces {} that could be used for template injection
        - Strips format string patterns like ${...}
        - Prevents code execution through malicious template strings
    """
    if not isinstance(text, str):
        return ""
    # Remove curly braces and format specifiers that could break templates
    sanitized = re.sub(r'[{}]', '', text)
    # Remove potential format string injection patterns
    sanitized = re.sub(r'\${[^}]*}', '', sanitized)  # ${...} patterns
    sanitized = re.sub(r'%[sd]', '', sanitized)      # %s, %d patterns
    return sanitized.strip()


def _generate_domain_template_hypotheses(
    observations: List[str],
    context: str,
    max_hypotheses: int,
    observations_count: int
) -> List[Dict[str, Any]]:
    """
    Generate domain-specific template hypotheses based on context.

    Args:
        observations: List of observations
        context: Context information for domain detection
        max_hypotheses: Maximum number of hypotheses to generate
        observations_count: Number of observations

    Returns:
        List[Dict]: Domain template hypotheses
    """
    # Determine domain based on keywords
    domain = None
    all_text = " ".join(observations) + " " + context.lower()
    # Additional safeguard: ensure all_text doesn't get too large even with validated inputs
    if len(all_text) > DOMAIN_DETECTION_LIMIT:  # 50KB limit for domain detection
        all_text = all_text[:DOMAIN_DETECTION_LIMIT]

    for domain_name, domain_info in DOMAIN_TEMPLATES.items():
        if any(keyword in all_text for keyword in domain_info["keywords"]):
            domain = domain_name
            break

    if not domain:
        return []

    keywords = _extract_keywords_with_context(observations, context)
    template_hyps = []

    for idx, template in enumerate(
        DOMAIN_TEMPLATES[domain]["templates"][:max_hypotheses]
    ):
        # Select best keywords for this template
        action = (
            keywords["actions"][0] if keywords["actions"] else "recent change"
        )
        component = (
            keywords["components"][
                min(idx, len(keywords["components"]) - 1)
            ] if keywords["components"] else "system"
        )
        issue = (
            keywords["issues"][
                min(idx, len(keywords["issues"]) - 1)
            ] if keywords["issues"] else "performance issue"
        )

        # SECURITY: Apply length limits IMMEDIATELY after keyword extraction
        action = action[:KEYWORD_LENGTH_LIMIT].strip()
        component = component[:COMPONENT_LENGTH_LIMIT].strip()
        issue = issue[:ISSUE_LENGTH_LIMIT].strip()

        # Validate inputs before template formatting
        if not isinstance(action, str) or len(action.strip()) == 0:
            action = "recent change"
        if not isinstance(component, str) or len(component.strip()) == 0:
            component = "system"
        if not isinstance(issue, str) or len(issue.strip()) == 0:
            issue = "performance issue"

        # Sanitize all template inputs to prevent injection
        safe_action = _sanitize_template_input(action)
        safe_component = _sanitize_template_input(component)
        safe_issue = _sanitize_template_input(issue)

        # Fill template with sanitized inputs (SECURE: no injection possible)
        hypothesis_text = template.format(
            action=safe_action,
            component=safe_component,
            issue=safe_issue
        )

        # Capitalize first letter
        hypothesis_text = hypothesis_text[0].upper() + hypothesis_text[1:]

        template_hyps.append({
            "hypothesis": hypothesis_text,
            "explains": list(range(observations_count)),
            "confidence": BASE_CONFIDENCE_TEMPLATE_HYPOTHESIS,
            "assumptions": ["Context '{context}' is relevant to the issue"],
            "testable_predictions": [
                f"Reverting the {action} should reduce or resolve the {issue}",
                f"Monitoring {component} metrics should show correlation with the issue"
            ],
            "type": "domain_template"
        })

    # Calculate confidence for template hypotheses
    for hyp in template_hyps:
        hyp["confidence"] = _calculate_hypothesis_confidence(
            hyp, observations_count, observations_count, 1
        )

    return template_hyps


def _generate_contextual_hypothesis(
    observations: List[str],
    context: str,
    observations_count: int
) -> Optional[Dict[str, Any]]:
    """
    Generate a contextual hypothesis when no domain matches.

    Args:
        observations: List of observations
        context: Context information
        observations_count: Number of observations

    Returns:
        Optional[Dict]: Contextual hypothesis or None
    """
    context_keywords = _extract_keywords(context)
    if not context_keywords:
        return None

    # SECURITY: Apply length limits to keywords to prevent DoS in contextual hypotheses
    safe_keywords = []
    for keyword in context_keywords[:MAX_TEMPLATE_KEYWORDS]:
        # Truncate each keyword to prevent long repetitive strings
        safe_keyword = keyword[:KEYWORD_LENGTH_LIMIT].strip()
        if safe_keyword:  # Only add non-empty keywords
            safe_keywords.append(safe_keyword)

    # Ensure we don't create overly long hypotheses
    if safe_keywords:
        # Create a more natural hypothesis that incorporates key context terms
        if len(safe_keywords) >= 2:
            main_keywords = safe_keywords[:2]  # Use the two most important keywords
            hypothesis_text = f"The observations may be related to {main_keywords[0]} and {main_keywords[1]} in this context"
        else:
            hypothesis_text = f"The observations may be related to {safe_keywords[0]} in this context"
    else:
        hypothesis_text = "The observations are related to the context"

    # Limit total hypothesis length
    if len(hypothesis_text) > HYPOTHESIS_TEXT_HARD_LIMIT:  # Hard limit for contextual hypotheses
        hypothesis_text = hypothesis_text[:HYPOTHESIS_TEXT_HARD_LIMIT].strip()

    context_hypothesis = {
        "hypothesis": hypothesis_text,
        "explains": list(range(observations_count)),
        "confidence": 0.0,  # Will be calculated
        "assumptions": [
            "Context is relevant to observations",
            f"{safe_keywords[0] if safe_keywords else 'context'} is a key factor"
        ],
        "testable_predictions": [
            "Changing the context should change the observations",
            "Similar contexts should produce similar observations"
        ],
        "type": "contextual",
        "context_keywords": safe_keywords
    }
    context_hypothesis["confidence"] = _calculate_hypothesis_confidence(
        context_hypothesis, observations_count, observations_count, 2
    )
    return context_hypothesis


def _generate_systemic_hypothesis(
    observations_count: int
) -> Dict[str, Any]:
    """
    Generate a systemic hypothesis about underlying system issues.

    Args:
        observations_count: Number of observations

    Returns:
        Dict: Systemic hypothesis
    """
    systemic = {
        "hypothesis": "The observations indicate a systemic issue affecting multiple components",
        "explains": list(range(observations_count)),
        "confidence": 0.0,  # Will be calculated
        "assumptions": [
            "Multiple observations share a common root cause",
            "System-wide factors are at play"
        ],
        "testable_predictions": [
            "Addressing the root cause should resolve all observations",
            "Similar issues may appear in other related areas"
        ],
        "type": "systemic"
    }
    systemic["confidence"] = _calculate_hypothesis_confidence(
        systemic, observations_count, observations_count, 2
    )
    return systemic


@tool_spec(
    mathematical_basis="Abductive reasoning - inference to the best explanation",
    confidence_factors=["coverage", "simplicity", "specificity"],
    confidence_formula="base * coverage_factor * simplicity_factor * specificity_factor"
)
@curry

def generate_hypotheses(
    observations: List[str],
    reasoning_chain: Optional[ReasoningChain],
    *,
    context: Optional[str] = None,
    max_hypotheses: int = MAX_HYPOTHESES_DEFAULT,
) -> List[Dict[str, Any]]:
    """
    Generate plausible explanatory hypotheses from observations
    using abductive reasoning.

    Args:
        observations (List[str]): List of observations to explain
        reasoning_chain (Optional[ReasoningChain]): An optional ReasoningChain
            to add steps to
        context (Optional[str]): Additional context for hypothesis generation
        max_hypotheses (int): Maximum number of hypotheses to generate

    Returns:
        List[Dict]: List of generated hypotheses with confidence scores and metadata
    """
    # Validate complex parameter types
    try:
        validated_observations = validate_string_list(
            observations, "observations", allow_empty=False, max_length=100
        )
    except ValidationError as e:
        if reasoning_chain:
            reasoning_chain.add_step(
                stage="Abductive Reasoning: Hypothesis Generation",
                description=f"Input validation failed: {str(e)}",
                result=[],
                confidence=0.0
            )
        raise

    # SECURITY: Apply input size validation BEFORE any processing to prevent DoS attacks
    observations, context = _validate_and_sanitize_input_size(validated_observations, context)

    if not observations:
        if reasoning_chain:
            reasoning_chain.add_step(
                stage="Abductive Reasoning: Hypothesis Generation",
                description="No observations provided for hypothesis generation",
                result=[],
                confidence=0.0
            )
        return []

    stage = "Abductive Reasoning: Hypothesis Generation"
    description = f"Generating hypotheses to explain {len(observations)} observations"

    # Find common themes in observations
    common_themes = _find_common_themes(observations)
    observations_count = len(observations)

    # Generate different types of hypotheses
    hypotheses = []

    # 1. Single-cause hypothesis
    single_cause = _generate_single_cause_hypothesis(common_themes, observations_count)
    if single_cause:
        hypotheses.append(single_cause)

    # 2. Multiple-causes hypothesis
    multiple_causes = _generate_multiple_causes_hypothesis(common_themes, observations_count)
    if multiple_causes:
        hypotheses.append(multiple_causes)

    # 3. Causal chain hypothesis
    causal_chain = _generate_causal_chain_hypothesis(observations_count)
    if causal_chain:
        hypotheses.append(causal_chain)

    # 4. Domain-specific template hypotheses
    if context:
        template_hyps = _generate_domain_template_hypotheses(
            observations, context, max_hypotheses, observations_count
        )
        hypotheses.extend(template_hyps)

        # 5. Contextual hypothesis (fallback if no domain matches)
        if not template_hyps:
            context_hyp = _generate_contextual_hypothesis(observations, context, observations_count)
            if context_hyp:
                hypotheses.append(context_hyp)

    # 6. Systemic hypothesis
    systemic = _generate_systemic_hypothesis(observations_count)
    hypotheses.append(systemic)

    # Sort hypotheses by confidence and limit to max_hypotheses
    hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
    hypotheses = hypotheses[:max_hypotheses]

    if reasoning_chain:
        reasoning_chain.add_step(
            stage=stage,
            description=description,
            result=hypotheses,
            confidence=max([h["confidence"] for h in hypotheses]) if hypotheses else 0.0,
            evidence=f"Generated {len(hypotheses)} hypotheses from {len(observations)} observations",
            assumptions=[
                "Observations are accurate and relevant",
                "Generated hypotheses are plausible"
            ]
        )

    return hypotheses


@tool_spec(
    mathematical_basis="Abductive reasoning - inference to the best explanation",
    confidence_factors=["coverage", "simplicity", "specificity"],
    confidence_formula="base * coverage_factor * simplicity_factor * specificity_factor"
)
@curry

def rank_hypotheses(
    hypotheses: List[Dict[str, Any]],
    new_evidence: List[str],
    reasoning_chain: Optional[ReasoningChain],
) -> List[Dict[str, Any]]:
    """
    Rank and update hypotheses based on new evidence.

    This function validates confidence values to prevent type coercion vulnerabilities.
    Each hypothesis must have a numeric confidence value (int or float) between 0.0 and 1.0.
    Invalid confidence types will raise TypeError, while out-of-range values are
    automatically clamped to the valid range [0.0, 1.0].

    Args:
        hypotheses (List[Dict]): List of existing hypotheses. Each hypothesis should
            be a dictionary with at least:
            - "hypothesis" (str): The hypothesis text
            - "confidence" (int|float): Numeric confidence value (0.0-1.0)
        new_evidence (List[str]): New evidence to consider
        reasoning_chain (Optional[ReasoningChain]): An optional ReasoningChain
            to add steps to

    Returns:
        List[Dict]: Updated hypotheses with adjusted confidence scores (0.0-1.0)

    Raises:
        TypeError: If any hypothesis confidence is not numeric (int or float)
        ValueError: If any hypothesis confidence is NaN or infinite

    Examples:
        >>> hypotheses = [
        ...     {"hypothesis": "Server overload", "confidence": 0.7},
        ...     {"hypothesis": "Network issue", "confidence": 0.3}
        ... ]
        >>> evidence = ["High CPU usage", "Slow response times"]
        >>> result = rank_hypotheses(hypotheses, evidence, None)
        >>> len(result)
        2
        >>> all(0.0 <= h["confidence"] <= 1.0 for h in result)
        True
    """
    # Validate complex parameter types
    try:
        validated_hypotheses = validate_hypotheses_list(
            hypotheses, "hypotheses", max_hypotheses=50
        )
        validated_evidence = validate_string_list(
            new_evidence, "new_evidence", allow_empty=True, max_length=50
        )
    except ValidationError as e:
        if reasoning_chain:
            reasoning_chain.add_step(
                stage="Abductive Reasoning: Hypothesis Ranking",
                description=f"Input validation failed: {str(e)}",
                result=[],
                confidence=0.0
            )
        raise

    if not validated_hypotheses:
        if reasoning_chain:
            reasoning_chain.add_step(
                stage="Abductive Reasoning: Hypothesis Ranking",
                description="No hypotheses provided for ranking",
                result=[],
                confidence = 0.0
            )
        return []

    stage = "Abductive Reasoning: Hypothesis Ranking"
    description = f"Updating {len(validated_hypotheses)} hypotheses based on {len(validated_evidence)} pieces of new evidence"

    updated_hypotheses = []

    for index, hypothesis in enumerate(validated_hypotheses):
        # Create a copy to avoid modifying original
        updated_hypothesis = hypothesis.copy()

        # Validate confidence value to prevent type coercion vulnerabilities
        validated_confidence = _validate_confidence_value(hypothesis.get("confidence"), index)

        # Calculate evidence support score
        evidence_support = 0.0
        total_evidence_score = 0.0

        for evidence in validated_evidence:
            # Simple evidence matching based on keyword overlap
            evidence_keywords = set(_extract_keywords(evidence))
            hypothesis_keywords = set(_extract_keywords(hypothesis["hypothesis"]))

            # Calculate overlap
            overlap = len(evidence_keywords & hypothesis_keywords)
            total = len(evidence_keywords | hypothesis_keywords)

            if total > 0:
                similarity = overlap / total
                evidence_support += similarity
                total_evidence_score += 1.0

        # Average evidence support
        avg_evidence_support = evidence_support / total_evidence_score if total_evidence_score > 0 else 0.0

        # Update confidence based on evidence (now using validated confidence)
        confidence_multiplier = 1.0 + (EVIDENCE_SUPPORT_MULTIPLIER * avg_evidence_support)
        updated_hypothesis["confidence"] = min(CONFIDENCE_MAX, validated_confidence * confidence_multiplier)

        # Add evidence to hypothesis
        if "supporting_evidence" not in updated_hypothesis:
            updated_hypothesis["supporting_evidence"] = []
        updated_hypothesis["supporting_evidence"].extend(new_evidence)

        # Update hypothesis description if strong evidence
        if avg_evidence_support > EVIDENCE_SUPPORT_HIGH_THRESHOLD:
            updated_hypothesis["hypothesis"] += " (strongly supported by new evidence)"
        elif avg_evidence_support > EVIDENCE_SUPPORT_MODERATE_THRESHOLD:
            updated_hypothesis["hypothesis"] += " (supported by new evidence)"

        updated_hypotheses.append(updated_hypothesis)

    # Re - sort by updated confidence
    updated_hypotheses.sort(key=lambda x: x["confidence"], reverse=True)

    if reasoning_chain:
        reasoning_chain.add_step(
            stage = stage,
            description = description,
            result = updated_hypotheses,
            confidence = max([h["confidence"] for h in updated_hypotheses]) if updated_hypotheses else 0.0,
            evidence = f"Hypotheses re - ranked based on {len(new_evidence)} pieces of new evidence",
            assumptions=[
                "New evidence is accurate and relevant",
                "Evidence evaluation is objective"
            ]
        )

    return updated_hypotheses


@tool_spec(
    mathematical_basis="Abductive reasoning - inference to the best explanation",
    confidence_factors=["coverage", "simplicity", "specificity"],
    confidence_formula="base * coverage_factor * simplicity_factor * specificity_factor"
)
@curry

def evaluate_best_explanation(
    hypotheses: List[Dict[str, Any]],
    reasoning_chain: Optional[ReasoningChain],
) -> Optional[Dict[str, Any]]:
    """
    Select the best explanation from a set of hypotheses.

    Args:
        hypotheses (List[Dict]): List of hypotheses to evaluate
        reasoning_chain (Optional[ReasoningChain]): An optional ReasoningChain
            to add steps to

    Returns:
        Optional[Dict]: The best explanation or None if no hypotheses provided
    """
    # Validate complex parameter types
    try:
        validated_hypotheses = validate_hypotheses_list(
            hypotheses, "hypotheses", max_hypotheses=50
        )
    except ValidationError as e:
        if reasoning_chain:
            reasoning_chain.add_step(
                stage="Abductive Reasoning: Best Explanation Selection",
                description=f"Input validation failed: {str(e)}",
                result=None,
                confidence=0.0
            )
        raise

    if not validated_hypotheses:
        if reasoning_chain:
            reasoning_chain.add_step(
                stage="Abductive Reasoning: Best Explanation Selection",
                description="No hypotheses provided for evaluation",
                result = None,
                confidence = 0.0
            )
        return None

    stage = "Abductive Reasoning: Best Explanation Selection"
    description = f"Evaluating {len(validated_hypotheses)} hypotheses to select best explanation"

    # Select the hypothesis with highest confidence
    best_hypothesis = max(validated_hypotheses, key=lambda x: x["confidence"])

    # Add evaluation metadata
    best_hypothesis["evaluation"] = {
        "total_hypotheses": len(validated_hypotheses),
        "rank": 1,
        "selected_as_best": True,
        "selection_reason": f"Highest confidence score ({best_hypothesis['confidence']:.3f})"
    }

    if reasoning_chain:
        reasoning_chain.add_step(
            stage = stage,
            description = description,
            result = best_hypothesis,
            confidence = best_hypothesis["confidence"],
            evidence = f"Selected from {len(hypotheses)} hypotheses based on confidence score",
            assumptions=[
                "Higher confidence indicates better explanation",
                "All relevant hypotheses were considered"
            ]
        )

    return best_hypothesis
