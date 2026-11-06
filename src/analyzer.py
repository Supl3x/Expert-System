"""
OfferWise Expert System - Analyzer and Decision Support
Converts fired rules into category scores, final verdict, and actionable recommendations.
"""

from typing import Dict, List, Any


class OfferAnalyzer:
    """
    Analyzes fired rules to produce:
    - Category scores (Compensation, Career Growth, Working Conditions, Legitimacy)
    - Final verdict with explanation
    - Positive factors and risk factors
    - Recommended actions
    - Questions to ask employer
    """
    
    def __init__(self):
        """Initialize the analyzer with scoring weights."""
        # Weights for calculating category scores based on severity
        # These determine how much each severity level contributes to the score
        self.severity_weights = {
            'Critical': -40,  # Major negative impact
            'High': -20,      # Significant negative impact
            'Medium': -10,    # Moderate negative impact
            'Low': +5         # Small positive impact
        }
        
        # Base score for each category (neutral starting point)
        self.base_score = 50
        
    def analyze(self, inference_result: Dict, initial_facts: Dict) -> Dict:
        """
        Main analysis function.
        
        Args:
            inference_result: Output from InferenceEngine.run()
            initial_facts: Original user inputs
            
        Returns:
            Dictionary with verdict, scores, factors, recommendations
        """
        fired_rules = inference_result['fired_rules']
        working_memory = inference_result['working_memory']
        
        # Calculate category scores
        scores = self._calculate_category_scores(fired_rules)
        
        # Identify positive and risk factors
        positives = self._extract_positive_factors(fired_rules)
        risks = self._extract_risk_factors(fired_rules)
        
        # Determine final verdict
        verdict = self._determine_verdict(fired_rules, working_memory, initial_facts, scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(fired_rules, risks)
        
        # Generate questions for employer
        questions = self._generate_employer_questions(fired_rules, initial_facts)
        
        # Identify unknown/unanswered facts
        unknown_count = sum(1 for v in initial_facts.values() 
                          if v == 'Not sure' or v is None or v == '')
        
        return {
            'verdict': verdict['decision'],
            'verdict_reason': verdict['reason'],
            'scores': scores,
            'positive_factors': positives,
            'risk_factors': risks,
            'recommendations': recommendations,
            'employer_questions': questions,
            'unknown_count': unknown_count,
            'total_rules_fired': len(fired_rules),
            'critical_issues': len([r for r in fired_rules if r['severity'] == 'Critical'])
        }
    
    def _calculate_category_scores(self, fired_rules: List[Dict]) -> Dict[str, int]:
        """
        Calculate score for each category based on fired rules.
        
        Returns scores from 0-100 for:
        - Compensation
        - Career Growth
        - Working Conditions
        - Legitimacy
        """
        categories = {
            'Compensation': self.base_score,
            'Career Growth': self.base_score,
            'Workload and Conditions': self.base_score,
            'Legitimacy Red Flags': self.base_score
        }
        
        # Count rules per category to avoid double-counting
        category_rule_count = {cat: 0 for cat in categories}
        
        for rule in fired_rules:
            category = rule['category']
            if category in categories:
                # Apply weight based on severity
                weight = self.severity_weights.get(rule['severity'], 0)
                categories[category] += weight
                category_rule_count[category] += 1
        
        # Normalize scores to 0-100 range
        for cat in categories:
            categories[cat] = max(0, min(100, categories[cat]))
        
        # Rename for clearer display
        return {
            'Compensation': categories['Compensation'],
            'Career Growth': categories['Career Growth'],
            'Working Conditions': categories['Workload and Conditions'],
            'Legitimacy': categories['Legitimacy Red Flags']
        }
    
    def _extract_positive_factors(self, fired_rules: List[Dict]) -> List[str]:
        """Extract positive aspects from fired rules."""
        positives = []
        
        for rule in fired_rules:
            # Low severity rules are typically positive indicators
            if rule['severity'] == 'Low':
                # Extract positive explanations
                explanation = rule['explanation']
                if any(word in explanation.lower() for word in 
                      ['good', 'excellent', 'strong', 'competitive', 'positive', 
                       'clear', 'acceptable', 'reasonable', 'fair']):
                    positives.append(f"{rule['rule_name']}: {explanation}")
        
        return positives[:8]  # Limit to top 8 for display
    
    def _extract_risk_factors(self, fired_rules: List[Dict]) -> List[str]:
        """Extract risk factors and concerns from fired rules."""
        risks = []
        
        for rule in fired_rules:
            # High and Critical severity are risks
            if rule['severity'] in ['High', 'Critical']:
                risks.append(f"[{rule['severity']}] {rule['rule_name']}: {rule['explanation']}")
        
        # Sort by severity (Critical first)
        risks.sort(key=lambda x: 0 if 'Critical' in x else 1)
        
        return risks
    
    def _determine_verdict(self, fired_rules: List[Dict], working_memory: Dict, 
                          initial_facts: Dict, scores: Dict) -> Dict:
        """
        Determine the final verdict based on fired rules and scores.
        
        Verdict options:
        - Strongly Suitable
        - Suitable With Conditions
        - Needs Further Investigation
        - High Risk
        - Insufficient Information
        """
        # Check if too many questions were unanswered
        # Count actual distinct answers (not "Not sure", None, or empty)
        answered_count = 0
        for k, v in initial_facts.items():
            if v not in ['Not sure', None, ''] and k != 'commute_time':  # commute_time is conditional
                answered_count += 1
        
        if answered_count < 5:  # Minimum 5 substantive answers needed
            return {
                'decision': 'Insufficient Information',
                'reason': f'Only {answered_count} questions answered. Need more information to make assessment.'
            }
        
        # Check for Critical severity rules - these override everything
        # Look at ALL fired rules' conclusions, not just the final working memory
        critical_rules = [r for r in fired_rules if r['severity'] == 'Critical']
        if critical_rules:
            # Check specifically for scam/exploitation patterns in ANY fired critical rule
            for rule in critical_rules:
                conclusion_value = rule['conclusion'].get('value', '')
                if conclusion_value in ['upfront_fee_scam', 'identity_theft_risk', 'likely_scam', 
                                       'exploitative', 'unpaid_fulltime', 'exploitative_unpaid']:
                    return {
                        'decision': 'High Risk',
                        'reason': 'Critical red flags detected: ' + '; '.join([r['rule_name'] for r in critical_rules[:3]])
                    }
        
        # Check for final_verdict in working memory (from Overall Verdict rules)
        if 'final_verdict' in working_memory:
            verdict = working_memory['final_verdict']
            
            # Find the rule that set this verdict for explanation
            verdict_rule = next((r for r in fired_rules 
                               if r['conclusion'].get('fact') == 'final_verdict'), None)
            
            if verdict_rule:
                return {
                    'decision': verdict,
                    'reason': verdict_rule['explanation']
                }
        
        # Score-based fallback logic
        avg_score = sum(scores.values()) / len(scores)
        high_severity_count = len([r for r in fired_rules if r['severity'] in ['High', 'Critical']])
        
        if high_severity_count >= 3:
            return {
                'decision': 'High Risk',
                'reason': f'Multiple serious concerns detected ({high_severity_count} high-severity issues)'
            }
        elif high_severity_count >= 1:
            return {
                'decision': 'Needs Further Investigation',
                'reason': 'Some concerns identified that require clarification'
            }
        elif avg_score >= 60:
            return {
                'decision': 'Strongly Suitable',
                'reason': 'Strong positive indicators across multiple dimensions'
            }
        elif avg_score >= 45:
            return {
                'decision': 'Suitable With Conditions',
                'reason': 'Generally acceptable with some areas to clarify'
            }
        else:
            return {
                'decision': 'Needs Further Investigation',
                'reason': 'Mixed signals require deeper investigation'
            }
    
    def _generate_recommendations(self, fired_rules: List[Dict], 
                                 risk_factors: List[str]) -> List[str]:
        """Generate actionable recommendations based on fired rules."""
        recommendations = []
        seen_recs = set()  # Avoid duplicates
        
        # Prioritize recommendations from high-severity rules
        sorted_rules = sorted(fired_rules, 
                            key=lambda r: (0 if r['severity'] == 'Critical' else 
                                         1 if r['severity'] == 'High' else 
                                         2 if r['severity'] == 'Medium' else 3))
        
        for rule in sorted_rules:
            rec = rule['recommendation']
            if rec not in seen_recs:
                recommendations.append(rec)
                seen_recs.add(rec)
            
            if len(recommendations) >= 6:
                break
        
        # Add disclaimer if scam indicators present
        if any('scam' in rf.lower() or 'upfront' in rf.lower() for rf in risk_factors):
            recommendations.insert(0, "⚠️ URGENT: Do not proceed with this offer. Report to authorities if payment was requested.")
        
        return recommendations
    
    def _generate_employer_questions(self, fired_rules: List[Dict], 
                                    initial_facts: Dict) -> List[str]:
        """Generate questions user should ask the employer."""
        questions = []
        
        # Check what information is missing or concerning
        if initial_facts.get('written_contract') in ['No', 'Verbal only', 'Not sure']:
            questions.append("When will you provide a written offer letter with all terms?")
        
        if initial_facts.get('clear_responsibilities') in ['Vague', 'Somewhat clear', 'Not sure']:
            questions.append("Can you provide a detailed job description with specific responsibilities?")
        
        if initial_facts.get('paid_on_time') in ['No', 'Not sure']:
            questions.append("What are your payment terms and schedule?")
        
        if initial_facts.get('mentorship') in ['No', 'Not sure']:
            questions.append("What learning and mentorship support will be available?")
        
        if initial_facts.get('fulltime_chance') in ['Not sure'] and initial_facts.get('employment_type') == 'Internship':
            questions.append("Is there a possibility of full-time employment after the internship?")
        
        # Add questions based on fired rules
        for rule in fired_rules:
            if rule['severity'] in ['High', 'Critical']:
                if 'payment' in rule['rule_name'].lower():
                    if "What are your payment terms" not in ' '.join(questions):
                        questions.append("Can you guarantee payment terms in writing?")
                
                if 'contract' in rule['rule_name'].lower():
                    if "offer letter" not in ' '.join(questions):
                        questions.append("Why is there no written contract?")
        
        return questions[:6]  # Limit to 6 questions


def test_analyzer():
    """Test the analyzer with sample data."""
    # Sample inference result
    sample_result = {
        'fired_rules': [
            {
                'rule_id': 'R03',
                'rule_name': 'Good Internship Compensation',
                'category': 'Compensation',
                'severity': 'Low',
                'explanation': 'Pay is good for internship',
                'recommendation': 'Compensation is fair',
                'conclusion': {'fact': 'compensation_score', 'value': 'good'},
                'matched_facts': {'monthly_pay': 35000},
                'firing_order': 1,
                'conflict_override': None,
                'priority': 5
            }
        ],
        'working_memory': {'monthly_pay': 35000, 'compensation_score': 'good'}
    }
    
    sample_facts = {
        'employment_type': 'Internship',
        'monthly_pay': 35000,
        'written_contract': 'Yes'
    }
    
    analyzer = OfferAnalyzer()
    result = analyzer.analyze(sample_result, sample_facts)
    
    print("Analyzer Test:")
    print(f"Verdict: {result['verdict']}")
    print(f"Scores: {result['scores']}")
    print(f"Success: {result['verdict'] in ['Strongly Suitable', 'Suitable With Conditions']}")


if __name__ == '__main__':
    test_analyzer()
