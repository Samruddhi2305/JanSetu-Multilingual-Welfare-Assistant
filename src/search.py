import json
import os
import re

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'schemes.json')

def load_schemes():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schemes: {str(e)}")
        return []

def screen_eligibility(user_profile):
    """
    Evaluates eligibility of schemes based on user profile.
    user_profile: {
      'age': int/None,
      'income': int/None, (annual)
      'occupation': str/None,
      'gender': str/None, (Male/Female/Other)
      'state': str/None
    }
    """
    schemes = load_schemes()
    eligible = []
    
    # Normalize inputs
    age = user_profile.get('age')
    if isinstance(age, str):
        try: age = int(age)
        except: age = None
        
    income = user_profile.get('income')
    if isinstance(income, str):
        try: income = int(income)
        except: income = None
        
    occupation = user_profile.get('occupation', '')
    if occupation:
        occupation = occupation.strip().lower()
        
    gender = user_profile.get('gender', '')
    if gender:
        gender = gender.strip().lower()

    for scheme in schemes:
        el_rules = scheme.get('eligibility', {})
        is_eligible = True
        
        # 1. Age check
        min_age = el_rules.get('min_age')
        max_age = el_rules.get('max_age')
        if age is not None:
            if min_age is not None and age < min_age:
                is_eligible = False
            if max_age is not None and age > max_age:
                is_eligible = False
                
        # 2. Income check (annual)
        max_inc = el_rules.get('max_income_annual')
        if income is not None and max_inc is not None:
            if income > max_inc:
                is_eligible = False
                
        # 3. Gender check
        genders = el_rules.get('genders', 'All')
        if isinstance(genders, list) and gender:
            norm_genders = [g.lower() for g in genders]
            if gender not in norm_genders:
                is_eligible = False
                
        # 4. Occupation check
        occupations = el_rules.get('occupations', 'All')
        if isinstance(occupations, list) and occupation:
            # check if user occupation is in scheme occupations (sub-string matching)
            norm_occupations = [o.lower() for o in occupations]
            matched = False
            for o in norm_occupations:
                if o in occupation or occupation in o or o == 'all':
                    matched = True
                    break
            if not matched:
                is_eligible = False
                
        if is_eligible:
            eligible.append(scheme)
            
    return eligible

def search_schemes(query, user_profile=None):
    """
    Filters schemes by text search query and optionally screens eligibility.
    """
    schemes = load_schemes()
    if user_profile:
        # Screen first
        schemes = screen_eligibility(user_profile)
        
    if not query:
        return schemes
        
    # Simple keyword match
    query_words = [w.lower() for w in re.split(r'\W+', query) if w]
    matched = []
    
    for scheme in schemes:
        text_content = (scheme['name'] + ' ' + scheme['description'] + ' ' + scheme['benefit'] + ' ' + scheme['target_group']).lower()
        
        # Calculate matching score
        score = 0
        for qw in query_words:
            if qw in text_content:
                score += 1
                
        if score > 0:
            matched.append((score, scheme))
            
    # Sort by score descending
    matched.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in matched]

if __name__ == '__main__':
    # Quick test
    test_profile = {'age': 35, 'income': 100000, 'occupation': 'Farmer', 'gender': 'Male'}
    results = screen_eligibility(test_profile)
    print("Eligible Schemes for Farmer:")
    for r in results:
        print(f"- {r['name']}")
