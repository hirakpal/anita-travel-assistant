class HumanAgentIntegration:
    def __init__(self, name="HumanAgentIntegration"):
        self.name = name
        self.prompt = """
        You are the Human Integration Agent.
        Task: Ensure user approval before applying changes.
        """

    def run(self, state):
        if state.get("pending_change"):
            return {"message": "Do you approve this change or keep the original plan?"}
        return {"message": "No pending changes"}
