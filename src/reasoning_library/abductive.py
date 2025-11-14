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
from .sanitization import (
    sanitize_for_concatenation,
    _sanitize_input_for_concatenation,
    _sanitize_template_input
)

# Pre-compile regex patterns for ReDoS protection and performance
# HIGH-001 SECURITY FIX: Simple pattern prevents catastrophic backtracking
KEYWORD_EXTRACTION_PATTERN = re.compile(r'[a-zA-Z0-9]{1,50}')
# Simple character class with explicit length limits prevents ReDoS attacks
# Bounds checking (1,50) prevents excessive backtracking on malformed input

# Thread-safe shared constants for keyword extraction
# These are immutable sets that can be safely shared across threads
COMMON_WORDS = frozenset({
    'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with',
    'to', 'for', 'o', 'as', 'by', 'that', 'this', 'it', 'from', 'are', 'be', 'was',
    'were', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'very', 'really'
})

LESS_INFORMATIVE_WORDS = frozenset({
    'about', 'like', 'just', 'then', 'than', 'some', 'more', 'most'
})

# Thread safety note: These constants are immutable frozensets that are safe
# for concurrent access across multiple threads without locking mechanisms.

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

    sanitized_observations = []
    for obs in observations:
        if not isinstance(obs, str):
            obs = str(obs)
        # Truncate if too long to prevent memory issues
        if len(obs) > max_observation_length:
            obs = obs[:max_observation_length].strip()
        sanitized_observations.append(obs)

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

    if not isinstance(confidence, (int, float)):
        raise ValidationError(
            f"Confidence value '{confidence}' must be numeric (int or float), got {type(confidence).__name__}{hypothesis_ref}"
        )

    if isinstance(confidence, float):
        if confidence != confidence:  # NaN check
            raise ValidationError(f"Confidence cannot be NaN{hypothesis_ref}")
        if confidence in (float('inf'), float('-inf')):
            raise ValidationError(f"Confidence cannot be infinite{hypothesis_ref}")

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
    coverage_factor = (
        explained_observations / total_observations
        if total_observations > 0 else CONFIDENCE_MIN
    )

    simplicity_factor = 1.0 / (1.0 + SIMPLICITY_ASSUMPTION_PENALTY * assumption_count)

    specificity_factor = min(CONFIDENCE_MAX, len(hypothesis.get("testable_predictions", [])) / SPECIFICITY_PREDICTIONS_MINIMUM)

    confidence = (
        base_confidence * coverage_factor * simplicity_factor * specificity_factor
    )

    return min(CONFIDENCE_MAX, max(CONFIDENCE_MIN, confidence))


def _extract_keywords(text: str) -> List[str]:
    """
    Extract relevant keywords from text for hypothesis generation with ReDoS protection.

    Args:
        text (str): Text to analyze

    Returns:
        List[str]: List of relevant keywords

    Security:
        - Uses atomic groups to prevent catastrophic backtracking
        - Limits input length to prevent DoS attacks
        - Pre-compiled regex patterns for performance
        - Strict keyword extraction limits

    Raises:
        ValidationError: If text is None
    """
    # SECURITY: Input validation to prevent None crashes
    if text is None:
        raise ValidationError("text cannot be None for keyword extraction")

    if not isinstance(text, str):
        raise ValidationError(f"text must be a string, got {type(text).__name__}")

    # Strict input length limit to prevent DoS
    if len(text) > 5000:  # Conservative limit
        text = text[:5000]  # Truncate to safe length

    # THREAD SAFETY: Use immutable frozensets that are safe for concurrent access
    # This eliminates the overhead of creating sets on every function call

    # HIGH-001 SECURITY FIX: Use pre-compiled pattern with length limits to prevent ReDoS
    # Pattern [a-zA-Z0-9]{1,50} prevents backtracking and limits word length to 50 chars
    words = KEYWORD_EXTRACTION_PATTERN.findall(text.lower())

    # Use thread-safe shared constants for filtering
    keywords = [word for word in words if word not in COMMON_WORDS and len(word) > MIN_KEYWORD_LENGTH]
    keywords = [word for word in keywords if word not in LESS_INFORMATIVE_WORDS]

    unique_keywords = []
    seen = set()
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)

    unique_keywords.sort(key=lambda w: (-len(w), keywords.index(w)))

    # SECURITY: Additional safety limit to prevent DoS through keyword explosion
    # This provides defense-in-depth beyond MAX_TEMPLATE_KEYWORDS
    safe_limit = min(MAX_TEMPLATE_KEYWORDS, 50)  # Conservative upper bound
    return unique_keywords[:safe_limit]


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


def _sanitize_input_for_concatenation(text: str) -> str:
    """
    DEPRECATED: Use sanitize_for_concatenation() from .sanitization instead.

    This function is maintained for backward compatibility only.
    New code should use sanitize_for_concatenation() directly.

    Args:
        text: Input text to sanitize

    Returns:
        str: Sanitized text safe for string concatenation
    """
    return sanitize_for_concatenation(text, max_length=50)


def _sanitize_template_input(text: str) -> str:
    """
    DEPRECATED: Use _sanitize_input_for_concatenation() instead.

    This function is kept for backward compatibility but should not be used.
    Template formatting has been completely removed due to security vulnerabilities.
    """
    return _sanitize_input_for_concatenation(text)


def _safe_hypothesis_template(action: str, component: str, issue: str, template_pattern: str) -> str:
    """
    CRITICAL SECURITY: Safe hypothesis generation without template injection vulnerability.

    SECURE IMPLEMENTATION: Uses context-aware tokenization that eliminates cross-contamination
    while preserving the original template functionality.

    Args:
        action: Sanitized action description
        component: Sanitized component name
        issue: Sanitized issue description
        template_pattern: Template pattern with {action}, {component}, {issue} placeholders

    Returns:
        str: Safe hypothesis text with no template injection vulnerability

    Security Features:
        - CONTEXT-AWARE PARSING: Only processes template placeholders, not user input
        - NO CROSS-CONTAMINATION: User inputs with placeholder patterns treated as literal text
        - SECURE TOKENIZATION: Distinguishes template syntax from literal text
        - DEFENSE IN DEPTH: Multiple layers of input validation and sanitization
        - BACKWARD COMPATIBLE: Preserves original template behavior for legitimate use
    """
    # SECURITY: Validate all inputs
    if not isinstance(action, str):
        action = str(action) if action is not None else ""
    if not isinstance(component, str):
        component = str(component) if component is not None else ""
    if not isinstance(issue, str):
        issue = str(issue) if issue is not None else ""
    if not isinstance(template_pattern, str):
        template_pattern = "The {action} on {component} causes {issue}"

    # CRITICAL SECURITY FIX: Sanitize inputs BEFORE any processing
    # This ensures dangerous patterns are removed before template processing
    safe_action = sanitize_for_concatenation(action, max_length=50)
    safe_component = sanitize_for_concatenation(component, max_length=50)
    safe_issue = sanitize_for_concatenation(issue, max_length=100)

    # SECURITY: Use context-aware template processing that prevents cross-contamination
    # The key insight: only replace placeholders that existed in the ORIGINAL template
    # Do NOT process placeholder patterns that come from user input

    # Find placeholder positions in the ORIGINAL template before any processing
    import re

    # Store original template
    original_template = template_pattern

    # Create a list of all placeholder positions in the original template
    placeholder_positions = []
    for match in re.finditer(r'\{(action|component|issue)\}', original_template):
        placeholder_positions.append((match.start(), match.end(), match.group(1)))

    # SECURITY: Build result by processing template segments
    # This approach completely eliminates cross-contamination
    result_parts = []
    last_end = 0

    for start, end, placeholder_type in placeholder_positions:
        # Add literal text segment (unprocessed)
        if start > last_end:
            result_parts.append(original_template[last_end:start])

        # Add the appropriate safe value for this placeholder
        if placeholder_type == 'action':
            result_parts.append(safe_action)
        elif placeholder_type == 'component':
            result_parts.append(safe_component)
        elif placeholder_type == 'issue':
            result_parts.append(safe_issue)

        last_end = end

    # Add any remaining literal text
    if last_end < len(original_template):
        result_parts.append(original_template[last_end:])

    # Combine all parts
    result = ''.join(result_parts)

    # SECURITY: Final validation to ensure no dangerous patterns
    dangerous_patterns = [
        '__import__', 'system(', 'exec(', 'eval(', 'subprocess',
        'popen', 'getattr', 'setattr', '__class__', '__base__',
        '__subclasses__', '${', '%(', '{{', '}}'
    ]

    for pattern in dangerous_patterns:
        if pattern in result:
            # Emergency fallback - remove dangerous content
            result = result.replace(pattern, '')

    # Ensure result is not empty and properly formatted
    if not result.strip():
        result = f"Unknown issue affecting {safe_component or 'system'}"

    # Capitalize first letter for proper formatting
    if result and result[0].islower():
        result = result[0].upper() + result[1:]

    return result.strip()


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

    # SAFE: Use .get() with defaults to prevent KeyError if 'keywords' key is missing
    for domain_name, domain_info in DOMAIN_TEMPLATES.items():
        keywords = domain_info.get("keywords", [])
        if any(keyword in all_text for keyword in keywords):
            domain = domain_name
            break

    if not domain:
        return []

    keywords = _extract_keywords_with_context(observations, context)
    template_hyps = []

    for idx, template in enumerate(
        DOMAIN_TEMPLATES[domain]["templates"][:max_hypotheses]
    ):
        # SAFE: Use .get() with defaults to prevent KeyError if keys are missing
        actions_list = keywords.get("actions", [])
        components_list = keywords.get("components", [])
        issues_list = keywords.get("issues", [])

        # Select best keywords for this template
        action = actions_list[0] if actions_list else "recent change"
        component = (
            components_list[
                min(idx, len(components_list) - 1)
            ] if components_list else "system"
        )
        issue = (
            issues_list[
                min(idx, len(issues_list) - 1)
            ] if issues_list else "performance issue"
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

        # CRITICAL SECURITY FIX: Use safe template function instead of vulnerable template.format()
        hypothesis_text = _safe_hypothesis_template(action, component, issue, template)

        # CRITICAL SECURITY FIX: Sanitize inputs for testable predictions too
        safe_action = _sanitize_input_for_concatenation(action)
        safe_component = _sanitize_input_for_concatenation(component)
        safe_issue = _sanitize_input_for_concatenation(issue)

        template_hyps.append({
            "hypothesis": hypothesis_text,
            "explains": list(range(observations_count)),
            "confidence": BASE_CONFIDENCE_TEMPLATE_HYPOTHESIS,
            "assumptions": ["Context '{context}' is relevant to the issue"],
            "testable_predictions": [
                f"Reverting the {safe_action} should reduce or resolve the {safe_issue}",
                f"Monitoring {safe_component} metrics should show correlation with the issue"
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
    # Explicit None validation to ensure ValidationError is raised
    if observations is None:
        raise ValidationError("observations cannot be None")

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

    # SAFE: Sort hypotheses by confidence with fallback to prevent KeyError
    hypotheses.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
    hypotheses = hypotheses[:max_hypotheses]

    if reasoning_chain:
        reasoning_chain.add_step(
            stage=stage,
            description=description,
            result=hypotheses,
            confidence=max([h.get("confidence", 0.0) for h in hypotheses]) if hypotheses else 0.0,
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
    # Explicit None validation to ensure ValidationError is raised
    if hypotheses is None:
        raise ValidationError("hypotheses cannot be None")

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
            # SAFE: Use .get() with default to prevent KeyError if 'hypothesis' key is missing
            hypothesis_text = hypothesis.get("hypothesis", "")
            if not hypothesis_text:
                # Skip evidence matching for hypotheses without text
                continue
            hypothesis_keywords = set(_extract_keywords(hypothesis_text))

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

        # SAFE: Update hypothesis description if strong evidence - check if hypothesis key exists first
        hypothesis_text = updated_hypothesis.get("hypothesis", "")
        if hypothesis_text:  # Only update if hypothesis text exists
            if avg_evidence_support > EVIDENCE_SUPPORT_HIGH_THRESHOLD:
                updated_hypothesis["hypothesis"] += " (strongly supported by new evidence)"
            elif avg_evidence_support > EVIDENCE_SUPPORT_MODERATE_THRESHOLD:
                updated_hypothesis["hypothesis"] += " (supported by new evidence)"
        else:
            # If hypothesis doesn't exist, create a default one
            updated_hypothesis["hypothesis"] = "Hypothesis updated with new evidence"

        updated_hypotheses.append(updated_hypothesis)

    # SAFE: Re-sort by updated confidence with fallback to prevent KeyError
    updated_hypotheses.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

    if reasoning_chain:
        reasoning_chain.add_step(
            stage = stage,
            description = description,
            result = updated_hypotheses,
            confidence = max([h.get("confidence", 0.0) for h in updated_hypotheses]) if updated_hypotheses else 0.0,
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

    # SAFE: Select the hypothesis with highest confidence using .get() to prevent KeyError
    best_hypothesis = max(validated_hypotheses, key=lambda x: x.get("confidence", 0.0))

    # Add evaluation metadata
    best_hypothesis["evaluation"] = {
        "total_hypotheses": len(validated_hypotheses),
        "rank": 1,
        "selected_as_best": True,
        "selection_reason": f"Highest confidence score ({best_hypothesis.get('confidence', 0.0):.3f})"
    }

    if reasoning_chain:
        reasoning_chain.add_step(
            stage = stage,
            description = description,
            result = best_hypothesis,
            confidence = best_hypothesis.get("confidence", 0.0),
            evidence = f"Selected from {len(hypotheses)} hypotheses based on confidence score",
            assumptions=[
                "Higher confidence indicates better explanation",
                "All relevant hypotheses were considered"
            ]
        )

    return best_hypothesis
