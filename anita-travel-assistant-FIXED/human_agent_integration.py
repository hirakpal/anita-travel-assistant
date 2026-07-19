# agents/human_agent_integration.py
class HumanAgentIntegration:
    def __init__(self):
        self.name = "HumanAgentIntegration"

    def present_options(self, itinerary_summary):
        """
        Present agent outputs to the human for review.
        """
        print("\n--- Itinerary Summary ---")
        for section, items in itinerary_summary.items():
            print(f"\n{section.upper()}:")
            for i, item in enumerate(items, 1):
                print(f"{i}. {item}")

    def collect_feedback(self):
        """
        Collect human overrides or preferences.
        """
        feedback = input("\nEnter override (e.g., 'Prefer budget flight', 'Skip tour 2'): ")
        return feedback

    def apply_feedback(self, state, feedback):
        """
        Update agent state with human feedback.
        """
        state["constraint"] = feedback
        return state

