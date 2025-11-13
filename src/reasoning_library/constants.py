"""
Constants module for the reasoning library.

This module contains well-documented constants that were previously magic numbers
scattered throughout the codebase. Each constant is documented with its purpose,
chosen value, and reasoning.

The constants are organized by functional area:
- Security and performance thresholds
- Confidence calculation parameters
- Pattern detection tolerances
- Text processing limits
- Statistical calculation factors
"""

# =============================================================================
# SECURITY AND PERFORMANCE THRESHOLDS
# =============================================================================

# DoS Protection Constants
# ------------------------
# These limits prevent denial-of-service attacks from malicious inputs
# while maintaining reasonable functionality for legitimate use cases.

MAX_SEQUENCE_LENGTH = 1000
"""
Maximum allowed sequence length to prevent DoS attacks.

Chosen because:
- 1K elements is sufficient for legitimate pattern detection tasks
- Prevents memory exhaustion from large sequences (CRIT-002 fix)
- Maintains reasonable computation times even for recursive sequences
- Larger sequences would likely indicate malicious input or misuse
- Reduces attack surface for algorithmic DoS vulnerabilities

Security impact: Prevents memory exhaustion and CPU exhaustion attacks.
Limits exposure to exponential computation attacks in recursive sequences.
"""

COMPUTATION_TIMEOUT = 5.0
"""
Maximum computation time in seconds for intensive operations.

Chosen because:
- 5 seconds is sufficient for most legitimate pattern detection
- Prevents CPU exhaustion attacks from infinite loops or complex calculations
- Balances security with functionality - longer operations are rarely needed
- Allows for complex recursive patterns while preventing abuse

Security impact: Prevents CPU exhaustion attacks and ensures responsive service.
"""

# CRIT-002: Algorithmic DoS Protection Constants
# ----------------------------------------------

EXPONENTIAL_GROWTH_THRESHOLD = 2.0
"""
Growth ratio threshold to detect exponential sequences for DoS protection.

Chosen because:
- Ratio of 2.0 indicates exponential growth (each term doubles previous)
- Helps identify sequences that will cause computational explosion
- Recursive sequences with ratio > 2.0 can quickly exceed value limits
- Early detection prevents excessive computation

Security impact: Prevents algorithmic DoS from exponential sequence attacks.
"""

EXPONENTIAL_GROWTH_WINDOW = 5
"""
Window size to check for exponential growth patterns.

Chosen because:
- 5 consecutive elements provide reliable exponential growth detection
- Short enough to catch growth early in the sequence
- Long enough to avoid false positives from random fluctuations
- Balances detection accuracy with computational overhead

Security impact: Early detection of exponential sequences prevents DoS attacks.
"""

MAX_MEMORY_ELEMENTS = 5000
"""
Maximum elements for memory-intensive operations.

Chosen because:
- 5K elements provides good performance for statistical calculations
- Prevents memory exhaustion from operations like numpy array creation
- Accounts for memory overhead of intermediate calculations
- Well within typical memory limits for most systems

Security impact: Prevents memory exhaustion attacks during computation.
"""

MAX_OBSERVATION_LENGTH = 10000
"""
Maximum length for each observation string to prevent DoS attacks.

Chosen because:
- 10K characters is sufficient for detailed observations
- Prevents memory exhaustion from extremely long strings
- Maintains reasonable processing times for string operations
- Longer observations would likely indicate malformed input

Security impact: Prevents memory exhaustion from string processing attacks.
"""

MAX_CONTEXT_LENGTH = 5000
"""
Maximum length for context strings to prevent DoS attacks.

Chosen because:
- 5K characters provides adequate context for hypothesis generation
- Context is typically shorter than individual observations
- Prevents memory exhaustion while maintaining functionality
- Balances security with the need for sufficient context

Security impact: Prevents memory exhaustion from context processing attacks.
"""

VALUE_MAGNITUDE_LIMIT = 1e15
"""
Maximum allowed value magnitude to prevent overflow in calculations.

Chosen because:
- 1e15 is well within floating-point precision limits
- Allows for legitimate large numbers in sequences
- Prevents overflow errors in arithmetic operations
- Provides safety margin for intermediate calculations

Security impact: Prevents arithmetic overflow and computational errors.
"""

MAX_SOURCE_CODE_SIZE = 10000
"""
Prevent ReDoS attacks by limiting input size for source code analysis.

Chosen because:
- 10K characters is sufficient for most function source code
- Prevents regex DoS attacks from extremely large source files
- Maintains reasonable performance for code analysis
- Larger source files would rarely need analysis

Security impact: Prevents ReDoS attacks in regex processing of source code.
"""

# =============================================================================
# PERFORMANCE OPTIMIZATION THRESHOLDS
# =============================================================================

LARGE_SEQUENCE_THRESHOLD = 100
"""
Switch to optimized algorithms for sequences larger than this threshold.

Chosen because:
- 100 elements is where performance differences become noticeable
- Optimized algorithms have overhead that's justified at this size
- Below this threshold, simple algorithms are actually faster
- Provides good performance balance across sequence sizes

Performance impact: Improves performance for large sequences while maintaining speed for small ones.
"""

EARLY_EXIT_TOLERANCE = 1e-12
"""
Tolerance for detecting perfect patterns early to optimize performance.

Chosen because:
- 1e-12 is tight enough to detect truly perfect patterns
- Loose enough to account for floating-point precision errors
- Provides significant performance improvement for ideal sequences
- Prevents false positives from floating-point noise

Performance impact: Saves ~50% computation time for perfect patterns.
"""

MAX_CACHE_SIZE = 1000
"""
Cache size limit to prevent unbounded growth and memory exhaustion.

Chosen because:
- 1K entries provides good cache hit rates for repeated operations
- Prevents memory exhaustion from unbounded cache growth
- Reasonable memory footprint (~100KB per cache)
- Balances performance benefits with memory usage

Performance impact: Provides caching benefits while preventing memory issues.
"""

MAX_REGISTRY_SIZE = 500
"""
Registry size limits to prevent memory exhaustion attacks.

Chosen because:
- ~100 bytes per registry entry × 500 entries = ~50KB memory usage
- Sufficient capacity for most legitimate tool registries
- Prevents DoS while maintaining reasonable tool capacity
- Small enough to not impact system performance

Security impact: Prevents memory exhaustion from registry pollution attacks.
"""

MAX_CONVERSATIONS = 1000
"""
Configurable limit to prevent memory DoS in conversation tracking.

Chosen because:
- 1K conversations is sufficient for most applications
- Prevents memory exhaustion from conversation accumulation
- Provides reasonable session management
- Limits impact of memory leaks in conversation tracking

Security impact: Prevents memory exhaustion from conversation storage attacks.
"""

# =============================================================================
# CONFIDENCE CALCULATION PARAMETERS
# =============================================================================

# Base Confidence Values
# ----------------------
# These represent baseline confidence levels for different reasoning types
# before adjustment by evidence, complexity, and other factors.

BASE_CONFIDENCE_ARITHMETIC = 0.95
"""
Base confidence for arithmetic progression detection.

Chosen because:
- Arithmetic patterns are typically reliable when detected
- High base confidence reflects the mathematical certainty of arithmetic sequences
- Still allows for reduction by evidence quality and complexity factors
- Provides strong but not absolute confidence in simple mathematical patterns

Reasoning: Arithmetic progressions have strong mathematical foundations and are
less prone to false positives than more complex patterns.
"""

BASE_CONFIDENCE_GEOMETRIC = 0.95
"""
Base confidence for geometric progression detection.

Chosen because:
- Geometric patterns are mathematically precise when detected
- Similar reliability to arithmetic patterns
- High confidence reflects the deterministic nature of geometric sequences
- Accounts for the clarity of geometric relationships

Reasoning: Like arithmetic patterns, geometric progressions have clear mathematical
definitions and are less ambiguous than complex patterns.
"""

BASE_CONFIDENCE_ABDUCTIVE = 0.7
"""
Base confidence for abductive reasoning hypotheses.

Chosen because:
- Abductive reasoning deals with inference to best explanation, which is inherently uncertain
- Lower than mathematical patterns due to the subjective nature of explanations
- Still provides reasonable confidence in generated hypotheses
- Allows for significant adjustment based on evidence quality

Reasoning: Abductive reasoning involves uncertainty about the "best" explanation,
so confidence starts lower and is heavily influenced by supporting evidence.
"""

BASE_CONFIDENCE_CHAIN_OF_THOUGHT = 0.8
"""
Conservative default confidence for chain-of-thought reasoning steps.

Chosen because:
- Chain-of-thought reasoning involves multiple steps, each with potential error
- Conservative default accounts for cumulative uncertainty across steps
- Higher than abductive reasoning due to more structured approach
- Provides balanced confidence in sequential reasoning

Reasoning: Multi-step reasoning accumulates uncertainty, so each step should
have conservative confidence that can be adjusted based on step quality.
"""

BASE_CONFIDENCE_DEDUCTIVE = 1.0
"""
Confidence for deductive reasoning operations.

Chosen because:
- Valid deductive reasoning is logically certain when premises are true
- Maximum confidence reflects the logical necessity of deductive conclusions
- Assumes valid application of deductive rules
- Represents the ideal confidence for sound logical inference

Reasoning: Deductive reasoning, when correctly applied, yields logically necessary
conclusions from true premises, justifying maximum confidence.
"""

BASE_CONFIDENCE_TEMPLATE_HYPOTHESIS = 0.6
"""
Base confidence for domain-specific template hypotheses.

Chosen because:
- Template hypotheses are based on patterns but may not fit specific cases
- Lower than pattern detection due to generic nature of templates
- Provides reasonable starting confidence for domain-specific reasoning
- Allows for significant adjustment based on context relevance

Reasoning: Templates provide structure but may not perfectly match specific situations,
warranting moderate base confidence.
"""

BASE_CONFIDENCE_RECURSIVE = 0.9
"""
Base confidence for recursive pattern detection.

Chosen because:
- Recursive patterns (Fibonacci, Lucas, etc.) are mathematically precise
- High confidence reflects the clear definition of recursive relationships
- Slightly lower than arithmetic/geometric due to complexity
- Accounts for the strong mathematical foundation of recursive sequences

Reasoning: Recursive sequences have clear mathematical definitions but are more
complex than simple arithmetic/geometric patterns.
"""

BASE_CONFIDENCE_POLYNOMIAL = 0.85
"""
Base confidence for polynomial pattern detection.

Chosen because:
- Polynomial fitting provides good mathematical foundation
- High confidence reflects the reliability of polynomial regression
- Lower than simple sequences due to potential overfitting
- Accounts for the statistical nature of polynomial fitting

Reasoning: Polynomial patterns are mathematically sound but involve statistical
fitting, warranting slightly lower confidence than exact patterns.
"""

BASE_CONFIDENCE_EXPONENTIAL = 0.9
"""
Base confidence for exponential pattern detection (capped).

Chosen because:
- Exponential patterns have strong mathematical basis
- High confidence reflects the clarity of exponential relationships
- Capped at 0.9 to account for fitting complexity
- Provides strong but not absolute confidence in exponential trends

Reasoning: Exponential patterns are mathematically precise but involve fitting,
so confidence is high but capped below absolute certainty.
"""

BASE_CONFIDENCE_PATTERN_DESCRIPTION = 0.9
"""
Base confidence for pattern description (higher than prediction).

Chosen because:
- Pattern description is less risky than prediction
- 0.9 provides high confidence for identified patterns
- Higher than prediction confidence due to lower risk
- Appropriate for descriptive pattern analysis

Reasoning: Describing existing patterns is less risky than predicting future values,
justifying higher confidence in pattern identification.
"""

# Complexity Score Factors
# -----------------------
# These represent the inherent complexity of different reasoning types,
# used to reduce confidence based on complexity.

COMPLEXITY_SCORE_ARITHMETIC = 0.0
"""
Complexity score for arithmetic progression (simplest pattern).

Chosen because:
- Arithmetic sequences are the simplest mathematical pattern
- No complexity penalty for the most basic pattern type
- Maximum confidence factor for arithmetic patterns
- Reflects the simplicity and reliability of arithmetic relationships

Reasoning: Arithmetic progressions require only finding a constant difference,
making them the least complex pattern to detect and verify.
"""

COMPLEXITY_SCORE_GEOMETRIC = 0.1
"""
Complexity score for geometric progression.

Chosen because:
- Slightly more complex than arithmetic (requires ratio calculation)
- Small complexity penalty for division operations
- Near-maximum confidence factor for geometric patterns
- Accounts for potential division by zero and ratio variability

Reasoning: Geometric progressions require ratio calculation and handle zero values,
making them slightly more complex than arithmetic sequences.
"""

COMPLEXITY_SCORE_RECURSIVE = 0.3
"""
Complexity score for recursive pattern detection.

Chosen because:
- Recursive patterns involve multiple previous terms
- Higher complexity due to recursive relationship tracking
- Significant complexity penalty for recursive computation
- Accounts for the computational complexity of recursive sequence generation

Reasoning: Recursive sequences require tracking multiple previous terms and
computing recursive relationships, increasing complexity significantly.
"""

COMPLEXITY_SCORE_POLYNOMIAL_DEGREE_FACTOR = 0.1
"""
Complexity factor multiplier for polynomial degree.

Chosen because:
- Higher degree polynomials are more complex to fit and verify
- Linear increase in complexity with polynomial degree
- Balances confidence reduction with polynomial complexity
- Prevents overconfidence in high-degree polynomial fits

Reasoning: Polynomial complexity increases with degree due to more parameters
to fit and higher risk of overfitting.
"""

# Simplicity and Specificity Factors
# ----------------------------------
# These factors adjust confidence based on hypothesis characteristics.

SIMPLICITY_ASSUMPTION_PENALTY = 0.2
"""
Penalty factor for each additional assumption in abductive hypotheses.

Chosen because:
- Each additional assumption reduces hypothesis reliability (Occam's razor)
- 0.2 penalty provides significant but not overwhelming confidence reduction
- Encourages simpler explanations when possible
- Balances explanatory power with simplicity

Reasoning: Based on Occam's razor principle - simpler explanations are
preferable when they explain the same observations.
"""

SPECIFICITY_PREDICTIONS_MINIMUM = 3.0
"""
Minimum number of testable predictions for maximum specificity factor.

Chosen because:
- 3 predictions provide reasonable testability without being overly restrictive
- Encourages specific, falsifiable hypotheses
- Prevents over-penalizing hypotheses with fewer predictions
- Balances specificity with practical hypothesis generation

Reasoning: More specific hypotheses (with testable predictions) are more reliable,
but requiring too many predictions would be overly restrictive.
"""

EVIDENCE_SUPPORT_MULTIPLIER = 0.5
"""
Multiplier for confidence adjustment based on supporting evidence.

Chosen because:
- Provides significant confidence boost when evidence is strong
- 0.5 multiplier allows confidence to increase by up to 50%
- Balances original hypothesis confidence with evidential support
- Prevents evidence from completely overriding original reasoning

Reasoning: Supporting evidence should increase confidence but not completely
override the original hypothesis evaluation.
"""

# =============================================================================
# PATTERN DETECTION TOLERANCES
# =============================================================================

# Floating Point Comparison Tolerances
# ------------------------------------
# These tolerances account for floating-point precision in pattern matching.

RELATIVE_TOLERANCE_DEFAULT = 0.2
"""
Default relative tolerance for pattern detection (20% variance).

Chosen because:
- 20% variance allows for reasonable noise in real-world data
- Tight enough to prevent false positives from random data
- Loose enough to detect patterns in imperfect data
- Provides good balance between sensitivity and specificity

Reasoning: Real-world data often contains noise and measurement errors,
so pattern detection should accommodate reasonable variance.
"""

RELATIVE_TOLERANCE_STRICT = 0.1
"""
Strict relative tolerance for precise pattern matching (10% variance).

Chosen because:
- 10% variance for applications requiring higher precision
- Used when patterns should be very clear and consistent
- Reduces false positives at the cost of some sensitivity
- Appropriate for mathematical sequences with low noise

Reasoning: Some applications require higher precision in pattern detection,
warranting stricter tolerance for variance.
"""

ABSOLUTE_TOLERANCE_DEFAULT = 1e-8
"""
Default absolute tolerance for floating-point comparisons.

Chosen because:
- 1e-8 is appropriate for double-precision floating-point arithmetic
- Tight enough to detect exact mathematical relationships
- Loose enough to account for floating-point rounding errors
- Standard tolerance for numerical comparisons in scientific computing

Reasoning: Floating-point arithmetic introduces small precision errors that
must be accommodated in exact pattern detection.
"""

ABSOLUTE_TOLERANCE_PATTERN = 1e-10
"""
Tolerance for detecting perfect patterns in recursive sequence detection.

Chosen because:
- 1e-10 is tighter than default tolerance for pattern detection
- Recursive patterns should match exactly when present
- Prevents false positives in recursive sequence detection
- Appropriate for mathematical sequences that should be precise

Reasoning: Recursive mathematical sequences should match exactly when
the pattern is present, warranting very tight tolerance.
"""

NUMERICAL_STABILITY_THRESHOLD = 1e-10
"""
Threshold for numerical stability in statistical calculations.

Chosen because:
- 1e-10 prevents division by very small numbers that cause instability
- Tight enough to maintain numerical precision
- Loose enough to handle legitimate small values
- Standard threshold for numerical stability in scientific computing

Reasoning: Statistical calculations can become unstable when dividing by
very small numbers, requiring a minimum threshold for numerical stability.
"""

# =============================================================================
# TEXT PROCESSING LIMITS
# =============================================================================

# String Length Limits
# --------------------
# These limits prevent memory exhaustion and performance issues in text processing.

KEYWORD_EXTRACTION_OBSERVATION_LIMIT = 1000
"""
Smaller limit for keyword extraction from observations.

Chosen because:
- Keyword extraction is less memory-intensive than full processing
- 1K characters provides sufficient context for keyword identification
- Reduces memory usage in text processing operations
- Maintains functionality while preventing abuse

Reasoning: Keyword extraction can work effectively with shorter text segments,
reducing memory requirements for text processing.
"""

KEYWORD_EXTRACTION_CONTEXT_LIMIT = 500
"""
Smaller limit for keyword extraction from context.

Chosen because:
- Context is typically more concise than observations
- 500 characters provides adequate context for keyword extraction
- Further reduces memory usage for context processing
- Sufficient for most contextual keyword identification

Reasoning: Context strings are usually shorter and more focused, allowing
for smaller limits while maintaining effectiveness.
"""

DOMAIN_DETECTION_LIMIT = 50000
"""
50KB limit for domain detection in text processing.

Chosen because:
- 50KB provides substantial text for domain keyword detection
- Prevents memory exhaustion in domain identification
- Larger than individual observation limits to account for combined text
- Maintains reasonable performance for text analysis

Reasoning: Domain detection may need to analyze combined text from multiple
sources, requiring larger limits than individual text processing.
"""

HYPOTHESIS_TEXT_HARD_LIMIT = 500
"""
Hard limit for contextual hypotheses text length.

Chosen because:
- 500 characters provides sufficient space for meaningful hypothesis text
- Prevents overly long hypotheses that become unwieldy
- Maintains readability and usability of generated hypotheses
- Prevents memory issues in hypothesis storage and processing

Reasoning: Hypotheses should be concise and meaningful, requiring limits
to prevent unwieldy text generation.
"""

# Keyword Length Limits
# ---------------------
# These limits prevent excessively long keywords that may indicate malformed input.

KEYWORD_LENGTH_LIMIT = 50
"""
Maximum length for individual keywords.

Chosen because:
- 50 characters accommodates meaningful technical terms
- Prevents abuse from extremely long word-like strings
- Maintains usability of keyword extraction results
- Excludes most malformed input while preserving legitimate terms

Reasoning: Legitimate keywords are typically concise, while very long strings
often indicate malformed input or abuse attempts.
"""

COMPONENT_LENGTH_LIMIT = 50
"""
Maximum length for component names in hypothesis generation.

Chosen because:
- 50 characters accommodates system component names
- Prevents unwieldy component references in hypotheses
- Maintains readability of generated hypotheses
- Sufficient for most technical component identifiers

Reasoning: System component names should be descriptive but concise,
requiring limits to maintain hypothesis readability.
"""

ISSUE_LENGTH_LIMIT = 100
"""
Maximum length for issue descriptions in hypothesis generation.

Chosen because:
- 100 characters allows for descriptive issue identification
- Longer than component/action limits due to descriptive nature
- Prevents overly verbose issue descriptions
- Maintains balance between detail and conciseness

Reasoning: Issue descriptions may need more detail than component names,
warranting slightly larger limits while maintaining conciseness.
"""

# =============================================================================
# STATISTICAL CALCULATION FACTORS
# =============================================================================

# Data Sufficiency Thresholds
# ---------------------------
# Minimum data points required for reliable pattern detection.

DATA_SUFFICIENCY_MINIMUM_ARITHMETIC = 4
"""
Minimum required data points for arithmetic progression detection.

Chosen because:
- 3 points define an arithmetic progression, 4 provides verification
- Statistical reliability improves with more data points
- Prevents false positives from very short sequences
- Balance between reliability and practical applicability

Reasoning: While 3 points can define an arithmetic progression, 4 points
provide better verification and reduce false positive risk.
"""

DATA_SUFFICIENCY_MINIMUM_GEOMETRIC = 4
"""
Minimum required data points for geometric progression detection.

Chosen because:
- 3 points define a geometric progression, 4 provides verification
- Similar requirements to arithmetic progression
- Accounts for potential zero or negative values in geometric sequences
- Ensures reliable ratio calculation across multiple points

Reasoning: Geometric progressions need sufficient points to establish
consistent ratios and verify the pattern.
"""

DATA_SUFFICIENCY_MINIMUM_DEFAULT = 3
"""
Default conservative minimum for unknown pattern types.

Chosen because:
- 3 points provide basic pattern indication
- Conservative approach for unknown or complex patterns
- Prevents premature pattern detection with insufficient data
- Balance between sensitivity and reliability

Reasoning: When pattern type is unknown, use conservative minimum
to avoid false pattern detection.
"""

DATA_SUFFICIENCY_MINIMUM_RECURSIVE = 5
"""
Minimum required data points for reliable recursive pattern detection.

Chosen because:
- Recursive patterns need more points to establish recursive relationships
- 5 points provide sufficient data for sequences like Fibonacci, Lucas
- Accounts for the complexity of recursive rule identification
- Reduces false positives in recursive pattern detection

Reasoning: Recursive sequences require more data points to establish
the recursive rule and verify it across multiple iterations.
"""

DATA_SUFFICIENCY_MINIMUM_FIBONACCI = 5
"""
Minimum required data points for reliable Fibonacci detection.

Chosen because:
- Fibonacci sequence needs at least 5 terms to establish the pattern
- 2 seed terms + 3 generated terms provide good verification
- Prevents false positives from coincidental sequences
- Ensures reliable identification of the recursive rule

Reasoning: Fibonacci patterns need sufficient terms to verify that
each term equals the sum of the two preceding terms.
"""

DATA_SUFFICIENCY_MINIMUM_LUCAS = 5
"""
Minimum required data points for reliable Lucas detection.

Chosen because:
- Lucas sequence follows same rule as Fibonacci but different seeds
- 5 terms provide good verification of Lucas-specific pattern
- Prevents confusion with other recursive sequences
- Ensures accurate identification of Lucas versus Lucas-like sequences

Reasoning: Lucas sequences need the same verification as Fibonacci
to establish the recursive rule and seed pattern.
"""

DATA_SUFFICIENCY_MINIMUM_TRIBONACCI = 6
"""
Minimum required data points for reliable Tribonacci detection.

Chosen because:
- Tribonacci requires 3 seed terms plus generated terms
- 6 terms provide sufficient verification of the 3-term recursive rule
- More complex than Fibonacci/Lucas, requiring more verification data
- Prevents false positives from coincidental sequences

Reasoning: Tribonacci sequences are more complex (3-term recursion)
and thus require more data points for reliable detection.
"""

DATA_SUFFICIENCY_MINIMUM_POLYNOMIAL = 2
"""
Minimum data points for polynomial fitting (degree + 2).

Chosen because:
- Polynomial of degree n requires at least n+2 points for reliable fitting
- 2 additional points provide verification beyond the minimum required
- Prevents overfitting with insufficient data
- Ensures statistical reliability of polynomial regression

Reasoning: Polynomial fitting requires more points than the polynomial
degree to provide reliable parameter estimation and verification.
"""

# Pattern Quality Factors
# -----------------------
# Quality factors for different amounts of pattern data.

PATTERN_QUALITY_MINIMAL_DATA = 0.7
"""
Conservative pattern quality factor for minimal data situations.

Chosen because:
- 0.7 provides reasonable confidence with minimal data
- Conservative approach prevents overconfidence with limited information
- Allows for pattern detection while acknowledging uncertainty
- Balance between sensitivity and reliability with small datasets

Reasoning: With minimal data points, pattern quality should be assessed
conservatively to avoid false confidence in uncertain patterns.
"""

PATTERN_QUALITY_GEOMETRIC_MINIMUM = 0.1
"""
Minimum pattern quality factor for geometric patterns with near-zero mean.

Chosen because:
- Prevents division by zero in geometric pattern quality calculation
- 0.1 provides minimum confidence even with problematic data
- Ensures calculation stability with edge cases
- Prevents complete confidence loss in edge cases

Reasoning: Geometric patterns with near-zero mean ratios can cause numerical
instability, requiring a minimum quality factor for stability.
"""

PATTERN_QUALITY_DEFAULT_UNKNOWN = 0.5
"""
Default pattern quality factor for unknown pattern types.

Chosen because:
- 0.5 provides neutral confidence assessment for unknown patterns
- Conservative approach when pattern type cannot be determined
- Prevents overconfidence in unidentifiable patterns
- Balance between acknowledging potential patterns and uncertainty

Reasoning: When pattern type cannot be determined, use neutral confidence
that neither overstates nor understates pattern quality.
"""

# Statistical Calculation Parameters
# ---------------------------------

COEFFICIENT_OF_VARIATION_DECAY_FACTOR = 2.0
"""
Decay factor for exponential penalty based on coefficient of variation.

Chosen because:
- 2.0 provides significant penalty for high variance in patterns
- Exponential decay rapidly reduces confidence with increasing variance
- Balances penalty severity with pattern quality assessment
- Prevents false confidence in noisy or inconsistent patterns

Reasoning: Higher coefficient of variation indicates less consistent patterns,
warranting exponential confidence penalty.
"""

# =============================================================================
# CACHE AND REGISTRY MANAGEMENT
# =============================================================================

# Cache Eviction Parameters
# -------------------------

CACHE_EVICTION_FRACTION = 0.25
"""
Fraction of cache entries to remove when cache size limit is reached.

Chosen because:
- Removing 25% of entries provides good cache performance after eviction
- Prevents frequent cache eviction cycles
- Balance between memory usage and cache effectiveness
- Standard cache eviction strategy (FIFO with fractional removal)

Reasoning: Removing a fraction of entries rather than just one prevents
immediate cache overflow and maintains good cache performance.
"""

REGISTRY_EVICTION_FRACTION = 0.25
"""
Fraction of registry entries to remove when registry size limit is reached.

Chosen because:
- 25% eviction prevents frequent registry management operations
- Maintains reasonable registry capacity after eviction
- Balance between memory usage and registry functionality
- Consistent with cache eviction strategy

Reasoning: Registry management should be infrequent but effective,
removing enough entries to prevent immediate overflow.
"""

# =============================================================================
# TIMEOUT AND CHECKPOINT PARAMETERS
# =============================================================================

# Computation Checkpoint Parameters
# ---------------------------------

TIMEOUT_CHECK_INTERVAL = 100
"""
Check timeout every N iterations to prevent DoS attacks.

Chosen because:
- Every 100 iterations provides better protection against fast attacks (CRIT-002 fix)
- Prevents excessive timeout checking overhead while being more secure
- Ensures timely detection of timeout conditions in exponential computations
- Reduces window for DoS attacks in recursive sequence algorithms

Reasoning: Timeout checking should be frequent enough to prevent DoS attacks
even against fast-growing exponential sequences. 100 iterations balances
security with performance for recursive computations.
"""

# =============================================================================
# CONFIDENCE BOUNDARIES
# =============================================================================

# Confidence Range Parameters
# ---------------------------

CONFIDENCE_MIN = 0.0
"""
Minimum allowed confidence value.

Chosen because:
- 0.0 represents complete uncertainty or no confidence
- Standard lower bound for confidence values
- Prevents negative confidence values
- Consistent with probability theory conventions

Reasoning: Confidence values represent probability-like assessments,
with 0.0 being the minimum possible confidence.
"""

CONFIDENCE_MAX = 1.0
"""
Maximum allowed confidence value.

Chosen because:
- 1.0 represents complete certainty
- Standard upper bound for confidence values
- Prevents confidence values exceeding 100%
- Consistent with probability theory conventions

Reasoning: Confidence values represent probability-like assessments,
with 1.0 being the maximum possible confidence.
"""

EVIDENCE_SUPPORT_HIGH_THRESHOLD = 0.7
"""
Threshold for high evidence support in hypothesis ranking.

Chosen because:
- 0.7 indicates strong supporting evidence
- Triggers special labeling for strongly supported hypotheses
- High enough to indicate meaningful evidence support
- Prevents over-labeling of moderately supported hypotheses

Reasoning: Hypotheses with strong evidence support should be identified
to highlight the most well-supported explanations.
"""

EVIDENCE_SUPPORT_MODERATE_THRESHOLD = 0.3
"""
Threshold for moderate evidence support in hypothesis ranking.

Chosen because:
- 0.3 indicates meaningful but not strong evidence support
- Triggers moderate labeling for supported hypotheses
- Low enough to include reasonably supported hypotheses
- High enough to exclude weakly supported hypotheses

Reasoning: Distinguishes between levels of evidence support to provide
nuanced hypothesis evaluation and ranking.
"""

# =============================================================================
# HYPOTHESIS GENERATION PARAMETERS
# =============================================================================

# Hypothesis Generation Limits
# ----------------------------

MAX_HYPOTHESES_DEFAULT = 5
"""
Default maximum number of hypotheses to generate.

Chosen because:
- 5 hypotheses provide good variety without overwhelming users
- Manages computational complexity of hypothesis evaluation
- Sufficient for most abductive reasoning scenarios
- Prevents generation of excessive low-quality hypotheses

Reasoning: Hypothesis generation should provide diverse explanations
while maintaining manageable complexity and quality.
"""

MAX_THEMES_RETURNED = 10
"""
Return top N themes from common theme analysis.

Chosen because:
- 10 themes provide good variety for hypothesis generation
- Manages complexity while ensuring comprehensive coverage
- Prevents overwhelming hypothesis generation with too many themes
- Sufficient for most observation sets

Reasoning: Theme extraction should provide comprehensive coverage
while maintaining manageable complexity for downstream processing.
"""

THEME_FREQUENCY_THRESHOLD = 2
"""
Minimum frequency for themes to be considered "common".

Chosen because:
- Themes appearing at least twice suggest pattern significance
- Prevents inclusion of rare or coincidental themes
- Ensures themes have some recurrence in observations
- Balance between inclusivity and relevance

Reasoning: Common themes should appear multiple times to indicate
genuine patterns rather than coincidences.
"""

# Template Generation Parameters
# ------------------------------

MAX_TEMPLATE_KEYWORDS = 3
"""
Maximum number of keywords to use in template hypothesis generation.

Chosen because:
- 3 keywords provide sufficient context for template filling
- Prevents overly complex or confusing hypothesis templates
- Maintains readability and clarity of generated hypotheses
- Balance between specificity and simplicity

Reasoning: Template hypotheses should be specific enough to be meaningful
but simple enough to remain clear and usable.
"""

# =============================================================================
# DOMAIN DETECTION PARAMETERS
# =============================================================================

# Domain Matching Parameters
# --------------------------

MIN_OBSERVATIONS_FOR_DOMAIN_DETECTION = 6
"""
Minimum observations needed for reliable domain detection.

Chosen because:
- 6 observations provide sufficient data for domain keyword matching
- Prevents domain detection with insufficient context
- Ensures reliable identification of domain-specific patterns
- Balance between sensitivity and reliability

Reasoning: Domain detection needs sufficient observations to identify
consistent domain-specific keywords and patterns.
"""

MAX_PATTERN_PERIOD = 5
"""
Maximum period to check for periodic patterns in sequences.

Chosen because:
- Periods up to 5 provide good coverage of common repeating patterns
- Prevents excessive computation for very long periods
- Sufficient for most practical periodic pattern detection
- Balances detection capability with computational efficiency

Reasoning: Periodic patterns in practical scenarios typically have
relatively short periods, making longer periods unnecessary.
"""

# =============================================================================
# POLYNOMIAL FITTING PARAMETERS
# =============================================================================

# Polynomial Detection Parameters
# -------------------------------

MAX_POLYNOMIAL_DEGREE_DEFAULT = 3
"""
Default maximum polynomial degree to check in pattern detection.

Chosen because:
- Cubic polynomials (degree 3) capture most practical patterns
- Higher degrees risk overfitting and reduced interpretability
- Computational complexity increases with degree
- Good balance between pattern detection capability and overfitting risk

Reasoning: Polynomial fitting should detect complex patterns without
risking overfitting to noise in the data.
"""

POLYNOMIAL_R_SQUARED_THRESHOLD = 0.95
"""
R-squared threshold for good polynomial fit.

Chosen because:
- 0.95 indicates very good fit between polynomial and data
- High threshold prevents overfitting to noisy data
- Ensures polynomial model explains most data variance
- Standard threshold for good statistical fit

Reasoning: Polynomial patterns should explain most of the data variance
to be considered valid patterns, preventing false positives.
"""

POLYNOMIAL_COEFFICIENT_TOLERANCE = 1e-6
"""
Tolerance for polynomial coefficient matching to perfect patterns.

Chosen because:
- 1e-6 allows for floating-point precision errors in coefficient calculation
- Tight enough to detect exact polynomial patterns (like squares, cubes)
- Loose enough to account for numerical computation errors
- Standard tolerance for coefficient comparison

Reasoning: Perfect polynomial patterns (like n², n³) should be detected
even with small numerical errors in coefficient calculation.
"""

# =============================================================================
# ALTERNATING PATTERN PARAMETERS
# =============================================================================

# Alternating Pattern Detection
# -----------------------------

ALTERNATING_PATTERN_MIN_DIFFS = 4
"""
Minimum number of differences for alternating pattern detection.

Chosen because:
- 4 differences provide at least 2 full cycles of alternating pattern
- Ensures sufficient data to establish alternating pattern
- Prevents false positives from insufficient alternating data
- Balance between sensitivity and reliability

Reasoning: Alternating patterns need multiple cycles to establish
the alternating relationship reliably.
"""

ALTERNATING_TOLERANCE = 0.1
"""
Tolerance for alternating pattern consistency checking.

Chosen because:
- 10% variance allows for reasonable noise in alternating patterns
- Tight enough to detect genuine alternating patterns
- Loose enough to accommodate imperfect real-world data
- Appropriate for pattern variance tolerance

Reasoning: Alternating patterns in real data may have variance,
requiring tolerance for noise while maintaining pattern detection.
"""

ALTERNATING_CONFIDENCE = 0.8
"""
Confidence score for clear alternating patterns.

Chosen because:
- 0.8 indicates high confidence in detected alternating patterns
- Alternating patterns are relatively reliable when detected
- High but not absolute confidence accounts for potential edge cases
- Reflects the clarity of alternating relationships

Reasoning: Clear alternating patterns provide strong evidence of
underlying regular behavior, warranting high confidence.
"""

PERIODIC_PATTERN_CONFIDENCE = 0.85
"""
Confidence score for detected periodic patterns.

Chosen because:
- 0.85 indicates very high confidence in periodic patterns
- Periodic patterns are highly regular and predictable
- Higher confidence than alternating patterns due to strict periodicity
- Reflects the reliability of detected periodic behavior

Reasoning: Periodic patterns show strong regularity and predictability,
justifying very high confidence when detected.
"""

# =============================================================================
# MISCENALLEOUS CONSTANTS
# =============================================================================

# Input Validation Constants
# --------------------------

MIN_KEYWORD_LENGTH = 3
"""
Minimum length for words to be considered as keywords.

Chosen because:
- Words shorter than 3 characters are often common articles or prepositions
- 3+ characters tend to be meaningful content words
- Prevents inclusion of non-informative short words
- Standard threshold for meaningful word identification

Reasoning: Keyword extraction should focus on meaningful words
rather than short function words that carry little semantic content.
"""

# Regular Expression Constants
# -----------------------------

REGEX_WORD_CHAR_MAX = 30
"""
Maximum word characters in regex patterns to prevent ReDoS.

Chosen because:
- 30 characters accommodates most technical terms and identifiers
- Prevents ReDoS attacks from extremely long word patterns
- Maintains regex performance while being comprehensive
- Reasonable limit for word matching in text processing

Reasoning: Regex patterns should handle typical word lengths without
vulnerability to ReDoS attacks from extremely long inputs.
"""

REGEX_SPACING_MAX = 10
"""
Maximum spacing in regex patterns to prevent ReDoS.

Chosen because:
- 10 spaces accommodates typical formatting variations
- Prevents catastrophic backtracking from excessive spacing
- Maintains regex performance for pattern matching
- Sufficient for most legitimate spacing variations

Reasoning: Regex patterns should handle reasonable spacing without
vulnerability to performance degradation from excessive spacing.
"""

# Cache and Registry Thread Safety
# ---------------------------------

REGISTRY_LOCK_TIMEOUT = None
"""
No timeout for registry operations (blocking locks).

Chosen because:
- Registry operations are typically fast and non-blocking
- Simplicity of implementation without timeout complexity
- Registry operations are critical and should complete rather than fail
- Standard approach for thread-safe registry operations

Reasoning: Registry operations should be atomic and complete successfully
rather than fail due to timeout, given their typically short duration.
"""