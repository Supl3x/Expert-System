"""
OfferWise Expert System - Knowledge Base
Contains all facts (questions) and exactly 50 IF-THEN rules for evaluating job/internship offers.
Rules are organized by category and use forward chaining to derive new facts.
"""

# ============================================================================
# THRESHOLDS - All monetary and numeric thresholds in one place for easy tuning
# ============================================================================
THRESHOLDS = {
    # Compensation thresholds (PKR per month)
    'minimum_fair_pay': 15000,           # Minimum acceptable pay for any work
    'good_internship_pay': 30000,        # Good pay for internship
    'excellent_internship_pay': 50000,   # Excellent internship pay
    'fair_fulltime_pay': 50000,          # Minimum for full-time junior role
    'good_fulltime_pay': 80000,          # Good full-time pay
    
    # Time thresholds
    'reasonable_hours': 40,              # Standard work week
    'overwork_threshold': 50,            # Hours that indicate overwork
    'long_commute_minutes': 90,          # One-way commute that's too long
    
    # Other
    'min_facts_for_verdict': 8,          # Minimum answered questions for verdict
}

# ============================================================================
# QUESTIONS - Facts that the system will gather from the user
# ============================================================================
QUESTIONS = [
    {
        'id': 'employment_type',
        'text': 'What type of opportunity is this?',
        'type': 'select',
        'options': ['Internship', 'Full-time Job', 'Contract/Freelance', 'Not sure'],
        'help': 'Select the employment type being offered'
    },
    {
        'id': 'work_mode',
        'text': 'What is the work mode?',
        'type': 'select',
        'options': ['Remote', 'On-site', 'Hybrid', 'Not sure'],
        'help': 'Where will you be working?'
    },
    {
        'id': 'weekly_hours',
        'text': 'Expected weekly working hours?',
        'type': 'number',
        'min': 0,
        'max': 80,
        'help': 'How many hours per week are expected? (0 if not sure)'
    },
    {
        'id': 'monthly_pay',
        'text': 'Monthly compensation (PKR)?',
        'type': 'number',
        'min': 0,
        'help': 'Enter 0 for unpaid positions'
    },
    {
        'id': 'paid_on_time',
        'text': 'Have they guaranteed timely payment?',
        'type': 'select',
        'options': ['Yes', 'No', 'Not sure'],
        'help': 'Did they commit to paying on time?'
    },
    {
        'id': 'learning_opportunity',
        'text': 'Does this offer real learning opportunities?',
        'type': 'select',
        'options': ['Yes - significant', 'Yes - moderate', 'No - minimal', 'Not sure'],
        'help': 'Will you learn valuable skills?'
    },
    {
        'id': 'mentorship',
        'text': 'Is mentorship or guidance provided?',
        'type': 'select',
        'options': ['Yes - dedicated mentor', 'Yes - team support', 'No', 'Not sure'],
        'help': 'Will someone guide your work?'
    },
    {
        'id': 'career_relevance',
        'text': 'Is this relevant to your career goals?',
        'type': 'select',
        'options': ['Very relevant', 'Somewhat relevant', 'Not relevant', 'Not sure'],
        'help': 'Does this align with your career path?'
    },
    {
        'id': 'fulltime_chance',
        'text': 'Is there a chance of full-time employment after?',
        'type': 'select',
        'options': ['Yes - clearly stated', 'Maybe - hinted at', 'No', 'Not applicable', 'Not sure'],
        'help': 'For internships: conversion possibility?'
    },
    {
        'id': 'commute_time',
        'text': 'One-way commute time (minutes)?',
        'type': 'number',
        'min': 0,
        'max': 300,
        'conditional': True,  # Only shown if work_mode is On-site or Hybrid
        'help': 'Travel time one way (0 if not applicable)'
    },
    {
        'id': 'written_contract',
        'text': 'Is there a written contract or offer letter?',
        'type': 'select',
        'options': ['Yes', 'No', 'Verbal only', 'Not sure'],
        'help': 'Have they provided documentation?'
    },
    {
        'id': 'clear_responsibilities',
        'text': 'Are job responsibilities clearly defined?',
        'type': 'select',
        'options': ['Yes - very clear', 'Somewhat clear', 'Vague', 'Not sure'],
        'help': 'Do you know what you\'ll be doing?'
    },
    {
        'id': 'upfront_payment',
        'text': 'Did they ask for any upfront payment or fee?',
        'type': 'select',
        'options': ['Yes', 'No', 'Not sure'],
        'help': 'Training fees, registration fees, deposits, etc.'
    },
    {
        'id': 'sensitive_docs_early',
        'text': 'Did they ask for CNIC/bank details before offer?',
        'type': 'select',
        'options': ['Yes', 'No', 'Not sure'],
        'help': 'Sensitive documents requested too early in the process'
    },
    {
        'id': 'hiring_pressure',
        'text': 'Are they pressuring you to decide immediately?',
        'type': 'select',
        'options': ['Yes - urgent', 'Somewhat', 'No - reasonable timeline', 'Not sure'],
        'help': 'Are they rushing your decision?'
    },
]

# ============================================================================
# RULES - Exactly 50 IF-THEN rules organized by category
# ============================================================================
# Each rule has:
# - id: Unique identifier (R01-R50)
# - name: Short descriptive name
# - category: One of 5 categories
# - conditions: Dictionary with AND/OR/NOT logic
# - conclusion: Fact to assert (can be derived fact)
# - severity: Low/Medium/High/Critical
# - explanation: Why this rule fired
# - recommendation: What user should do
# - priority: 1-10 (10 = highest, used in conflict resolution)

RULES = [
    # ========================================================================
    # CATEGORY 1: COMPENSATION (Rules R01-R10)
    # ========================================================================
    {
        'id': 'R01',
        'name': 'Unpaid Full-Time Work',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'monthly_pay', 'operator': 'lessThan', 'value': 1000},
                {'fact': 'weekly_hours', 'operator': 'greaterThanOrEqual', 'value': 35}
            ]
        },
        'conclusion': {'fact': 'compensation_risk', 'value': 'unpaid_fulltime'},
        'severity': 'Critical',
        'explanation': 'Working full-time hours without compensation is exploitative.',
        'recommendation': 'Reject this offer. Full-time work must be paid.',
        'priority': 10
    },
    {
        'id': 'R02',
        'name': 'Below Minimum Fair Pay',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'monthly_pay', 'operator': 'greaterThan', 'value': 0},
                {'fact': 'monthly_pay', 'operator': 'lessThan', 'value': THRESHOLDS['minimum_fair_pay']}
            ]
        },
        'conclusion': {'fact': 'compensation_score', 'value': 'very_low'},
        'severity': 'High',
        'explanation': f'Pay is below PKR {THRESHOLDS["minimum_fair_pay"]}/month, which is extremely low.',
        'recommendation': 'Negotiate for higher pay or consider other opportunities.',
        'priority': 8
    },
    {
        'id': 'R03',
        'name': 'Good Internship Compensation',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Internship'},
                {'fact': 'monthly_pay', 'operator': 'greaterThanOrEqual', 'value': THRESHOLDS['good_internship_pay']},
                {'fact': 'monthly_pay', 'operator': 'lessThan', 'value': THRESHOLDS['excellent_internship_pay']}
            ]
        },
        'conclusion': {'fact': 'compensation_score', 'value': 'good'},
        'severity': 'Low',
        'explanation': f'Pay of PKR {THRESHOLDS["good_internship_pay"]}-{THRESHOLDS["excellent_internship_pay"]} is good for an internship.',
        'recommendation': 'Compensation is fair for an internship.',
        'priority': 5
    },
    {
        'id': 'R04',
        'name': 'Excellent Internship Compensation',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Internship'},
                {'fact': 'monthly_pay', 'operator': 'greaterThanOrEqual', 'value': THRESHOLDS['excellent_internship_pay']}
            ]
        },
        'conclusion': {'fact': 'compensation_score', 'value': 'excellent'},
        'severity': 'Low',
        'explanation': f'Pay above PKR {THRESHOLDS["excellent_internship_pay"]} is excellent for an internship.',
        'recommendation': 'Compensation is very competitive.',
        'priority': 6
    },
    {
        'id': 'R05',
        'name': 'Below Fair Full-Time Pay',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Full-time Job'},
                {'fact': 'monthly_pay', 'operator': 'lessThan', 'value': THRESHOLDS['fair_fulltime_pay']}
            ]
        },
        'conclusion': {'fact': 'compensation_score', 'value': 'low_for_fulltime'},
        'severity': 'Medium',
        'explanation': f'Pay below PKR {THRESHOLDS["fair_fulltime_pay"]}/month is low for full-time work.',
        'recommendation': 'Negotiate for market-rate salary.',
        'priority': 7
    },
    {
        'id': 'R06',
        'name': 'Good Full-Time Compensation',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Full-time Job'},
                {'fact': 'monthly_pay', 'operator': 'greaterThanOrEqual', 'value': THRESHOLDS['good_fulltime_pay']}
            ]
        },
        'conclusion': {'fact': 'compensation_score', 'value': 'good_fulltime'},
        'severity': 'Low',
        'explanation': f'Pay above PKR {THRESHOLDS["good_fulltime_pay"]} is competitive for full-time.',
        'recommendation': 'Compensation is strong.',
        'priority': 5
    },
    {
        'id': 'R07',
        'name': 'No Payment Guarantee',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'paid_on_time', 'operator': 'equals', 'value': 'No'},
                {'fact': 'monthly_pay', 'operator': 'greaterThan', 'value': 0}
            ]
        },
        'conclusion': {'fact': 'payment_risk', 'value': 'no_guarantee'},
        'severity': 'High',
        'explanation': 'No guarantee of timely payment is a major red flag.',
        'recommendation': 'Request written payment terms before accepting.',
        'priority': 8
    },
    {
        'id': 'R08',
        'name': 'Unpaid Internship with Learning',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Internship'},
                {'fact': 'monthly_pay', 'operator': 'equals', 'value': 0},
                {'fact': 'learning_opportunity', 'operator': 'in', 'value': ['Yes - significant', 'Yes - moderate']},
                {'fact': 'weekly_hours', 'operator': 'lessThan', 'value': 25}
            ]
        },
        'conclusion': {'fact': 'compensation_acceptable', 'value': 'unpaid_but_learning'},
        'severity': 'Low',
        'explanation': 'Unpaid internship acceptable if part-time with real learning.',
        'recommendation': 'Ensure learning outcomes are clearly defined.',
        'priority': 4
    },
    {
        'id': 'R09',
        'name': 'Exploitative Unpaid Internship',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Internship'},
                {'fact': 'monthly_pay', 'operator': 'equals', 'value': 0},
                {'fact': 'weekly_hours', 'operator': 'greaterThanOrEqual', 'value': 25}
            ]
        },
        'conclusion': {'fact': 'compensation_risk', 'value': 'exploitative_unpaid'},
        'severity': 'Critical',
        'explanation': 'Unpaid work for 25+ hours/week is exploitative.',
        'recommendation': 'Reject. Demand fair compensation for substantial time commitment.',
        'priority': 10
    },
    {
        'id': 'R10',
        'name': 'Fair Pay with Guarantee',
        'category': 'Compensation',
        'conditions': {
            'AND': [
                {'fact': 'monthly_pay', 'operator': 'greaterThanOrEqual', 'value': THRESHOLDS['minimum_fair_pay']},
                {'fact': 'paid_on_time', 'operator': 'equals', 'value': 'Yes'}
            ]
        },
        'conclusion': {'fact': 'compensation_score', 'value': 'reliable'},
        'severity': 'Low',
        'explanation': 'Fair pay with payment guarantee is positive.',
        'recommendation': 'Payment terms appear reliable.',
        'priority': 5
    },
    
    # ========================================================================
    # CATEGORY 2: CAREER GROWTH (Rules R11-R20)
    # ========================================================================
    {
        'id': 'R11',
        'name': 'Significant Learning with Mentorship',
        'category': 'Career Growth',
        'conditions': {
            'AND': [
                {'fact': 'learning_opportunity', 'operator': 'equals', 'value': 'Yes - significant'},
                {'fact': 'mentorship', 'operator': 'in', 'value': ['Yes - dedicated mentor', 'Yes - team support']}
            ]
        },
        'conclusion': {'fact': 'growth_potential', 'value': 'excellent'},
        'severity': 'Low',
        'explanation': 'Strong learning opportunities with mentorship provide excellent growth.',
        'recommendation': 'This is a strong career development opportunity.',
        'priority': 6
    },
    {
        'id': 'R12',
        'name': 'No Learning Opportunity',
        'category': 'Career Growth',
        'conditions': {
            'fact': 'learning_opportunity', 'operator': 'equals', 'value': 'No - minimal'
        },
        'conclusion': {'fact': 'growth_potential', 'value': 'poor'},
        'severity': 'Medium',
        'explanation': 'Minimal learning opportunity limits career growth.',
        'recommendation': 'Consider if compensation justifies lack of skill development.',
        'priority': 6
    },
    {
        'id': 'R13',
        'name': 'Career Relevant Internship',
        'category': 'Career Growth',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Internship'},
                {'fact': 'career_relevance', 'operator': 'equals', 'value': 'Very relevant'}
            ]
        },
        'conclusion': {'fact': 'career_alignment', 'value': 'strong'},
        'severity': 'Low',
        'explanation': 'Internship aligns well with career goals.',
        'recommendation': 'Strong fit for your career path.',
        'priority': 5
    },
    {
        'id': 'R14',
        'name': 'Irrelevant Career Path',
        'category': 'Career Growth',
        'conditions': {
            'fact': 'career_relevance', 'operator': 'equals', 'value': 'Not relevant'
        },
        'conclusion': {'fact': 'career_alignment', 'value': 'poor'},
        'severity': 'Medium',
        'explanation': 'This opportunity does not align with your career goals.',
        'recommendation': 'Consider why you would take this role.',
        'priority': 5
    },
    {
        'id': 'R15',
        'name': 'Clear Conversion Path',
        'category': 'Career Growth',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Internship'},
                {'fact': 'fulltime_chance', 'operator': 'equals', 'value': 'Yes - clearly stated'}
            ]
        },
        'conclusion': {'fact': 'longterm_potential', 'value': 'strong'},
        'severity': 'Low',
        'explanation': 'Clear path to full-time employment adds value.',
        'recommendation': 'Good long-term opportunity.',
        'priority': 6
    },
    {
        'id': 'R16',
        'name': 'No Mentorship',
        'category': 'Career Growth',
        'conditions': {
            'fact': 'mentorship', 'operator': 'equals', 'value': 'No'
        },
        'conclusion': {'fact': 'guidance_risk', 'value': 'no_mentorship'},
        'severity': 'Medium',
        'explanation': 'Lack of mentorship may slow your learning.',
        'recommendation': 'Ask about learning support structures.',
        'priority': 5
    },
    {
        'id': 'R17',
        'name': 'Strong Growth Package',
        'category': 'Career Growth',
        'conditions': {
            'AND': [
                {'fact': 'learning_opportunity', 'operator': 'in', 'value': ['Yes - significant', 'Yes - moderate']},
                {'fact': 'career_relevance', 'operator': 'in', 'value': ['Very relevant', 'Somewhat relevant']},
                {'fact': 'mentorship', 'operator': 'in', 'value': ['Yes - dedicated mentor', 'Yes - team support']}
            ]
        },
        'conclusion': {'fact': 'growth_potential', 'value': 'comprehensive'},
        'severity': 'Low',
        'explanation': 'Combined learning, relevance, and mentorship create strong growth.',
        'recommendation': 'Excellent developmental opportunity.',
        'priority': 7
    },
    {
        'id': 'R18',
        'name': 'Dead-End Internship',
        'category': 'Career Growth',
        'conditions': {
            'AND': [
                {'fact': 'employment_type', 'operator': 'equals', 'value': 'Internship'},
                {'fact': 'fulltime_chance', 'operator': 'equals', 'value': 'No'},
                {'fact': 'learning_opportunity', 'operator': 'equals', 'value': 'No - minimal'}
            ]
        },
        'conclusion': {'fact': 'growth_potential', 'value': 'dead_end'},
        'severity': 'High',
        'explanation': 'No conversion chance and minimal learning make this a dead-end.',
        'recommendation': 'Only accept if compensation is excellent.',
        'priority': 7
    },
    {
        'id': 'R19',
        'name': 'Moderate Growth Potential',
        'category': 'Career Growth',
        'conditions': {
            'AND': [
                {'fact': 'learning_opportunity', 'operator': 'equals', 'value': 'Yes - moderate'},
                {'fact': 'career_relevance', 'operator': 'equals', 'value': 'Somewhat relevant'}
            ]
        },
        'conclusion': {'fact': 'growth_potential', 'value': 'moderate'},
        'severity': 'Low',
        'explanation': 'Moderate learning and relevance provide acceptable growth.',
        'recommendation': 'Reasonable developmental opportunity.',
        'priority': 4
    },
    {
        'id': 'R20',
        'name': 'Mentorship Compensates Low Pay',
        'category': 'Career Growth',
        'conditions': {
            'AND': [
                {'fact': 'compensation_score', 'operator': 'in', 'value': ['very_low', 'low_for_fulltime']},
                {'fact': 'mentorship', 'operator': 'equals', 'value': 'Yes - dedicated mentor'},
                {'fact': 'learning_opportunity', 'operator': 'equals', 'value': 'Yes - significant'}
            ]
        },
        'conclusion': {'fact': 'value_proposition', 'value': 'learning_over_pay'},
        'severity': 'Low',
        'explanation': 'Exceptional learning opportunity may justify lower pay.',
        'recommendation': 'Consider if career growth is worth the pay tradeoff.',
        'priority': 5
    },
    
    # ========================================================================
    # CATEGORY 3: WORKLOAD AND CONDITIONS (Rules R21-R30)
    # ========================================================================
    {
        'id': 'R21',
        'name': 'Excessive Working Hours',
        'category': 'Workload and Conditions',
        'conditions': {
            'fact': 'weekly_hours', 'operator': 'greaterThan', 'value': THRESHOLDS['overwork_threshold']
        },
        'conclusion': {'fact': 'workload_risk', 'value': 'excessive_hours'},
        'severity': 'High',
        'explanation': f'Over {THRESHOLDS["overwork_threshold"]} hours/week indicates overwork.',
        'recommendation': 'Negotiate for reasonable hours or reject.',
        'priority': 8
    },
    {
        'id': 'R22',
        'name': 'Reasonable Work Hours',
        'category': 'Workload and Conditions',
        'conditions': {
            'AND': [
                {'fact': 'weekly_hours', 'operator': 'greaterThan', 'value': 0},
                {'fact': 'weekly_hours', 'operator': 'lessThanOrEqual', 'value': THRESHOLDS['reasonable_hours']}
            ]
        },
        'conclusion': {'fact': 'workload_score', 'value': 'reasonable'},
        'severity': 'Low',
        'explanation': f'Up to {THRESHOLDS["reasonable_hours"]} hours/week is standard.',
        'recommendation': 'Work hours are acceptable.',
        'priority': 4
    },
    {
        'id': 'R23',
        'name': 'Exploitative Workload',
        'category': 'Workload and Conditions',
        'conditions': {
            'AND': [
                {'fact': 'compensation_risk', 'operator': 'equals', 'value': 'unpaid_fulltime'},
                {'fact': 'weekly_hours', 'operator': 'greaterThan', 'value': 40}
            ]
        },
        'conclusion': {'fact': 'workload_risk', 'value': 'exploitative'},
        'severity': 'Critical',
        'explanation': 'Unpaid work exceeding 40 hours is severely exploitative.',
        'recommendation': 'Reject immediately.',
        'priority': 10
    },
    {
        'id': 'R24',
        'name': 'Long Commute Burden',
        'category': 'Workload and Conditions',
        'conditions': {
            'AND': [
                {'fact': 'work_mode', 'operator': 'in', 'value': ['On-site', 'Hybrid']},
                {'fact': 'commute_time', 'operator': 'greaterThan', 'value': THRESHOLDS['long_commute_minutes']}
            ]
        },
        'conclusion': {'fact': 'workload_risk', 'value': 'long_commute'},
        'severity': 'Medium',
        'explanation': f'Commute over {THRESHOLDS["long_commute_minutes"]} minutes each way reduces quality of life.',
        'recommendation': 'Factor in 3+ hours daily commute time and costs.',
        'priority': 6
    },
    {
        'id': 'R25',
        'name': 'Remote Flexibility',
        'category': 'Workload and Conditions',
        'conditions': {
            'fact': 'work_mode', 'operator': 'equals', 'value': 'Remote'
        },
        'conclusion': {'fact': 'flexibility_score', 'value': 'high'},
        'severity': 'Low',
        'explanation': 'Remote work offers flexibility and no commute.',
        'recommendation': 'Remote work is a positive factor.',
        'priority': 3
    },
    {
        'id': 'R26',
        'name': 'Vague Responsibilities',
        'category': 'Workload and Conditions',
        'conditions': {
            'fact': 'clear_responsibilities', 'operator': 'equals', 'value': 'Vague'
        },
        'conclusion': {'fact': 'role_clarity_risk', 'value': 'vague_duties'},
        'severity': 'Medium',
        'explanation': 'Vague job responsibilities can lead to scope creep.',
        'recommendation': 'Request detailed job description before accepting.',
        'priority': 6
    },
    {
        'id': 'R27',
        'name': 'Clear Role Definition',
        'category': 'Workload and Conditions',
        'conditions': {
            'fact': 'clear_responsibilities', 'operator': 'equals', 'value': 'Yes - very clear'
        },
        'conclusion': {'fact': 'role_clarity_score', 'value': 'clear'},
        'severity': 'Low',
        'explanation': 'Clear responsibilities help set proper expectations.',
        'recommendation': 'Role clarity is good.',
        'priority': 4
    },
    {
        'id': 'R28',
        'name': 'Overwork with Low Pay',
        'category': 'Workload and Conditions',
        'conditions': {
            'AND': [
                {'fact': 'weekly_hours', 'operator': 'greaterThan', 'value': THRESHOLDS['reasonable_hours']},
                {'fact': 'compensation_score', 'operator': 'in', 'value': ['very_low', 'low_for_fulltime']}
            ]
        },
        'conclusion': {'fact': 'workload_risk', 'value': 'overwork_underpaid'},
        'severity': 'High',
        'explanation': 'Long hours with low pay is a bad combination.',
        'recommendation': 'Negotiate better terms or look elsewhere.',
        'priority': 8
    },
    {
        'id': 'R29',
        'name': 'Balanced Workload',
        'category': 'Workload and Conditions',
        'conditions': {
            'AND': [
                {'fact': 'weekly_hours', 'operator': 'lessThanOrEqual', 'value': THRESHOLDS['reasonable_hours']},
                {'fact': 'work_mode', 'operator': 'in', 'value': ['Remote', 'Hybrid']},
                {'fact': 'clear_responsibilities', 'operator': 'in', 'value': ['Yes - very clear', 'Somewhat clear']}
            ]
        },
        'conclusion': {'fact': 'workload_score', 'value': 'balanced'},
        'severity': 'Low',
        'explanation': 'Reasonable hours, flexibility, and clear duties create good conditions.',
        'recommendation': 'Working conditions appear favorable.',
        'priority': 5
    },
    {
        'id': 'R30',
        'name': 'Hybrid with Long Commute',
        'category': 'Workload and Conditions',
        'conditions': {
            'AND': [
                {'fact': 'work_mode', 'operator': 'equals', 'value': 'Hybrid'},
                {'fact': 'commute_time', 'operator': 'greaterThan', 'value': 60},
                {'fact': 'commute_time', 'operator': 'lessThanOrEqual', 'value': THRESHOLDS['long_commute_minutes']}
            ]
        },
        'conclusion': {'fact': 'workload_score', 'value': 'moderate_commute'},
        'severity': 'Low',
        'explanation': 'Hybrid mode with 1-1.5 hour commute is manageable.',
        'recommendation': 'Commute is notable but acceptable for hybrid.',
        'priority': 4
    },
    
    # ========================================================================
    # CATEGORY 4: LEGITIMACY RED FLAGS (Rules R31-R40)
    # ========================================================================
    {
        'id': 'R31',
        'name': 'Upfront Payment Demanded',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'fact': 'upfront_payment', 'operator': 'equals', 'value': 'Yes'
        },
        'conclusion': {'fact': 'legitimacy_risk', 'value': 'upfront_fee_scam'},
        'severity': 'Critical',
        'explanation': 'Legitimate employers NEVER ask for upfront payment.',
        'recommendation': 'REJECT. This is a common scam indicator.',
        'priority': 10
    },
    {
        'id': 'R32',
        'name': 'No Written Contract',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'fact': 'written_contract', 'operator': 'in', 'value': ['No', 'Verbal only']
        },
        'conclusion': {'fact': 'legitimacy_risk', 'value': 'no_contract'},
        'severity': 'High',
        'explanation': 'Lack of written contract leaves you unprotected.',
        'recommendation': 'Insist on written offer letter before starting.',
        'priority': 8
    },
    {
        'id': 'R33',
        'name': 'Early Sensitive Document Request',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'AND': [
                {'fact': 'sensitive_docs_early', 'operator': 'equals', 'value': 'Yes'},
                {'fact': 'written_contract', 'operator': 'notEquals', 'value': 'Yes'}
            ]
        },
        'conclusion': {'fact': 'legitimacy_risk', 'value': 'identity_theft_risk'},
        'severity': 'Critical',
        'explanation': 'Requesting CNIC/bank details without offer letter is suspicious.',
        'recommendation': 'REJECT. Possible identity theft attempt.',
        'priority': 10
    },
    {
        'id': 'R34',
        'name': 'High Pressure Tactics',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'fact': 'hiring_pressure', 'operator': 'equals', 'value': 'Yes - urgent'
        },
        'conclusion': {'fact': 'legitimacy_risk', 'value': 'pressure_tactics'},
        'severity': 'High',
        'explanation': 'Urgent pressure to decide is a manipulation tactic.',
        'recommendation': 'Take your time. Legitimate offers allow reasonable decision time.',
        'priority': 8
    },
    {
        'id': 'R35',
        'name': 'Multiple Red Flags',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'AND': [
                {'fact': 'written_contract', 'operator': 'in', 'value': ['No', 'Verbal only']},
                {'fact': 'paid_on_time', 'operator': 'equals', 'value': 'No'},
                {'fact': 'clear_responsibilities', 'operator': 'equals', 'value': 'Vague'}
            ]
        },
        'conclusion': {'fact': 'legitimacy_risk', 'value': 'multiple_red_flags'},
        'severity': 'Critical',
        'explanation': 'Multiple warning signs together indicate high risk.',
        'recommendation': 'Avoid this opportunity.',
        'priority': 9
    },
    {
        'id': 'R36',
        'name': 'Legitimate Documentation',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'AND': [
                {'fact': 'written_contract', 'operator': 'equals', 'value': 'Yes'},
                {'fact': 'clear_responsibilities', 'operator': 'in', 'value': ['Yes - very clear', 'Somewhat clear']}
            ]
        },
        'conclusion': {'fact': 'legitimacy_score', 'value': 'documented'},
        'severity': 'Low',
        'explanation': 'Written contract and clear responsibilities indicate legitimacy.',
        'recommendation': 'Documentation is in order.',
        'priority': 5
    },
    {
        'id': 'R37',
        'name': 'Reasonable Hiring Process',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'AND': [
                {'fact': 'hiring_pressure', 'operator': 'in', 'value': ['No - reasonable timeline', 'Somewhat']},
                {'fact': 'upfront_payment', 'operator': 'equals', 'value': 'No'}
            ]
        },
        'conclusion': {'fact': 'legitimacy_score', 'value': 'standard_process'},
        'severity': 'Low',
        'explanation': 'Normal timeline and no fees indicate legitimate process.',
        'recommendation': 'Hiring process appears standard.',
        'priority': 4
    },
    {
        'id': 'R38',
        'name': 'Scam Combination',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'AND': [
                {'fact': 'upfront_payment', 'operator': 'equals', 'value': 'Yes'},
                {'fact': 'hiring_pressure', 'operator': 'equals', 'value': 'Yes - urgent'}
            ]
        },
        'conclusion': {'fact': 'legitimacy_risk', 'value': 'likely_scam'},
        'severity': 'Critical',
        'explanation': 'Upfront fee + pressure = classic scam pattern.',
        'recommendation': 'REJECT and report. This is almost certainly a scam.',
        'priority': 10
    },
    {
        'id': 'R39',
        'name': 'Contract but Payment Issues',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'AND': [
                {'fact': 'written_contract', 'operator': 'equals', 'value': 'Yes'},
                {'fact': 'paid_on_time', 'operator': 'equals', 'value': 'No'}
            ]
        },
        'conclusion': {'fact': 'legitimacy_risk', 'value': 'payment_reliability'},
        'severity': 'Medium',
        'explanation': 'Even with a contract, no payment guarantee is concerning.',
        'recommendation': 'Add payment terms to contract before signing.',
        'priority': 6
    },
    {
        'id': 'R40',
        'name': 'Proper Sensitive Data Handling',
        'category': 'Legitimacy Red Flags',
        'conditions': {
            'AND': [
                {'fact': 'sensitive_docs_early', 'operator': 'equals', 'value': 'No'},
                {'fact': 'written_contract', 'operator': 'equals', 'value': 'Yes'}
            ]
        },
        'conclusion': {'fact': 'legitimacy_score', 'value': 'proper_data_handling'},
        'severity': 'Low',
        'explanation': 'Sensitive data requested after offer shows proper process.',
        'recommendation': 'Data handling follows standard practice.',
        'priority': 4
    },
    
    # ========================================================================
    # CATEGORY 5: OVERALL VERDICT (Rules R41-R50)
    # These rules use DERIVED facts from previous rules to make final judgments
    # ========================================================================
    {
        'id': 'R41',
        'name': 'Critical Scam Indicators',
        'category': 'Overall Verdict',
        'conditions': {
            'fact': 'legitimacy_risk', 'operator': 'in', 
            'value': ['upfront_fee_scam', 'identity_theft_risk', 'likely_scam']
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'High Risk'},
        'severity': 'Critical',
        'explanation': 'Critical scam indicators override all positive factors.',
        'recommendation': 'REJECT this offer immediately.',
        'priority': 10
    },
    {
        'id': 'R42',
        'name': 'Exploitation Pattern',
        'category': 'Overall Verdict',
        'conditions': {
            'fact': 'workload_risk', 'operator': 'in',
            'value': ['exploitative', 'overwork_underpaid']
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'High Risk'},
        'severity': 'Critical',
        'explanation': 'Exploitative working conditions make this unsuitable.',
        'recommendation': 'Reject offers that exploit your time and skills.',
        'priority': 10
    },
    {
        'id': 'R43',
        'name': 'Strong Positive Offer',
        'category': 'Overall Verdict',
        'conditions': {
            'AND': [
                {'fact': 'compensation_score', 'operator': 'in', 'value': ['good', 'excellent', 'good_fulltime']},
                {'fact': 'growth_potential', 'operator': 'in', 'value': ['excellent', 'comprehensive']},
                {'fact': 'legitimacy_score', 'operator': 'in', 'value': ['documented', 'proper_data_handling']}
            ]
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'Strongly Suitable'},
        'severity': 'Low',
        'explanation': 'Good pay, growth potential, and legitimate documentation.',
        'recommendation': 'This is a strong opportunity. Consider accepting.',
        'priority': 8
    },
    {
        'id': 'R44',
        'name': 'Acceptable with Conditions',
        'category': 'Overall Verdict',
        'conditions': {
            'AND': [
                {'fact': 'compensation_score', 'operator': 'in', 'value': ['good', 'reliable']},
                {'fact': 'workload_score', 'operator': 'in', 'value': ['reasonable', 'balanced']},
                {'fact': 'legitimacy_risk', 'operator': 'notIn', 
                 'value': ['upfront_fee_scam', 'identity_theft_risk', 'likely_scam', 'multiple_red_flags']}
            ]
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'Suitable With Conditions'},
        'severity': 'Low',
        'explanation': 'Overall acceptable but clarify some points before accepting.',
        'recommendation': 'Proceed with minor clarifications.',
        'priority': 7
    },
    {
        'id': 'R45',
        'name': 'Investigation Needed',
        'category': 'Overall Verdict',
        'conditions': {
            'fact': 'legitimacy_risk', 'operator': 'in',
            'value': ['no_contract', 'pressure_tactics', 'payment_reliability', 'multiple_red_flags']
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'Needs Further Investigation'},
        'severity': 'High',
        'explanation': 'Concerning signs require deeper investigation.',
        'recommendation': 'Request clarifications before deciding.',
        'priority': 8
    },
    {
        'id': 'R46',
        'name': 'Learning Justifies Low Pay',
        'category': 'Overall Verdict',
        'conditions': {
            'AND': [
                {'fact': 'value_proposition', 'operator': 'equals', 'value': 'learning_over_pay'},
                {'fact': 'legitimacy_score', 'operator': 'in', 'value': ['documented', 'standard_process']},
                {'fact': 'workload_score', 'operator': 'notEquals', 'value': 'exploitative'}
            ]
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'Suitable With Conditions'},
        'severity': 'Low',
        'explanation': 'Strong learning opportunity compensates for lower pay.',
        'recommendation': 'Accept if career growth is your priority.',
        'priority': 6
    },
    {
        'id': 'R47',
        'name': 'Dead End Low Value',
        'category': 'Overall Verdict',
        'conditions': {
            'AND': [
                {'fact': 'growth_potential', 'operator': 'in', 'value': ['poor', 'dead_end']},
                {'fact': 'compensation_score', 'operator': 'in', 'value': ['very_low', 'low_for_fulltime']}
            ]
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'High Risk'},
        'severity': 'High',
        'explanation': 'Low pay with minimal growth is a poor investment of your time.',
        'recommendation': 'Look for better opportunities.',
        'priority': 7
    },
    {
        'id': 'R48',
        'name': 'Moderate Opportunity',
        'category': 'Overall Verdict',
        'conditions': {
            'AND': [
                {'fact': 'growth_potential', 'operator': 'equals', 'value': 'moderate'},
                {'fact': 'compensation_score', 'operator': 'notIn', 'value': ['very_low']},
                {'fact': 'workload_score', 'operator': 'in', 'value': ['reasonable', 'moderate_commute']}
            ]
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'Suitable With Conditions'},
        'severity': 'Low',
        'explanation': 'Moderate across dimensions - acceptable but not exceptional.',
        'recommendation': 'Consider your alternatives before deciding.',
        'priority': 5
    },
    {
        'id': 'R49',
        'name': 'High Pay Overrides Issues',
        'category': 'Overall Verdict',
        'conditions': {
            'AND': [
                {'fact': 'compensation_score', 'operator': 'in', 'value': ['excellent', 'good_fulltime']},
                {'fact': 'legitimacy_risk', 'operator': 'notIn', 
                 'value': ['upfront_fee_scam', 'identity_theft_risk', 'likely_scam']},
                {'fact': 'workload_risk', 'operator': 'notIn', 'value': ['exploitative']}
            ]
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'Suitable With Conditions'},
        'severity': 'Low',
        'explanation': 'Excellent compensation can justify other moderate concerns.',
        'recommendation': 'Strong pay makes this worth considering.',
        'priority': 6
    },
    {
        'id': 'R50',
        'name': 'Unclear Situation',
        'category': 'Overall Verdict',
        'conditions': {
            'AND': [
                {'fact': 'compensation_score', 'operator': 'notIn', 
                 'value': ['very_low', 'good', 'excellent', 'good_fulltime', 'reliable']},
                {'fact': 'growth_potential', 'operator': 'notIn', 
                 'value': ['excellent', 'comprehensive', 'poor', 'dead_end']},
                {'fact': 'legitimacy_risk', 'operator': 'notIn',
                 'value': ['upfront_fee_scam', 'identity_theft_risk', 'likely_scam', 'multiple_red_flags']}
            ]
        },
        'conclusion': {'fact': 'final_verdict', 'value': 'Needs Further Investigation'},
        'severity': 'Medium',
        'explanation': 'Not enough clear indicators to make strong recommendation.',
        'recommendation': 'Gather more information before deciding.',
        'priority': 4
    },
]


def get_rule_by_id(rule_id):
    """Helper function to retrieve a rule by its ID."""
    for rule in RULES:
        if rule['id'] == rule_id:
            return rule
    return None


def get_rules_by_category(category):
    """Helper function to get all rules in a category."""
    return [rule for rule in RULES if rule['category'] == category]


def validate_knowledge_base():
    """
    Validate that the knowledge base is properly structured.
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Check we have exactly 50 rules
    if len(RULES) != 50:
        errors.append(f"Expected exactly 50 rules, found {len(RULES)}")
    
    # Check for unique IDs
    ids = [rule['id'] for rule in RULES]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate rule IDs found")
    
    # Check ID format (R01-R50)
    expected_ids = [f"R{i:02d}" for i in range(1, 51)]
    if set(ids) != set(expected_ids):
        errors.append(f"Rule IDs should be R01-R50, found: {ids}")
    
    # Check required fields in each rule
    required_fields = ['id', 'name', 'category', 'conditions', 'conclusion', 
                      'severity', 'explanation', 'recommendation', 'priority']
    for rule in RULES:
        missing = [f for f in required_fields if f not in rule]
        if missing:
            errors.append(f"Rule {rule.get('id', 'UNKNOWN')} missing fields: {missing}")
    
    return (len(errors) == 0, errors)
