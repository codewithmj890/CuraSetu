import os
import google.generativeai as genai
from django.conf import settings

class GeminiService:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"API Key found: {'Yes' if api_key else 'No'}")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def format_to_table(self, response_text):
        """Convert AI response to HTML table format"""
        print(f"Formatting response: {response_text}")
        
        lines = response_text.strip().split('\n')
        
        # Extract disease name
        disease = "Unknown"
        generic_cures = []
        desi_cures = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for disease
            if "Expected Disease:" in line or "Disease:" in line:
                disease = line.split(":", 1)[1].strip().replace("*", "")
                continue
            
            # Check for section headers
            if "Generic Cure" in line:
                current_section = "generic"
                continue
            elif "Desi Cure" in line:
                current_section = "desi"
                continue
            
            # Parse cure items
            if line.startswith("-") and current_section:
                cure_text = line[1:].strip()
                
                # Extract name and description
                if "**" in cure_text and ":**" in cure_text:
                    # Format: - **Name:** Description
                    parts = cure_text.split(":**", 1)
                    name = parts[0].replace("*", "").strip()
                    desc = parts[1].strip()
                elif ":" in cure_text:
                    # Format: - Name: Description
                    parts = cure_text.split(":", 1)
                    name = parts[0].replace("*", "").strip()
                    desc = parts[1].strip()
                else:
                    # Just description
                    name = "Treatment"
                    desc = cure_text.replace("*", "").strip()
                
                if current_section == "generic" and len(generic_cures) < 3:
                    generic_cures.append((name, desc))
                elif current_section == "desi" and len(desi_cures) < 3:
                    desi_cures.append((name, desc))
        
        # Fill with defaults if needed
        default_generic = [
            ("Rest", "Get adequate rest and sleep"),
            ("Hydration", "Drink plenty of fluids"),
            ("Medication", "Take appropriate over-the-counter medicine")
        ]
        
        default_desi = [
            ("Kadha", "Herbal tea with ginger, tulsi, and honey"),
            ("Steam", "Steam inhalation with eucalyptus"),
            ("Turmeric", "Turmeric milk or paste application")
        ]
        
        while len(generic_cures) < 3:
            generic_cures.append(default_generic[len(generic_cures)])
        while len(desi_cures) < 3:
            desi_cures.append(default_desi[len(desi_cures)])
        
        # Create HTML table
        table_html = f"""
        <div class="table-responsive">
        <table class="table table-dark table-striped table-hover">
        <thead class="table-primary">
        <tr>
        <th style="width: 25%;">Category</th>
        <th style="width: 30%;">Treatment</th>
        <th style="width: 45%;">Description</th>
        </tr>
        </thead>
        <tbody>
        <tr class="table-warning">
        <td><strong>Expected Disease</strong></td>
        <td colspan="2"><strong>{disease}</strong></td>
        </tr>
        """
        
        # Add generic cures
        for i, (name, desc) in enumerate(generic_cures[:3], 1):
            table_html += f"""
        <tr>
        <td><strong>Generic Cure {i}</strong></td>
        <td>{name}</td>
        <td>{desc}</td>
        </tr>
        """
        
        # Add desi cures
        for i, (name, desc) in enumerate(desi_cures[:3], 1):
            table_html += f"""
        <tr class="table-success">
        <td><strong>Desi Cure {i}</strong></td>
        <td>{name}</td>
        <td>{desc}</td>
        </tr>
        """
        
        table_html += """
        </tbody>
        </table>
        </div>
        """
        
        return table_html
    
    def get_health_advice(self, symptoms):
        prompt = f"""
        You are an expert healthcare AI assistant with deep knowledge of both modern medicine and traditional Indian (Ayurvedic/home) remedies. 
        
        Analyze these symptoms carefully: {symptoms}
        
        Instructions:
        1. Consider symptom combinations, duration, and severity
        2. Identify the most probable minor condition based on medical knowledge
        3. Provide evidence-based generic treatments with specific dosages/instructions
        4. Suggest authentic traditional Indian remedies with preparation methods
        5. If symptoms indicate serious conditions (chest pain, difficulty breathing, severe headache, high fever >102°F, persistent vomiting), immediately recommend emergency medical care
        
        Respond in this exact format:
        
        Expected Disease: [Specific condition name with brief explanation]
        
        Generic Cure:
        - **[Treatment 1]:** [Specific instructions with dosage/frequency]
        - **[Treatment 2]:** [Specific instructions with dosage/frequency] 
        - **[Treatment 3]:** [Specific instructions with dosage/frequency]
        
        Desi Cure:
        - **[Traditional Remedy 1]:** [Detailed preparation and usage instructions]
        - **[Traditional Remedy 2]:** [Detailed preparation and usage instructions]
        - **[Traditional Remedy 3]:** [Detailed preparation and usage instructions]
        
        Medical Disclaimer: These suggestions are for minor conditions only. Consult a qualified healthcare provider for proper diagnosis and treatment, especially if symptoms persist or worsen.
        """
        
        try:
            response = self.model.generate_content(prompt)
            print(f"API Response received: {response.text[:100]}...")
            return self.format_to_table(response.text)
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            # Return actual AI response for the symptoms
            return self.create_manual_response(symptoms)
    
    def create_manual_response(self, symptoms):
        """Create an intelligent manual response based on symptom analysis"""
        symptoms_lower = symptoms.lower()
        
        # Respiratory symptoms
        if any(word in symptoms_lower for word in ['cough', 'cold', 'runny nose', 'sneezing', 'sore throat']):
            if 'fever' in symptoms_lower:
                disease = "Viral Upper Respiratory Infection (Common Cold with Fever)"
                generic_cures = [
                    ("Paracetamol", "500mg every 6 hours for fever (max 4g/day). Monitor temperature"),
                    ("Rest", "Complete bed rest for 2-3 days. Avoid physical exertion"),
                    ("Hydration", "Drink 3-4 liters of fluids daily: water, warm soups, herbal teas")
                ]
                desi_cures = [
                    ("Immunity Kadha", "Boil 1 cup water with 1 inch ginger, 10 tulsi leaves, 2 cloves, 1 tsp honey. Drink 3x daily"),
                    ("Steam Therapy", "Inhale steam with 2-3 drops eucalyptus oil for 10 mins, 3x daily"),
                    ("Golden Milk", "1 tsp turmeric + pinch black pepper in warm milk before bed")
                ]
            else:
                disease = "Common Cold (Viral Rhinitis)"
                generic_cures = [
                    ("Saline Rinse", "Use saline nasal spray 3-4 times daily to clear congestion"),
                    ("Throat Lozenges", "Sugar-free lozenges every 2-3 hours for sore throat"),
                    ("Humidifier", "Use humidifier or breathe moist air to ease congestion")
                ]
                desi_cures = [
                    ("Ginger Tea", "Fresh ginger slices in hot water with honey, 3-4 cups daily"),
                    ("Salt Water Gargle", "1 tsp salt in warm water, gargle 4-5 times daily"),
                    ("Ajwain Steam", "Add 1 tsp carom seeds to hot water, inhale steam 2x daily")
                ]
        
        # Digestive symptoms
        elif any(word in symptoms_lower for word in ['stomach', 'nausea', 'vomiting', 'diarrhea', 'acidity', 'gas']):
            disease = "Gastric Upset/Indigestion"
            generic_cures = [
                ("ORS", "Oral rehydration solution every 2 hours if diarrhea present"),
                ("Antacid", "Take antacid 30 mins after meals if acidity (follow package instructions)"),
                ("BRAT Diet", "Banana, Rice, Applesauce, Toast for 24-48 hours")
            ]
            desi_cures = [
                ("Jeera Water", "Boil 1 tsp cumin seeds in water, strain, drink warm 3x daily"),
                ("Ginger Remedy", "Fresh ginger juice with lemon and salt before meals"),
                ("Buttermilk", "Fresh buttermilk with roasted cumin powder and salt, 2-3 glasses daily")
            ]
        
        # Headache symptoms
        elif any(word in symptoms_lower for word in ['headache', 'head pain', 'migraine']):
            disease = "Tension Headache/Mild Migraine"
            generic_cures = [
                ("Pain Relief", "Paracetamol 500mg or Ibuprofen 400mg (follow dosage instructions)"),
                ("Rest", "Lie down in dark, quiet room for 30-60 minutes"),
                ("Hydration", "Drink 2-3 glasses of water immediately, continue regular intake")
            ]
            desi_cures = [
                ("Head Massage", "Gentle massage with coconut oil mixed with 2 drops peppermint oil"),
                ("Cold Compress", "Apply cold cloth on forehead for 15 minutes, repeat as needed"),
                ("Tulsi Tea", "Fresh tulsi leaves tea with honey, 2-3 cups throughout the day")
            ]
        
        # Body aches and fever
        elif any(word in symptoms_lower for word in ['body ache', 'muscle pain', 'joint pain', 'weakness']):
            disease = "Viral Myalgia/Body Aches"
            generic_cures = [
                ("Anti-inflammatory", "Ibuprofen 400mg every 8 hours with food (if no contraindications)"),
                ("Warm Bath", "Warm water bath with Epsom salt for 15-20 minutes"),
                ("Gentle Movement", "Light stretching or walking to prevent stiffness")
            ]
            desi_cures = [
                ("Mustard Oil Massage", "Warm mustard oil with garlic, massage affected areas gently"),
                ("Turmeric Paste", "Mix turmeric with coconut oil, apply on painful joints"),
                ("Herbal Decoction", "Boil ginger, turmeric, black pepper in milk, drink warm 2x daily")
            ]
        
        else:
            disease = "General Health Concern"
            generic_cures = [
                ("Observation", "Monitor symptoms for 24-48 hours, note any changes"),
                ("Hydration", "Maintain adequate fluid intake (8-10 glasses water daily)"),
                ("Medical Consultation", "Consult healthcare provider if symptoms persist or worsen")
            ]
            desi_cures = [
                ("Immunity Booster", "Amla juice with honey on empty stomach daily"),
                ("Herbal Tea", "Tulsi, ginger, and honey tea for general wellness"),
                ("Balanced Diet", "Include fresh fruits, vegetables, and avoid processed foods")
            ]
        
        # Create HTML table with medical disclaimer
        table_html = f"""
        <div class="table-responsive">
        <table class="table table-dark table-striped table-hover">
        <thead class="table-primary">
        <tr>
        <th style="width: 25%;">Category</th>
        <th style="width: 30%;">Treatment</th>
        <th style="width: 45%;">Description</th>
        </tr>
        </thead>
        <tbody>
        <tr class="table-warning">
        <td><strong>Expected Condition</strong></td>
        <td colspan="2"><strong>{disease}</strong></td>
        </tr>
        """
        
        for i, (name, desc) in enumerate(generic_cures, 1):
            table_html += f"""
        <tr>
        <td><strong>Medical Treatment {i}</strong></td>
        <td>{name}</td>
        <td>{desc}</td>
        </tr>
        """
        
        for i, (name, desc) in enumerate(desi_cures, 1):
            table_html += f"""
        <tr class="table-success">
        <td><strong>Traditional Remedy {i}</strong></td>
        <td>{name}</td>
        <td>{desc}</td>
        </tr>
        """
        
        table_html += """
        <tr class="table-info">
        <td><strong>⚠️ Disclaimer</strong></td>
        <td colspan="2"><small>This is AI-generated advice for minor conditions only. Consult a qualified doctor for proper diagnosis and treatment, especially if symptoms persist beyond 3 days or worsen.</small></td>
        </tr>
        </tbody>
        </table>
        </div>
        """
        
        return table_html