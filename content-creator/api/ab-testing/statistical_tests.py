"""
Statistical Analysis Module

Performs statistical significance testing on A/B test results.
Implements various statistical tests and confidence interval calculations.
"""

import math
import numpy as np
from scipy import stats
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StatisticalTest(Enum):
    """Types of statistical tests for A/B testing."""
    CHI_SQUARE = "chi_square"
    T_TEST = "t_test"
    Z_TEST = "z_test"
    MANN_WHITNEY_U = "mann_whitney_u"
    KOLMOGOROV_SMIRNOV = "kolmogorov_smirnov"
    BAYESIAN = "bayesian"

class SignificanceLevel(Enum):
    """Common significance levels for statistical tests."""
    P001 = 0.001  # 99.9% confidence
    P01 = 0.01    # 99% confidence
    P05 = 0.05    # 95% confidence
    P10 = 0.10    # 90% confidence

@dataclass
class StatisticalResult:
    """Results of a statistical test."""
    test_type: str
    p_value: float
    significance_level: float
    is_significant: bool
    confidence_interval: Optional[Tuple[float, float]] = None
    effect_size: Optional[float] = None
    power: Optional[float] = None
    sample_size_a: int = 0
    sample_size_b: int = 0
    statistic: Optional[float] = None
    degrees_of_freedom: Optional[int] = None

class StatisticalAnalyzer:
    """Performs statistical analysis on A/B test results."""
    
    def __init__(self, default_significance_level: SignificanceLevel = SignificanceLevel.P05):
        """Initialize the statistical analyzer."""
        self.default_significance_level = default_significance_level
        self.test_results_history: List[StatisticalResult] = []
    
    def analyze_ab_test(
        self,
        group_a_data: List[float],
        group_b_data: List[float],
        test_type: StatisticalTest = StatisticalTest.T_TEST,
        significance_level: Optional[SignificanceLevel] = None,
        alpha: Optional[float] = None
    ) -> StatisticalResult:
        """Analyze A/B test results using specified statistical test."""
        
        if not group_a_data or not group_b_data:
            raise ValueError("Both groups must have data")
        
        if len(group_a_data) < 2 or len(group_b_data) < 2:
            raise ValueError("Each group must have at least 2 data points")
        
        # Determine significance level
        if alpha is not None:
            sig_level = alpha
        elif significance_level:
            sig_level = significance_level.value
        else:
            sig_level = self.default_significance_level.value
        
        # Choose appropriate test
        if test_type == StatisticalTest.T_TEST:
            result = self._t_test(group_a_data, group_b_data, sig_level)
        elif test_type == StatisticalTest.Z_TEST:
            result = self._z_test(group_a_data, group_b_data, sig_level)
        elif test_type == StatisticalTest.CHI_SQUARE:
            result = self._chi_square_test(group_a_data, group_b_data, sig_level)
        elif test_type == StatisticalTest.MANN_WHITNEY_U:
            result = self._mann_whitney_u_test(group_a_data, group_b_data, sig_level)
        elif test_type == StatisticalTest.KOLMOGOROV_SMIRNOV:
            result = self._kolmogorov_smirnov_test(group_a_data, group_b_data, sig_level)
        elif test_type == StatisticalTest.BAYESIAN:
            result = self._bayesian_analysis(group_a_data, group_b_data, sig_level)
        else:
            raise ValueError(f"Unsupported test type: {test_type}")
        
        # Store result in history
        self.test_results_history.append(result)
        
        return result
    
    def _t_test(self, group_a: List[float], group_b: List[float], alpha: float) -> StatisticalResult:
        """Perform independent samples t-test."""
        # Calculate t-test
        t_stat, p_value = stats.ttest_ind(group_a, group_b)
        
        # Calculate confidence interval
        pooled_std = math.sqrt(((len(group_a) - 1) * np.var(group_a, ddof=1) + 
                               (len(group_b) - 1) * np.var(group_b, ddof=1)) / 
                              (len(group_a) + len(group_b) - 2))
        
        se = pooled_std * math.sqrt(1/len(group_a) + 1/len(group_b))
        mean_diff = np.mean(group_a) - np.mean(group_b)
        t_critical = stats.t.ppf(1 - alpha/2, len(group_a) + len(group_b) - 2)
        ci_lower = mean_diff - t_critical * se
        ci_upper = mean_diff + t_critical * se
        
        # Calculate effect size (Cohen's d)
        pooled_variance = ((len(group_a) - 1) * np.var(group_a, ddof=1) + 
                          (len(group_b) - 1) * np.var(group_b, ddof=1)) / (len(group_a) + len(group_b) - 2)
        cohens_d = (np.mean(group_a) - np.mean(group_b)) / math.sqrt(pooled_variance)
        
        # Calculate statistical power
        effect_size = abs(cohens_d)
        n1, n2 = len(group_a), len(group_b)
        power = self._calculate_power(effect_size, n1, n2, alpha)
        
        return StatisticalResult(
            test_type="t_test",
            p_value=p_value,
            significance_level=alpha,
            is_significant=p_value < alpha,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=cohens_d,
            power=power,
            sample_size_a=len(group_a),
            sample_size_b=len(group_b),
            statistic=t_stat,
            degrees_of_freedom=len(group_a) + len(group_b) - 2
        )
    
    def _z_test(self, group_a: List[float], group_b: List[float], alpha: float) -> StatisticalResult:
        """Perform Z-test for large samples."""
        # Calculate means and standard deviations
        mean_a = np.mean(group_a)
        mean_b = np.mean(group_b)
        std_a = np.std(group_a, ddof=1)
        std_b = np.std(group_b, ddof=1)
        
        # Calculate pooled standard error
        se = math.sqrt((std_a**2 / len(group_a)) + (std_b**2 / len(group_b)))
        
        # Calculate Z-statistic
        z_stat = (mean_a - mean_b) / se if se != 0 else 0
        
        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        # Calculate confidence interval
        z_critical = stats.norm.ppf(1 - alpha/2)
        ci_lower = (mean_a - mean_b) - z_critical * se
        ci_upper = (mean_a - mean_b) + z_critical * se
        
        # Calculate effect size (Cohen's d)
        pooled_std = math.sqrt(((len(group_a) - 1) * std_a**2 + (len(group_b) - 1) * std_b**2) / 
                              (len(group_a) + len(group_b) - 2))
        cohens_d = (mean_a - mean_b) / pooled_std if pooled_std != 0 else 0
        
        # Calculate statistical power
        effect_size = abs(cohens_d)
        n1, n2 = len(group_a), len(group_b)
        power = self._calculate_power(effect_size, n1, n2, alpha)
        
        return StatisticalResult(
            test_type="z_test",
            p_value=p_value,
            significance_level=alpha,
            is_significant=p_value < alpha,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=cohens_d,
            power=power,
            sample_size_a=len(group_a),
            sample_size_b=len(group_b),
            statistic=z_stat
        )
    
    def _chi_square_test(self, group_a: List[float], group_b: List[float], alpha: float) -> StatisticalResult:
        """Perform Chi-square test on categorical data."""
        # Convert continuous data to categorical (success/failure)
        threshold_a = np.median(group_a)
        threshold_b = np.median(group_b)
        
        success_a = sum(1 for x in group_a if x >= threshold_a)
        failure_a = len(group_a) - success_a
        success_b = sum(1 for x in group_b if x >= threshold_b)
        failure_b = len(group_b) - success_b
        
        # Create contingency table
        contingency_table = np.array([[success_a, failure_a], [success_b, failure_b]])
        
        # Perform Chi-square test
        chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        # Calculate effect size (Cramér's V)
        n = np.sum(contingency_table)
        cramers_v = math.sqrt(chi2_stat / (n * (min(contingency_table.shape) - 1)))
        
        return StatisticalResult(
            test_type="chi_square",
            p_value=p_value,
            significance_level=alpha,
            is_significant=p_value < alpha,
            effect_size=cramers_v,
            sample_size_a=len(group_a),
            sample_size_b=len(group_b),
            statistic=chi2_stat,
            degrees_of_freedom=dof
        )
    
    def _mann_whitney_u_test(self, group_a: List[float], group_b: List[float], alpha: float) -> StatisticalResult:
        """Perform Mann-Whitney U test (non-parametric)."""
        # Perform Mann-Whitney U test
        u_stat, p_value = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
        
        # Calculate effect size (rank-biserial correlation)
        n1, n2 = len(group_a), len(group_b)
        effect_size = 1 - (2 * u_stat) / (n1 * n2)
        
        return StatisticalResult(
            test_type="mann_whitney_u",
            p_value=p_value,
            significance_level=alpha,
            is_significant=p_value < alpha,
            effect_size=effect_size,
            sample_size_a=n1,
            sample_size_b=n2,
            statistic=u_stat
        )
    
    def _kolmogorov_smirnov_test(self, group_a: List[float], group_b: List[float], alpha: float) -> StatisticalResult:
        """Perform Kolmogorov-Smirnov test."""
        # Perform K-S test
        ks_stat, p_value = stats.ks_2samp(group_a, group_b)
        
        # Calculate effect size (based on KS statistic)
        effect_size = ks_stat
        
        return StatisticalResult(
            test_type="kolmogorov_smirnov",
            p_value=p_value,
            significance_level=alpha,
            is_significant=p_value < alpha,
            effect_size=effect_size,
            sample_size_a=len(group_a),
            sample_size_b=len(group_b),
            statistic=ks_stat
        )
    
    def _bayesian_analysis(self, group_a: List[float], group_b: List[float], alpha: float) -> Dict[str, Any]:
        """Perform Bayesian analysis for A/B testing."""
        # Bayesian A/B testing implementation
        # Using Beta-Binomial conjugate prior for conversion rates
        
        # Convert to success/failure data
        threshold_a = np.median(group_a)
        threshold_b = np.median(group_b)
        
        successes_a = sum(1 for x in group_a if x >= threshold_a)
        trials_a = len(group_a)
        successes_b = sum(1 for x in group_b if x >= threshold_b)
        trials_b = len(group_b)
        
        # Bayesian inference with Beta priors
        alpha_prior = 1  # Uninformative prior
        beta_prior = 1
        
        # Posterior parameters
        alpha_posterior_a = alpha_prior + successes_a
        beta_posterior_a = beta_prior + trials_a - successes_a
        alpha_posterior_b = alpha_prior + successes_b
        beta_posterior_b = beta_prior + trials_b - successes_b
        
        # Calculate probability that B > A
        prob_b_better = stats.beta.cdf(
            stats.beta.rvs(alpha_posterior_b, beta_posterior_b, size=1000),
            alpha_posterior_a, beta_posterior_a
        )
        probability_b_beats_a = np.mean(prob_b_better)
        
        return {
            "test_type": "bayesian",
            "probability_b_beats_a": probability_b_beats_a,
            "credible_interval_a": stats.beta.interval(1-alpha, alpha_posterior_a, beta_posterior_a),
            "credible_interval_b": stats.beta.interval(1-alpha, alpha_posterior_b, beta_posterior_b),
            "is_significant": probability_b_beats_a > (1 - alpha),
            "sample_size_a": trials_a,
            "sample_size_b": trials_b
        }
    
    def _calculate_power(self, effect_size: float, n1: int, n2: int, alpha: float) -> float:
        """Calculate statistical power of a test."""
        # Simplified power calculation
        # In practice, this would use more sophisticated power analysis
        if effect_size < 0.2:
            return 0.1  # Small effect size
        elif effect_size < 0.5:
            return 0.3  # Medium effect size
        elif effect_size < 0.8:
            return 0.7  # Large effect size
        else:
            return 0.9  # Very large effect size
    
    def multiple_comparison_correction(
        self,
        p_values: List[float],
        method: str = "bonferroni"
    ) -> List[float]:
        """Apply multiple comparison correction to p-values."""
        if method == "bonferroni":
            corrected_p_values = [p / len(p_values) for p in p_values]
        elif method == "holm":
            corrected_p_values = self._holm_correction(p_values)
        elif method == "benjamini_hochberg":
            corrected_p_values = self._benjamini_hochberg_correction(p_values)
        else:
            raise ValueError(f"Unsupported correction method: {method}")
        
        return corrected_p_values
    
    def _holm_correction(self, p_values: List[float]) -> List[float]:
        """Apply Holm-Bonferroni correction."""
        p_values_sorted = sorted(enumerate(p_values), key=lambda x: x[1])
        corrected_p_values = [None] * len(p_values)
        
        m = len(p_values)
        
        for i, (original_index, p_value) in enumerate(p_values_sorted):
            correction = (m - i) * p_value
            corrected_p_values[original_index] = min(correction, 1.0)
        
        return corrected_p_values
    
    def _benjamini_hochberg_correction(self, p_values: List[float]) -> List[float]:
        """Apply Benjamini-Hochberg (FDR) correction."""
        m = len(p_values)
        p_values_sorted = sorted(enumerate(p_values), key=lambda x: x[1])
        corrected_p_values = [None] * m
        
        for i, (original_index, p_value) in enumerate(p_values_sorted):
            correction = (m / (i + 1)) * p_value
            corrected_p_values[original_index] = min(correction, 1.0)
        
        # Ensure monotonicity
        corrected_p_values_sorted = sorted(corrected_p_values)
        for i in range(1, m):
            if corrected_p_values_sorted[i] < corrected_p_values_sorted[i-1]:
                corrected_p_values_sorted[i] = corrected_p_values_sorted[i-1]
        
        return corrected_p_values_sorted
    
    def sample_size_calculation(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        alpha: float = 0.05,
        power: float = 0.8
    ) -> int:
        """Calculate required sample size for A/B test."""
        # Calculate effect size (absolute difference)
        effect_size = baseline_rate * minimum_detectable_effect
        
        # Z-scores for alpha and power
        z_alpha = stats.norm.ppf(1 - alpha/2)  # Two-tailed test
        z_beta = stats.norm.ppf(power)
        
        # Required sample size per group
        p1 = baseline_rate
        p2 = baseline_rate + effect_size
        
        n = 2 * ((z_alpha * math.sqrt(2 * p1 * (1 - p1)) + 
                  z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2) / (effect_size**2)
        
        return int(math.ceil(n))
    
    def sequential_test_analysis(self, data_points: List[Tuple[str, float]]) -> List[StatisticalResult]:
        """Perform sequential analysis as data comes in."""
        results = []
        
        # Sort data by time
        data_points.sort(key=lambda x: x[0])  # Assuming first element is timestamp
        
        group_a_data = []
        group_b_data = []
        
        # Process data points sequentially
        for timestamp, value in data_points:
            # Determine which group this data point belongs to
            # This is a simplified implementation
            if len(group_a_data) <= len(group_b_data):
                group_a_data.append(value)
            else:
                group_b_data.append(value)
            
            # Perform statistical test if we have enough data
            if len(group_a_data) >= 10 and len(group_b_data) >= 10:
                try:
                    result = self.analyze_ab_test(
                        group_a_data[-50:],  # Use last 50 points
                        group_b_data[-50:],
                        test_type=StatisticalTest.T_TEST
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Sequential test failed: {e}")
        
        return results
    
    def get_test_recommendations(self, result: StatisticalResult) -> List[str]:
        """Get recommendations based on test results."""
        recommendations = []
        
        if result.is_significant:
            recommendations.append("Results are statistically significant.")
            
            if result.effect_size:
                if abs(result.effect_size) < 0.2:
                    recommendations.append("Effect size is small - practical significance may be limited.")
                elif abs(result.effect_size) > 0.5:
                    recommendations.append("Large effect size detected - implementation recommended.")
                else:
                    recommendations.append("Medium effect size - consider business context.")
        else:
            recommendations.append("Results are not statistically significant.")
            
            if result.sample_size_a + result.sample_size_b < 100:
                recommendations.append("Consider increasing sample size.")
        
        if result.power and result.power < 0.8:
            recommendations.append("Statistical power is low - consider longer testing period.")
        
        if result.p_value < 0.001:
            recommendations.append("Very strong evidence of difference.")
        elif result.p_value < 0.01:
            recommendations.append("Strong evidence of difference.")
        elif result.p_value < 0.05:
            recommendations.append("Moderate evidence of difference.")
        
        return recommendations
    
    def export_analysis_report(self, results: List[StatisticalResult]) -> Dict[str, Any]:
        """Export comprehensive analysis report."""
        report = {
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(results),
                "significant_tests": sum(1 for r in results if r.is_significant),
                "average_effect_size": np.mean([r.effect_size for r in results if r.effect_size]) if any(r.effect_size for r in results) else 0,
                "min_p_value": min(r.p_value for r in results),
                "max_p_value": max(r.p_value for r in results)
            },
            "test_details": []
        }
        
        for result in results:
            test_detail = {
                "test_type": result.test_type,
                "p_value": result.p_value,
                "is_significant": result.is_significant,
                "effect_size": result.effect_size,
                "sample_sizes": {
                    "group_a": result.sample_size_a,
                    "group_b": result.sample_size_b
                },
                "confidence_interval": result.confidence_interval,
                "recommendations": self.get_test_recommendations(result)
            }
            
            report["test_details"].append(test_detail)
        
        return report
