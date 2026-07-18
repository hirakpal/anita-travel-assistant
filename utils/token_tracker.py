# utils/token_tracker.py
_token_log = {}

def log_tokens(agent_name, prompt_tokens, response_tokens):
    total = prompt_tokens + response_tokens
    _token_log.setdefault(agent_name, []).append(total)

def get_usage(agent_name):
    return sum(_token_log.get(agent_name, []))

def get_all_usage():
    return {agent: sum(tokens) for agent, tokens in _token_log.items()}
