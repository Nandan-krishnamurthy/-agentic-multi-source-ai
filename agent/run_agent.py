from agent.executor import execute
from agent.planner import plan

def run_agent(
    user_question: str,
    fallback_to_vector: bool = True,
    fallback_to_web: bool = True
):
    # planner returns a dict like {"tool": "...", "reason": "..."}
    plan_result = plan(user_question)
    tool_name = plan_result["tool"]

    return execute(
        tool_name=tool_name,
        user_question=user_question,
        fallback_to_vector=fallback_to_vector,
        fallback_to_web=fallback_to_web
    )
