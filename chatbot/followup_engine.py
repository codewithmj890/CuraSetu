import os
import json
from django.conf import settings


class FollowUpEngine:
    """
    Slot-based follow-up engine.
    Asks EXACTLY ONE most important unanswered question.
    NO hard-coded diseases. NO followup_rules.json.
    """

    def __init__(self):
        self.disease_data = self._load_disease_data()
        self.SLOT_QUESTIONS = self._init_slot_questions()

    def _init_slot_questions(self):
        """Canonical slot question registry (GLOBAL)"""
        return {
            'fever': {
                'question': 'Do you have fever?',
                'options': ['Yes', 'No']
            },
            'duration': {
                'question': 'How many days have you had these symptoms?',
                'options': ['1-2 days', '3-5 days', 'More than 5 days']
            },
            'white_patches': {
                'question': 'Do you see white patches on your tonsils?',
                'options': ['Yes', 'No', 'Not sure']
            },
            'difficulty_swallowing': {
                'question': 'Is swallowing painful?',
                'options': ['Mild', 'Moderate', 'Severe']
            },
            'painful': {
                'question': 'Is it painful?',
                'options': ['Yes', 'No']
            },
            'itching': {
                'question': 'Is there itching?',
                'options': ['Yes, severe', 'Yes, mild', 'No']
            },
            'location': {
                'question': 'Where is the pain located?',
                'options': ['One side', 'Both sides', 'All over']
            },
            'cough_type': {
                'question': 'Is the cough dry or producing phlegm?',
                'options': ['Dry', 'With phlegm', 'Both']
            },
            'shortness_of_breath': {
                'question': 'Do you have shortness of breath?',
                'options': ['Yes', 'No']
            },
            'blood_in_stool': {
                'question': 'Have you noticed any blood in your stool?',
                'options': ['Yes', 'No']
            },
            'vomiting': {
                'question': 'Are you experiencing vomiting?',
                'options': ['Yes', 'No']
            },
            'joint_location': {
                'question': 'Which joints are affected?',
                'options': ['Hands', 'Knees', 'Both', 'Other']
            },
            'morning_stiffness': {
                'question': 'Do you have morning stiffness?',
                'options': ['Yes, >1 hour', 'Yes, <30 mins', 'No']
            },
            'swelling': {
                'question': 'Is there swelling?',
                'options': ['Yes', 'No']
            },
            'chest_pain_type': {
                'question': 'What type of chest pain?',
                'options': ['Crushing', 'Sharp', 'Burning', 'Dull']
            },
            'exertion_related': {
                'question': 'Does the pain worsen with exertion?',
                'options': ['Yes', 'No']
            },
            'thirst': {
                'question': 'Are you experiencing excessive thirst?',
                'options': ['Yes', 'No']
            },
            'urination_frequency': {
                'question': 'Are you urinating more frequently?',
                'options': ['Yes', 'No']
            },
            'weight_change': {
                'question': 'Have you noticed any weight change?',
                'options': ['Weight loss', 'Weight gain', 'No change']
            },
            'blood_pressure_reading': {
                'question': 'Have you measured your blood pressure recently?',
                'options': ['Yes, high', 'Yes, normal', 'No']
            },
            'burning_urination': {
                'question': 'Do you have burning sensation during urination?',
                'options': ['Yes', 'No']
            },
            'frequency': {
                'question': 'How often do you need to urinate?',
                'options': ['Very frequently', 'Moderately', 'Normal']
            },
            'fever_pattern': {
                'question': 'Does your fever come and go in cycles?',
                'options': ['Yes', 'No']
            },
            'chills': {
                'question': 'Do you have chills?',
                'options': ['Yes', 'No']
            },
            'fever_progression': {
                'question': 'How did your fever start?',
                'options': ['Gradually increasing', 'Sudden high fever']
            },
            'abdominal_pain': {
                'question': 'Do you have abdominal pain?',
                'options': ['Yes', 'No']
            },
            'loss_of_smell': {
                'question': 'Have you lost your sense of smell or taste?',
                'options': ['Yes', 'No']
            },
            'breathing_difficulty': {
                'question': 'Are you having difficulty breathing?',
                'options': ['Yes', 'No']
            },
            'fatigue_level': {
                'question': 'How severe is your fatigue?',
                'options': ['Severe', 'Moderate', 'Mild']
            },
            'pale_skin': {
                'question': 'Have you noticed pale skin or gums?',
                'options': ['Yes', 'No']
            },
            'mood_duration': {
                'question': 'How long have you felt this way?',
                'options': ['< 2 weeks', '2-6 months', '> 6 months']
            },
            'sleep_pattern': {
                'question': 'How is your sleep?',
                'options': ['Difficulty sleeping', 'Sleeping too much', 'Normal']
            },
            'onset_speed': {
                'question': 'How quickly did symptoms start?',
                'options': ['Sudden (minutes)', 'Gradual (hours/days)', 'Slow (weeks)']
            },
            'weakness_location': {
                'question': 'Where is the weakness?',
                'options': ['One side', 'Both sides', 'Legs only', 'Arms only']
            },
            'severity': {
                'question': 'How severe are your symptoms?',
                'options': ['Mild', 'Moderate', 'Severe']
            }
        }

    def _load_disease_data(self):
        """Load disease data from JSON"""
        try:
            path = os.path.join(settings.BASE_DIR, "disease_data.json")
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle both list and dict formats
                if isinstance(data, list):
                    return {d["disease"]: d for d in data}
                return data
        except Exception as e:
            print(f"[FollowUpEngine] Failed to load disease data: {e}")
            return {}

    def get_next_question(self, disease_name, resolved_slots_by_disease):
        """
        Returns ONE next critical unanswered slot question.
        
        Args:
            disease_name: Exact disease name from RAG
            resolved_slots_by_disease: Dict of {disease: {slot_id: answer}}
        
        Returns:
            Single question dict with id, question, options OR None
        """
        disease = self.disease_data.get(disease_name)
        if not disease:
            return None

        diagnostic_slots = disease.get('diagnostic_slots', [])
        if not diagnostic_slots:
            return None
        
        # Get disease-specific resolved slots only
        resolved_slots = resolved_slots_by_disease.get(disease_name, {})
        
        # Priority order from disease data or default
        priority_order = disease.get('priority_slots', ['fever', 'duration'])
        
        # Check priority slots first (ONLY if not already resolved)
        for slot in priority_order:
            if slot in diagnostic_slots and slot not in resolved_slots:
                q = self.SLOT_QUESTIONS.get(slot)
                if q:
                    return {
                        'id': slot,
                        'question': q['question'],
                        'options': q['options']
                    }
        
        # Then check remaining diagnostic slots (ONLY if not already resolved)
        for slot in diagnostic_slots:
            if slot not in resolved_slots:
                q = self.SLOT_QUESTIONS.get(slot)
                if q:
                    return {
                        'id': slot,
                        'question': q['question'],
                        'options': q['options']
                    }
        
        return None
    
    def extract_resolved_slots(self, user_input, active_system=None):
        """
        Extract resolved slots from user's free text input.
        Context-aware to prevent cross-system slot pollution.
        
        Args:
            user_input: User's symptom description
            active_system: Body system (ENT, DERMATOLOGY, etc.)
        
        Returns:
            Dict of {slot_id: 'Yes'} for detected symptoms
        """
        resolved = {}
        text_lower = user_input.lower()
        
        # Universal symptoms (any system)
        if any(term in text_lower for term in ['fever', 'temperature', 'hot']):
            resolved['fever'] = 'Yes'
        
        if any(term in text_lower for term in ['cough', 'coughing']):
            resolved['cough_type'] = 'Yes'
        
        if 'headache' in text_lower:
            resolved['location'] = 'Yes'
        
        # ENT-specific (only if ENT system)
        if active_system == 'ENT':
            if any(term in text_lower for term in ['swallow', 'throat']):
                resolved['difficulty_swallowing'] = 'Yes'
            if 'white' in text_lower and 'patch' in text_lower:
                resolved['white_patches'] = 'Yes'
        
        # Dermatology-specific (only if DERMATOLOGY system)
        if active_system == 'DERMATOLOGY':
            if any(term in text_lower for term in ['itch', 'itchy', 'itching']):
                resolved['itching'] = 'Yes'
            if any(term in text_lower for term in ['painful', 'pus', 'hurt']):
                resolved['painful'] = 'Yes'
        
        # Respiratory-specific
        if active_system == 'RESPIRATORY':
            if any(term in text_lower for term in ['breath', 'breathing']):
                resolved['shortness_of_breath'] = 'Yes'
        
        # Systemic symptoms
        if any(term in text_lower for term in ['joint', 'joints']):
            resolved['joint_location'] = 'Yes'
        
        if 'rash' in text_lower:
            resolved['rash'] = 'Yes'
        
        return resolved
    
    def is_complete(self, disease_name, resolved_slots_by_disease):
        """
        Check if all required diagnostic slots are filled for this disease.
        
        Args:
            disease_name: Disease being diagnosed
            resolved_slots_by_disease: Dict of {disease: {slot_id: answer}}
        
        Returns:
            True if all required slots filled, False otherwise
        """
        disease = self.disease_data.get(disease_name)
        if not disease:
            return True
        
        required_slots = disease.get('diagnostic_slots', [])
        if not required_slots:
            return True
        
        # Get disease-specific resolved slots
        resolved = resolved_slots_by_disease.get(disease_name, {})
        
        # Check if all required slots are resolved
        return all(slot in resolved for slot in required_slots)
    
    def required_slots(self, disease_name):
        """Get list of required slots for a disease"""
        disease = self.disease_data.get(disease_name)
        if not disease:
            return []
        return disease.get('diagnostic_slots', [])
