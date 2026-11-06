"""
OfferWise Expert System - Test Suite
Comprehensive tests for the inference engine and knowledge base.
"""

import pytest
import sys
from pathlib import Path

# Add src to path — go up one level from tests/ to project root, then into src/
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from knowledge_base import RULES, QUESTIONS, THRESHOLDS, validate_knowledge_base, get_rule_by_id
from inference_engine import InferenceEngine
from analyzer import OfferAnalyzer


class TestKnowledgeBase:
    """Test the knowledge base structure and content."""
    
    def test_exactly_50_rules(self):
        """Verify we have exactly 50 rules."""
        assert len(RULES) == 50, f"Expected 50 rules, found {len(RULES)}"
    
    def test_unique_rule_ids(self):
        """Verify all rule IDs are unique."""
        ids = [rule['id'] for rule in RULES]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"
    
    def test_rule_id_format(self):
        """Verify rule IDs are R01-R50."""
        expected_ids = {f"R{i:02d}" for i in range(1, 51)}
        actual_ids = {rule['id'] for rule in RULES}
        assert actual_ids == expected_ids, f"Rule IDs should be R01-R50"
    
    def test_required_fields_present(self):
        """Verify each rule has all required fields."""
        required_fields = ['id', 'name', 'category', 'conditions', 'conclusion', 
                          'severity', 'explanation', 'recommendation', 'priority']
        
        for rule in RULES:
            for field in required_fields:
                assert field in rule, f"Rule {rule.get('id', 'UNKNOWN')} missing field: {field}"
    
    def test_valid_severities(self):
        """Verify all severities are valid."""
        valid_severities = {'Low', 'Medium', 'High', 'Critical'}
        for rule in RULES:
            assert rule['severity'] in valid_severities, \
                f"Rule {rule['id']} has invalid severity: {rule['severity']}"
    
    def test_valid_priorities(self):
        """Verify priorities are in valid range (1-10)."""
        for rule in RULES:
            assert 1 <= rule['priority'] <= 10, \
                f"Rule {rule['id']} has invalid priority: {rule['priority']}"
    
    def test_categories_correct(self):
        """Verify all rules belong to one of the 5 categories."""
        valid_categories = {
            'Compensation',
            'Career Growth',
            'Workload and Conditions',
            'Legitimacy Red Flags',
            'Overall Verdict'
        }
        
        for rule in RULES:
            assert rule['category'] in valid_categories, \
                f"Rule {rule['id']} has invalid category: {rule['category']}"
    
    def test_ten_rules_per_category(self):
        """Verify there are exactly 10 rules in each of the 5 categories."""
        categories = [
            'Compensation',
            'Career Growth',
            'Workload and Conditions',
            'Legitimacy Red Flags',
            'Overall Verdict'
        ]
        
        for category in categories:
            count = sum(1 for rule in RULES if rule['category'] == category)
            assert count == 10, f"Category '{category}' has {count} rules, expected 10"
    
    def test_validation_passes(self):
        """Test that knowledge base validation passes."""
        is_valid, errors = validate_knowledge_base()
        assert is_valid, f"Knowledge base validation failed: {errors}"


class TestInferenceEngine:
    """Test the inference engine logic."""
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly."""
        engine = InferenceEngine(RULES)
        assert engine is not None
        assert len(engine.rules) == 50
    
    def test_simple_rule_firing(self):
        """Test that a simple rule can fire."""
        # Create a simple test rule
        test_rules = [{
            'id': 'T1',
            'name': 'Test Rule',
            'category': 'Test',
            'conditions': {'fact': 'test_fact', 'operator': 'equals', 'value': 'yes'},
            'conclusion': {'fact': 'result', 'value': 'success'},
            'severity': 'Low',
            'explanation': 'Test',
            'recommendation': 'Test',
            'priority': 5
        }]
        
        engine = InferenceEngine(test_rules)
        result = engine.run({'test_fact': 'yes'})
        
        assert len(result['fired_rules']) == 1
        assert result['working_memory']['result'] == 'success'
    
    def test_forward_chaining_with_derived_facts(self):
        """Test that derived facts trigger second-level rules."""
        # Rule 1 derives a fact, Rule 2 uses that derived fact
        test_rules = [
            {
                'id': 'T1',
                'name': 'Derive Fact',
                'category': 'Test',
                'conditions': {'fact': 'x', 'operator': 'greaterThan', 'value': 5},
                'conclusion': {'fact': 'x_high', 'value': True},
                'severity': 'Low',
                'explanation': 'X is high',
                'recommendation': 'Test',
                'priority': 5
            },
            {
                'id': 'T2',
                'name': 'Use Derived Fact',
                'category': 'Test',
                'conditions': {'fact': 'x_high', 'operator': 'equals', 'value': True},
                'conclusion': {'fact': 'final_result', 'value': 'cascade_success'},
                'severity': 'Low',
                'explanation': 'Used derived fact',
                'recommendation': 'Test',
                'priority': 5
            }
        ]
        
        engine = InferenceEngine(test_rules)
        result = engine.run({'x': 10})
        
        assert len(result['fired_rules']) == 2
        assert result['working_memory']['x_high'] == True
        assert result['working_memory']['final_result'] == 'cascade_success'
    
    def test_unknown_facts_dont_trigger_rules(self):
        """Test that unknown/missing facts don't trigger rules."""
        test_rules = [{
            'id': 'T1',
            'name': 'Should Not Fire',
            'category': 'Test',
            'conditions': {'fact': 'unknown_fact', 'operator': 'equals', 'value': 'yes'},
            'conclusion': {'fact': 'result', 'value': 'bad'},
            'severity': 'Low',
            'explanation': 'Test',
            'recommendation': 'Test',
            'priority': 5
        }]
        
        engine = InferenceEngine(test_rules)
        result = engine.run({'some_other_fact': 'value'})
        
        assert len(result['fired_rules']) == 0
        assert 'result' not in result['working_memory']
    
    def test_not_sure_is_unknown(self):
        """Test that 'Not sure' answers don't trigger rules."""
        test_rules = [{
            'id': 'T1',
            'name': 'Should Not Fire',
            'category': 'Test',
            'conditions': {'fact': 'answer', 'operator': 'equals', 'value': 'Yes'},
            'conclusion': {'fact': 'result', 'value': 'fired'},
            'severity': 'Low',
            'explanation': 'Test',
            'recommendation': 'Test',
            'priority': 5
        }]
        
        engine = InferenceEngine(test_rules)
        result = engine.run({'answer': 'Not sure'})
        
        # 'Not sure' should be filtered out, so rule shouldn't fire
        assert len(result['fired_rules']) == 0
    
    def test_conflict_resolution_deterministic(self):
        """Test that conflict resolution is deterministic."""
        # Two rules that could both fire - higher priority should win
        test_rules = [
            {
                'id': 'T1',
                'name': 'Low Priority',
                'category': 'Test',
                'conditions': {'fact': 'x', 'operator': 'equals', 'value': 10},
                'conclusion': {'fact': 'result', 'value': 'low'},
                'severity': 'Low',
                'explanation': 'Low priority',
                'recommendation': 'Test',
                'priority': 3
            },
            {
                'id': 'T2',
                'name': 'High Priority',
                'category': 'Test',
                'conditions': {'fact': 'x', 'operator': 'equals', 'value': 10},
                'conclusion': {'fact': 'result', 'value': 'high'},
                'severity': 'Low',
                'explanation': 'High priority',
                'recommendation': 'Test',
                'priority': 8
            }
        ]
        
        engine = InferenceEngine(test_rules)
        result1 = engine.run({'x': 10})
        
        # Run again - should get same result
        engine2 = InferenceEngine(test_rules)
        result2 = engine2.run({'x': 10})
        
        # Both should fire high priority rule first
        assert result1['fired_rules'][0]['rule_id'] == result2['fired_rules'][0]['rule_id']
        assert result1['fired_rules'][0]['rule_id'] == 'T2'
    
    def test_no_infinite_loops(self):
        """Test that forward chaining terminates."""
        # Each rule fires at most once, preventing infinite loops
        engine = InferenceEngine(RULES)
        
        # Create facts that might trigger many rules
        facts = {
            'employment_type': 'Internship',
            'monthly_pay': 0,
            'weekly_hours': 45,
            'upfront_payment': 'Yes'
        }
        
        result = engine.run(facts)
        
        # Should terminate without hitting max iterations
        assert result['iterations'] < 100


class TestRulesCanBTriggered:
    """Test that each rule can actually be triggered."""
    
    def test_compensation_rules_triggerable(self):
        """Test rules R01-R10 can be triggered."""
        engine = InferenceEngine(RULES)
        
        # Test R01: Unpaid full-time work
        result = engine.run({'monthly_pay': 0, 'weekly_hours': 40})
        fired_ids = [r['rule_id'] for r in result['fired_rules']]
        assert 'R01' in fired_ids
        
        # Test R03: Good internship compensation
        result = engine.run({'employment_type': 'Internship', 'monthly_pay': 35000})
        fired_ids = [r['rule_id'] for r in result['fired_rules']]
        assert 'R03' in fired_ids
    
    def test_career_growth_rules_triggerable(self):
        """Test rules R11-R20 can be triggered."""
        engine = InferenceEngine(RULES)
        
        # Test R11: Significant learning with mentorship
        result = engine.run({
            'learning_opportunity': 'Yes - significant',
            'mentorship': 'Yes - dedicated mentor'
        })
        fired_ids = [r['rule_id'] for r in result['fired_rules']]
        assert 'R11' in fired_ids
    
    def test_workload_rules_triggerable(self):
        """Test rules R21-R30 can be triggered."""
        engine = InferenceEngine(RULES)
        
        # Test R21: Excessive working hours
        result = engine.run({'weekly_hours': 60})
        fired_ids = [r['rule_id'] for r in result['fired_rules']]
        assert 'R21' in fired_ids
    
    def test_legitimacy_rules_triggerable(self):
        """Test rules R31-R40 can be triggered."""
        engine = InferenceEngine(RULES)
        
        # Test R31: Upfront payment demanded
        result = engine.run({'upfront_payment': 'Yes'})
        fired_ids = [r['rule_id'] for r in result['fired_rules']]
        assert 'R31' in fired_ids
    
    def test_overall_verdict_rules_triggerable(self):
        """Test rules R41-R50 can be triggered."""
        engine = InferenceEngine(RULES)
        
        # Test R41: Critical scam indicators
        # First trigger a rule that creates the derived fact
        result = engine.run({'upfront_payment': 'Yes'})
        fired_ids = [r['rule_id'] for r in result['fired_rules']]
        assert 'R41' in fired_ids  # Should fire based on derived fact


class TestScenarios:
    """Test realistic scenarios end-to-end."""
    
    def test_unpaid_fulltime_internship(self):
        """Test unpaid full-time internship scenario."""
        facts = {
            'employment_type': 'Internship',
            'monthly_pay': 0,
            'weekly_hours': 40,
            'learning_opportunity': 'No - minimal',
            'written_contract': 'No'
        }
        
        engine = InferenceEngine(RULES)
        result = engine.run(facts)
        analyzer = OfferAnalyzer()
        analysis = analyzer.analyze(result, facts)
        
        # Should be high risk due to exploitation
        assert analysis['verdict'] in ['High Risk', 'Needs Further Investigation']
        assert analysis['critical_issues'] > 0
    
    def test_good_paid_internship(self):
        """Test well-paid internship with mentorship."""
        facts = {
            'employment_type': 'Internship',
            'monthly_pay': 40000,
            'weekly_hours': 35,
            'learning_opportunity': 'Yes - significant',
            'mentorship': 'Yes - dedicated mentor',
            'career_relevance': 'Very relevant',
            'written_contract': 'Yes',
            'paid_on_time': 'Yes',
            'clear_responsibilities': 'Yes - very clear',
            'upfront_payment': 'No',
            'work_mode': 'Hybrid'
        }
        
        engine = InferenceEngine(RULES)
        result = engine.run(facts)
        analyzer = OfferAnalyzer()
        analysis = analyzer.analyze(result, facts)
        
        # Should be positive verdict
        assert analysis['verdict'] in ['Strongly Suitable', 'Suitable With Conditions']
        assert len(analysis['positive_factors']) > 0
    
    def test_scam_with_upfront_payment(self):
        """Test that upfront payment triggers High Risk even with good pay."""
        facts = {
            'employment_type': 'Full-time Job',
            'monthly_pay': 100000,  # High pay
            'weekly_hours': 40,
            'upfront_payment': 'Yes',  # SCAM INDICATOR
            'written_contract': 'No'
        }
        
        engine = InferenceEngine(RULES)
        result = engine.run(facts)
        analyzer = OfferAnalyzer()
        analysis = analyzer.analyze(result, facts)
        
        # Must be High Risk regardless of high pay
        assert analysis['verdict'] == 'High Risk'
        assert analysis['critical_issues'] > 0
    
    def test_no_written_contract(self):
        """Test scenario without written contract."""
        facts = {
            'employment_type': 'Internship',
            'monthly_pay': 25000,
            'written_contract': 'No',
            'weekly_hours': 30
        }
        
        engine = InferenceEngine(RULES)
        result = engine.run(facts)
        analyzer = OfferAnalyzer()
        analysis = analyzer.analyze(result, facts)
        
        # Should have concerns
        assert len(analysis['risk_factors']) > 0
        # Should fire rule about no contract
        fired_rule_names = [r['rule_name'] for r in result['fired_rules']]
        assert any('Contract' in name for name in fired_rule_names)
    
    def test_insufficient_information(self):
        """Test that too many 'Not sure' answers gives Insufficient Information."""
        facts = {
            'employment_type': 'Not sure',
            'monthly_pay': 0,
            'weekly_hours': 0
        }
        
        engine = InferenceEngine(RULES)
        result = engine.run(facts)
        analyzer = OfferAnalyzer()
        analysis = analyzer.analyze(result, facts)
        
        # Should indicate need for more info
        assert analysis['verdict'] in ['Insufficient Information', 'Needs Further Investigation']
    
    def test_whatif_changes_verdict(self):
        """Test that changing key parameters changes the verdict."""
        # Start with low pay
        facts1 = {
            'employment_type': 'Internship',
            'monthly_pay': 10000,
            'weekly_hours': 40,
            'written_contract': 'Yes',
            'learning_opportunity': 'Yes - moderate'
        }
        
        engine1 = InferenceEngine(RULES)
        result1 = engine1.run(facts1)
        analyzer1 = OfferAnalyzer()
        analysis1 = analyzer1.analyze(result1, facts1)
        
        # Now with much higher pay
        facts2 = facts1.copy()
        facts2['monthly_pay'] = 50000
        
        engine2 = InferenceEngine(RULES)
        result2 = engine2.run(facts2)
        analyzer2 = OfferAnalyzer()
        analysis2 = analyzer2.analyze(result2, facts2)
        
        # Rules fired should be different
        rules1 = set(r['rule_id'] for r in result1['fired_rules'])
        rules2 = set(r['rule_id'] for r in result2['fired_rules'])
        
        assert rules1 != rules2  # Different rules should fire


class TestAnalyzer:
    """Test the analyzer component."""
    
    def test_analyzer_produces_verdict(self):
        """Test that analyzer produces a valid verdict."""
        engine = InferenceEngine(RULES)
        facts = {
            'employment_type': 'Internship',
            'monthly_pay': 30000,
            'weekly_hours': 35
        }
        
        result = engine.run(facts)
        analyzer = OfferAnalyzer()
        analysis = analyzer.analyze(result, facts)
        
        valid_verdicts = [
            'Strongly Suitable',
            'Suitable With Conditions',
            'Needs Further Investigation',
            'High Risk',
            'Insufficient Information'
        ]
        
        assert analysis['verdict'] in valid_verdicts
    
    def test_analyzer_produces_scores(self):
        """Test that analyzer produces category scores."""
        engine = InferenceEngine(RULES)
        facts = {'employment_type': 'Internship', 'monthly_pay': 30000}
        
        result = engine.run(facts)
        analyzer = OfferAnalyzer()
        analysis = analyzer.analyze(result, facts)
        
        assert 'scores' in analysis
        assert 'Compensation' in analysis['scores']
        assert 'Career Growth' in analysis['scores']
        assert 'Working Conditions' in analysis['scores']
        assert 'Legitimacy' in analysis['scores']
        
        # Scores should be 0-100
        for score in analysis['scores'].values():
            assert 0 <= score <= 100


def test_streamlit_app_no_exceptions():
    """Test that the Streamlit app can run without raising exceptions.
    Uses streamlit.testing.v1.AppTest so we do not trigger the
    'st.set_page_config() can only be called once' restriction."""
    from streamlit.testing.v1 import AppTest
    app_path = str(Path(__file__).parent.parent / 'src' / 'app.py')
    at = AppTest.from_file(app_path)
    at.run(timeout=15)
    # If Streamlit raises an unhandled exception the test fails
    assert not at.exception, f"Streamlit app raised exception: {at.exception}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
