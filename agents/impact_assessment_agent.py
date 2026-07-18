from utils.models import ImpactReport

class ImpactAssessmentAgent:
    def __init__(self, mode="Online"):
        """
        mode = "Online" → run full evaluation logic
        mode = "Demo"   → return mock impact report for testing
        """
        self.mode = mode

    def assess(self, itinerary, traveler_type="general", preferences=None):
        """
        Assess the impact of an itinerary across sustainability, risk, wellbeing,
        cultural fit, budget, accessibility, health, time preferences, and group dynamics.
        Traveler type and preferences are factored into risk and recommendations.
        """

        # DEMO MODE → return static mock data
        if self.mode == "Demo":
            return {
                "sustainability": {
                    "carbon_score": "Medium",
                    "eco_alternatives": ["Demo Eco Hotel", "Demo Metro transport"]
                },
                "risk": {
                    "weather": "Clear skies",
                    "political": "None",
                    "risk_level": "Low"
                },
                "wellbeing": {
                    "activity_balance": "Balanced",
                    "recommendation": "Looks good"
                },
                "cultural_fit": {
                    "sensitivity": "Demo cultural note",
                    "dietary": "Demo dietary options"
                },
                "budget": {
                    "flag": "Affordable",
                    "alternatives": ["Demo budget hotel", "Demo street food tour"]
                },
                "accessibility": {
                    "wheelchair_friendly_hotels": ["Demo Accessible Hotel"],
                    "accessible_tours": ["Demo Accessible Tour"]
                },
                "health": {
                    "altitude_risk": "Low",
                    "vaccination_advisories": ["Demo vaccination advisory"]
                },
                "time_preferences": {
                    "morning_activities": ["Demo morning walk"],
                    "evening_activities": ["Demo evening concert"]
                },
                "group_dynamics": {
                    "shared_activities": ["Demo family cooking class"],
                    "solo_activities": ["Demo solo photography walk"]
                }
            }

        # ONLINE MODE → run full evaluation logic
        # --- Sustainability ---
        sustainability = {
            "carbon_score": "High" if "flight" in str(itinerary).lower() else "Low",
            "eco_alternatives": ["Eco Hotel Verde", "Metro transport"]
        }

        # --- Risk & Safety ---
        risk_level = "Medium"
        if traveler_type == "solo":
            risk_level = "High" if "rally" in str(itinerary).lower() else "Medium"
        elif traveler_type == "family":
            risk_level = "High" if "heatwave" in str(itinerary).lower() else "Low"
        elif traveler_type == "senior":
            risk_level = "High" if "late night" in str(itinerary).lower() else "Medium"
        elif traveler_type == "adventure":
            risk_level = "Medium"  # adventure travelers tolerate more risk

        risk = {
            "weather": "Heatwave advisory" if "heatwave" in str(itinerary).lower() else "Clear",
            "political": "Rally near Piazza Venezia" if "rally" in str(itinerary).lower() else "None",
            "risk_level": risk_level
        }

        # --- Wellbeing ---
        wellbeing = {
            "activity_balance": "Packed schedule" if len(itinerary.get("tours", [])) > 3 else "Balanced",
            "recommendation": "Add rest day" if len(itinerary.get("tours", [])) > 3 else "Looks good"
        }

        # --- Cultural & Social Fit ---
        cultural_fit = {
            "sensitivity": "Dress modestly at religious sites",
            "dietary": "Vegetarian options available"
        }

        # --- Budget Sensitivity ---
        budget = {
            "flag": "Expensive" if "luxury" in str(itinerary).lower() else "Affordable",
            "alternatives": ["Budget hotel", "Street food tour"]
        }

        # --- Accessibility Needs ---
        accessibility = {
            "wheelchair_friendly_hotels": ["Hotel Roma Accessible"],
            "accessible_tours": ["Colosseum ramp access tour"]
        }

        # --- Health Considerations ---
        health = {
            "altitude_risk": "High" if "Cusco" in str(itinerary) else "Low",
            "vaccination_advisories": ["Yellow fever recommended for Africa trips"]
        }

        # --- Time Preferences ---
        time_pref = {
            "morning_activities": ["Museum tours", "City walks"],
            "evening_activities": ["Jazz festival", "Night market"]
        }

        # --- Group Dynamics ---
        group_dynamics = {
            "shared_activities": ["Family cooking class"],
            "solo_activities": ["Photography walk"]
        }

        # --- Final Impact Report ---
        return {
            "sustainability": sustainability,
            "risk": risk,
            "wellbeing": wellbeing,
            "cultural_fit": cultural_fit,
            "budget": budget,
            "accessibility": accessibility,
            "health": health,
            "time_preferences": time_pref,
            "group_dynamics": group_dynamics
        }
