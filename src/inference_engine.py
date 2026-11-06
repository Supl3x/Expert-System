"""
OfferWise Expert System - Inference Engine
Implements forward chaining with conflict resolution and explanation facility.
Does NOT import Streamlit - pure logic layer.
"""

from typing import Dict, List, Any, Set
import copy


class InferenceEngine:
    """
    Forward chaining inference engine with conflict resolution.
    
    The engine:
    1. Takes initial facts (user answers)
    2. Repeatedly finds matching rules
    3. Fires rules to derive new facts
    4. Stops when no new rules can fire
    5. Tracks explanation trace for all fired rules
    """
    
    def __init__(self, rules: List[Dict]):
        """
        Initialize the engine with a rule base.
        
        Args:
            rules: List of rule dictionaries from knowledge_base.py
        """
        self.rules = rules
        self.working_memory = {}  # Current facts: {fact_name: value}
        self.fired_rules = []  # List of rules that have fired: [{rule, matched_facts, order}]
        self.overridden_rules = []  # Rules blocked by conflict resolution
        self.firing_order = 0  # Counter for tracking firing sequence
        
    def run(self, initial_facts: Dict[str, Any]) -> Dict:
        """
        Main forward chaining loop.
        
        Args:
            initial_facts: Dictionary of user-provided facts {fact_name: value}
            
        Returns:
            Dictionary containing:
            - working_memory: All facts (initial + derived)
            - fired_rules: List of fired rule details
            - overridden_rules: Rules that were blocked
            - derivation_trace: Human-readable explanation
        """
        # Initialize working memory with user facts
        # Filter out "Not sure", None, and empty string values - these are UNKNOWN, not facts
        # BUT: Keep 0 for numeric fields like monthly_pay (0 = unpaid, which IS a fact)
        self.working_memory = {}
        for k, v in initial_facts.items():
            if v is None or v == 'Not sure' or v == '':
                continue
            # Keep 0 values - they are meaningful (e.g., unpaid = 0)
            self.working_memory[k] = v
        
        self.fired_rules = []
        self.overridden_rules = []
        self.firing_order = 0
        
        # Track which rules have already fired (prevent infinite loops)
        fired_rule_ids = set()
        
        # Forward chaining loop: keep firing rules until no new rules match
        max_iterations = 100  # Safety limit
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Find all rules that match current facts and haven't fired yet
            matching_rules = []
            for rule in self.rules:
                if rule['id'] not in fired_rule_ids:
                    match_result = self._evaluate_conditions(rule['conditions'])
                    if match_result['matches']:
                        matching_rules.append({
                            'rule': rule,
                            'matched_facts': match_result['matched_facts']
                        })
            
            # If no rules match, we're done
            if not matching_rules:
                break
            
            # CONFLICT RESOLUTION: If multiple rules match, pick the best one
            # Priority: highest priority first, then severity, then rule ID
            selected = self._resolve_conflicts(matching_rules)
            
            # Fire the selected rule
            rule = selected['rule']
            matched_facts = selected['matched_facts']
            
            # Add the conclusion to working memory (derive new fact)
            conclusion = rule['conclusion']
            fact_name = conclusion['fact']
            fact_value = conclusion['value']
            
            # Check for conflicts with existing facts
            if fact_name in self.working_memory:
                existing_value = self.working_memory[fact_name]
                if existing_value != fact_value:
                    # Conflict! The current rule would override existing fact
                    # Record this but let it happen (higher priority wins)
                    conflict_reason = f"Overriding {fact_name}={existing_value} with {fact_value}"
                else:
                    conflict_reason = None
            else:
                conflict_reason = None
            
            # Assert the new fact
            self.working_memory[fact_name] = fact_value
            
            # Record that this rule fired
            self.firing_order += 1
            fired_rule_ids.add(rule['id'])
            
            self.fired_rules.append({
                'rule_id': rule['id'],
                'rule_name': rule['name'],
                'category': rule['category'],
                'severity': rule['severity'],
                'matched_facts': matched_facts,
                'conclusion': conclusion,
                'explanation': rule['explanation'],
                'recommendation': rule['recommendation'],
                'firing_order': self.firing_order,
                'conflict_override': conflict_reason,
                'priority': rule['priority']
            })
        
        # Build human-readable derivation trace
        trace = self._build_explanation_trace()
        
        return {
            'working_memory': self.working_memory,
            'fired_rules': self.fired_rules,
            'overridden_rules': self.overridden_rules,
            'derivation_trace': trace,
            'iterations': iteration
        }
    
    def _evaluate_conditions(self, conditions: Dict) -> Dict:
        """
        Evaluate if conditions match current working memory.
        
        Conditions can be:
        - Single condition: {'fact': 'x', 'operator': 'equals', 'value': 'y'}
        - AND: {'AND': [condition1, condition2, ...]}
        - OR: {'OR': [condition1, condition2, ...]}
        - NOT: {'NOT': condition}
        
        Returns:
            {'matches': bool, 'matched_facts': dict of facts used}
        """
        matched_facts = {}
        
        # Handle AND logic
        if 'AND' in conditions:
            for condition in conditions['AND']:
                result = self._evaluate_conditions(condition)
                if not result['matches']:
                    return {'matches': False, 'matched_facts': {}}
                matched_facts.update(result['matched_facts'])
            return {'matches': True, 'matched_facts': matched_facts}
        
        # Handle OR logic
        if 'OR' in conditions:
            for condition in conditions['OR']:
                result = self._evaluate_conditions(condition)
                if result['matches']:
                    matched_facts.update(result['matched_facts'])
                    return {'matches': True, 'matched_facts': matched_facts}
            return {'matches': False, 'matched_facts': {}}
        
        # Handle NOT logic
        if 'NOT' in conditions:
            result = self._evaluate_conditions(conditions['NOT'])
            # NOT inverts the match but still records what was checked
            matched_facts.update(result['matched_facts'])
            return {
                'matches': not result['matches'],
                'matched_facts': matched_facts
            }
        
        # Single condition evaluation
        fact_name = conditions['fact']
        operator = conditions['operator']
        expected_value = conditions['value']

        # Special case: negative operators on a fact that is NOT in working memory.
        # 'notIn' or 'notEquals' means "this fact should NOT be a bad value."
        # If the fact is entirely absent (never set), there is no bad value present,
        # so the condition should PASS (True).
        # Example: legitimacy_risk notIn ['scam', ...] when legitimacy_risk was never
        # set means no risk was detected → safe to proceed → condition True.
        if fact_name not in self.working_memory:
            if operator in ('notIn', 'notEquals'):
                return {'matches': True, 'matched_facts': {}}
            # All other operators: missing fact means we cannot satisfy the condition
            return {'matches': False, 'matched_facts': {}}
        
        actual_value = self.working_memory[fact_name]
        matched_facts[fact_name] = actual_value
        
        # Evaluate based on operator
        matches = self._apply_operator(actual_value, operator, expected_value)
        
        return {'matches': matches, 'matched_facts': matched_facts}
    
    def _apply_operator(self, actual: Any, operator: str, expected: Any) -> bool:
        """
        Apply comparison operator.
        
        Supported operators:
        - equals, notEquals
        - greaterThan, greaterThanOrEqual
        - lessThan, lessThanOrEqual
        - in, notIn (for list membership)
        """
        try:
            if operator == 'equals':
                return actual == expected
            elif operator == 'notEquals':
                return actual != expected
            elif operator == 'greaterThan':
                return float(actual) > float(expected)
            elif operator == 'greaterThanOrEqual':
                return float(actual) >= float(expected)
            elif operator == 'lessThan':
                return float(actual) < float(expected)
            elif operator == 'lessThanOrEqual':
                return float(actual) <= float(expected)
            elif operator == 'in':
                # Check if actual is in the expected list
                return actual in expected
            elif operator == 'notIn':
                return actual not in expected
            else:
                # Unknown operator - fail safe
                return False
        except (ValueError, TypeError):
            # Type mismatch or conversion error - condition fails
            return False
    
    def _resolve_conflicts(self, matching_rules: List[Dict]) -> Dict:
        """
        Conflict resolution strategy.
        
        When multiple rules match, select ONE based on:
        1. Priority (higher is better)
        2. Severity (Critical > High > Medium > Low)
        3. Rule ID (alphabetical, for determinism)
        
        This ensures deterministic behavior: same input always produces same output.
        
        Args:
            matching_rules: List of {'rule': rule_dict, 'matched_facts': dict}
            
        Returns:
            The selected rule dictionary
        """
        if len(matching_rules) == 1:
            return matching_rules[0]
        
        # Severity ordering
        severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        
        # Sort by: priority (desc), severity (desc), rule_id (asc)
        def sort_key(item):
            rule = item['rule']
            return (
                -rule['priority'],  # Higher priority first (negate for desc)
                -severity_order.get(rule['severity'], 0),  # Higher severity first
                rule['id']  # Alphabetical for determinism
            )
        
        sorted_rules = sorted(matching_rules, key=sort_key)
        
        # Record rules that were NOT selected (overridden)
        selected = sorted_rules[0]
        for i in range(1, len(sorted_rules)):
            self.overridden_rules.append({
                'rule_id': sorted_rules[i]['rule']['id'],
                'rule_name': sorted_rules[i]['rule']['name'],
                'reason': f"Lower priority than {selected['rule']['id']}",
                'iteration': self.firing_order + 1
            })
        
        return selected
    
    def _build_explanation_trace(self) -> str:
        """
        Build human-readable explanation of what the engine did.
        
        Returns:
            Multi-line string explaining the inference process
        """
        if not self.fired_rules:
            return "No rules were triggered. Insufficient information to make assessment."
        
        lines = [
            "INFERENCE ENGINE TRACE",
            "=" * 50,
            f"Total rules fired: {len(self.fired_rules)}",
            f"Total iterations: {self.firing_order}",
            ""
        ]
        
        # Group by firing order
        for fired in sorted(self.fired_rules, key=lambda x: x['firing_order']):
            lines.append(f"[{fired['firing_order']}] Rule {fired['rule_id']}: {fired['rule_name']}")
            lines.append(f"    Category: {fired['category']}")
            lines.append(f"    Severity: {fired['severity']}")
            lines.append(f"    Matched facts: {fired['matched_facts']}")
            lines.append(f"    Conclusion: {fired['conclusion']}")
            if fired['conflict_override']:
                lines.append(f"    ⚠ {fired['conflict_override']}")
            lines.append("")
        
        if self.overridden_rules:
            lines.append("OVERRIDDEN RULES (not fired due to conflict resolution):")
            for overridden in self.overridden_rules:
                lines.append(f"  - {overridden['rule_id']}: {overridden['rule_name']}")
                lines.append(f"    Reason: {overridden['reason']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_unknown_facts(self, all_questions: List[Dict]) -> List[str]:
        """
        Identify which questions were not answered (remain unknown).
        
        Args:
            all_questions: List of question dictionaries
            
        Returns:
            List of question texts that were not answered
        """
        unknown = []
        for question in all_questions:
            fact_id = question['id']
            if fact_id not in self.working_memory:
                unknown.append(question['text'])
        return unknown


def test_inference_engine():
    """
    Simple test to verify the engine works.
    Run this file directly to test: python inference_engine.py
    """
    # Simple test rules
    test_rules = [
        {
            'id': 'T1',
            'name': 'Test Rule 1',
            'category': 'Test',
            'conditions': {'fact': 'x', 'operator': 'greaterThan', 'value': 5},
            'conclusion': {'fact': 'derived_x', 'value': 'high'},
            'severity': 'Low',
            'explanation': 'X is high',
            'recommendation': 'Test',
            'priority': 5
        },
        {
            'id': 'T2',
            'name': 'Test Rule 2',
            'category': 'Test',
            'conditions': {'fact': 'derived_x', 'operator': 'equals', 'value': 'high'},
            'conclusion': {'fact': 'final', 'value': 'success'},
            'severity': 'Low',
            'explanation': 'Derived fact triggered',
            'recommendation': 'Test',
            'priority': 5
        }
    ]
    
    engine = InferenceEngine(test_rules)
    result = engine.run({'x': 10})
    
    print("Test Results:")
    print(f"Working memory: {result['working_memory']}")
    print(f"Fired rules: {[r['rule_id'] for r in result['fired_rules']]}")
    print(f"Expected: derived_x=high, final=success")
    print(f"Success: {result['working_memory'].get('final') == 'success'}")


if __name__ == '__main__':
    test_inference_engine()
