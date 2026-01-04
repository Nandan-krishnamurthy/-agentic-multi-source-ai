"""
Streamlit UI for Agentic Multi-Source AI System

This app orchestrates the agent components:
1. Planner - decides which tool to use
2. Executor - executes the chosen tool
3. Responder - generates the final answer
"""

from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv()

import streamlit as st
from agent import planner, executor, responder


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Agentic AI System",
        page_icon="🤖",
        layout="wide"
    )
    
    # Title and description
    st.title("🤖 Agentic Multi-Source AI System")
    st.markdown("""
    This system intelligently routes your questions to the most appropriate data source:
    - **Direct Answer**: Simple questions and greetings
    - **Vector Search**: Document and policy questions
    - **Graph Search**: Relationship and organizational queries
    - **Web Search**: Current events and external information
    """)
    
    st.divider()
    
    # User input section
    st.subheader("Ask a Question")
    user_question = st.text_input(
        "Enter your question:",
        placeholder="Ask a question about OpenAI, its people, products, or system architecture…",
        key="question_input"
    )
    
    submit_button = st.button("Submit", type="primary", use_container_width=True)
    
    # Process question when submitted
    if submit_button and user_question:
        process_question(user_question)
    elif submit_button and not user_question:
        st.warning("Please enter a question first.")


def validate_results(tool_name: str, execution_result: dict) -> bool:
    """
    Validate if tool execution returned useful results.
    
    Args:
        tool_name: Name of the tool that was executed
        execution_result: The raw execution result
        
    Returns:
        True if results are valid/useful, False otherwise
    """
    # direct_answer and web_search always considered valid
    if tool_name in ["direct_answer", "web_search"]:
        return True
    
    # Check if results exist
    if not execution_result or "results" not in execution_result:
        return False
    
    results = execution_result["results"]
    
    # Empty results = validation failure
    if not results:
        return False
    
    # For list results, check if non-empty
    if isinstance(results, list) and len(results) == 0:
        return False
    
    # For graph search, check if we have actual data
    if tool_name == "graph_search":
        if isinstance(results, list):
            # Check if any result has meaningful data
            for item in results:
                if isinstance(item, dict) and "name" in item:
                    return True
            return False
    
    # For vector search, check if we have document chunks
    if tool_name == "vector_search":
        if isinstance(results, list):
            # Check if any result has text content
            for item in results:
                if isinstance(item, dict) and item.get("text", "").strip():
                    return True
            return False
    
    # Default: consider valid if we got here
    return True


def process_question(user_question: str):
    """
    Orchestrate the agent workflow:
    1. Plan - decide which tool to use
    2. Execute - run the tool (with automatic fallback from graph to vector)
    3. Validate - check if results are useful
    4. Fallback - if validation fails, try web_search
    5. Respond - generate final answer
    """
    
    try:
        # Step 1: Planning
        with st.spinner("🧠 Planning..."):
            plan_result = planner.plan(user_question)
            tool_name = plan_result["tool"]
            tool_reason = plan_result["reason"]
        
        # Step 2: Execution (with automatic fallback: graph->vector->web or vector->web)
        try:
            with st.spinner(f"🔧 Executing {tool_name}..."):
                execution_result = executor.execute(tool_name, user_question)
                
                # Check if executor performed a fallback
                if execution_result.get("fallback_used"):
                    original = execution_result.get("original_tool")
                    current = execution_result["tool"]
                    fallback_chain = execution_result.get("fallback_chain")
                    
                    if fallback_chain:
                        st.info(f"ℹ️ {fallback_chain}")
                    elif original == "graph_search" and current == "vector_search":
                        st.info(f"ℹ️ Graph search returned no results. Automatically fell back to vector search.")
                    elif original == "graph_search" and current == "web_search":
                        st.info(f"ℹ️ Graph search and vector search returned no results. Automatically fell back to web search.")
                    elif original == "vector_search" and current == "web_search":
                        st.info(f"ℹ️ Vector search returned no results. Automatically fell back to web search.")
                    
                    tool_name = current
                    tool_reason = f"Fallback from {original} (no internal data found)"
                    
        except Exception as exec_error:
            # Tool execution failed - display error and stop
            st.error(f"❌ Error executing {tool_name}: {str(exec_error)}")
            with st.expander("View Error Details"):
                st.exception(exec_error)
            # Do NOT call responder when executor fails
            return
        
        # Step 3: Validate Results & Additional Fallback (if executor didn't handle it)
        fallback_used = execution_result.get("fallback_used", False)
        original_tool = execution_result.get("original_tool", None) if fallback_used else tool_name
        
        # Only do additional validation fallback if executor hasn't already done it
        # and the current tool is not already web_search
        if not fallback_used and tool_name in ["vector_search", "graph_search"]:
            is_valid = validate_results(tool_name, execution_result)
            
            if not is_valid:
                # Results are empty/invalid - fall back to web_search
                st.info(f"ℹ️ {tool_name} returned no useful results. Falling back to web search...")
                
                try:
                    with st.spinner("🌐 Searching the web..."):
                        execution_result = executor.execute("web_search", user_question)
                        tool_name = "web_search"
                        tool_reason = f"Fallback from {original_tool} (no internal data found)"
                        fallback_used = True
                except Exception as fallback_error:
                    st.error(f"❌ Web search fallback also failed: {str(fallback_error)}")
                    return
        
        # Step 4: Response Generation (only if execution succeeded)
        with st.spinner("✍️ Generating response..."):
            final_response = responder.respond(
                user_question=user_question,
                tool_name=tool_name,
                tool_reason=tool_reason,
                tool_result=execution_result
            )
        
        # Display results with fallback info
        display_results(
            plan_result=plan_result,
            execution_result=execution_result,
            final_response=final_response,
            fallback_used=fallback_used,
            original_tool=original_tool if fallback_used else None
        )
        
    except Exception as e:
        st.error(f"❌ Error processing question: {str(e)}")
        with st.expander("View Error Details"):
            st.exception(e)


def display_results(plan_result: dict, execution_result: dict, final_response: dict, 
                   fallback_used: bool = False, original_tool: str = None):
    """Display the results in an organized format."""
    
    st.divider()
    st.subheader("📊 Results")
    
    # Show fallback notice if applicable
    if fallback_used and original_tool:
        st.warning(f"⚠️ Note: Originally tried {original_tool}, but fell back to web_search due to insufficient internal data.")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "💡 Answer",
        "🎯 Tool Selection",
        "📦 Retrieved Data",
        "ℹ️ Explanation"
    ])
    
    # Tab 1: Final Answer
    with tab1:
        st.markdown("### Final Answer")
        st.success(final_response["answer"])
    
    # Tab 2: Tool Selection
    with tab2:
        st.markdown("### Tool Selection")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Tool Selected", final_response["tool_used"])
        
        with col2:
            # Add emoji based on tool type
            tool_emojis = {
                "direct_answer": "💬",
                "vector_search": "📄",
                "graph_search": "🕸️",
                "web_search": "🌐"
            }
            emoji = tool_emojis.get(final_response["tool_used"], "🔧")
            st.markdown(f"### {emoji}")
        
        st.info(f"**Reason:** {plan_result['reason']}")
    
    # Tab 3: Retrieved Data
    with tab3:
        st.markdown("### Retrieved Data")
        
        if final_response["evidence"] is None:
            st.info("No external data was retrieved for this question.")
        else:
            st.json(final_response["evidence"])
        
        # Show raw execution result in expander
        with st.expander("View Raw Execution Result"):
            st.json(execution_result)
    
    # Tab 4: Explanation
    with tab4:
        st.markdown("### How This Answer Was Generated")
        st.write(final_response["explanation"])
        
        # Workflow summary
        st.markdown("#### Workflow Steps:")
        st.markdown(f"""
        1. **Planning**: Analyzed the question and selected initial tool
        2. **Execution**: Retrieved data from the chosen source
        3. **Validation**: Checked if results are useful (falls back to web if needed)
        4. **Response**: Generated a natural language answer based on the evidence
        
        Final tool used: `{final_response['tool_used']}`
        """)


def display_sidebar():
    """Display sidebar with additional information and examples."""
    
    with st.sidebar:
        st.header("📚 About")
        st.markdown("""
        This Agentic AI system uses three core components:
        
        1. **Planner**: Analyzes questions and selects the appropriate tool
        2. **Executor**: Retrieves data from the selected source
        3. **Responder**: Generates natural language answers
        """)
        
        st.divider()
        
        st.header("💡 Example Questions")
        
        examples = {
            "Direct Answer": [
                "Hi",
                "Hello",
                "What can you do?"
            ],
            "Graph Search (OpenAI Only)": [
                "Who is the CEO of OpenAI?",
                "Who is the President of OpenAI?",
                "Which products are built by OpenAI?"
            ],
            "Vector Search (OpenAI Docs)": [
                "What is OpenAI's mission?",
                "What is OpenAI?",
                "What does OpenAI do?",
                "Describe OpenAI's system architecture",
                "How does OpenAI use vector databases?"
            ],
            "Web Search (External/General)": [
                "Toyota",
                "What is Toyota",
                "NVIDIA",
                "Who is the CEO of Google?",
                "Who is the CEO of NVIDIA?",
                "Apple revenue",
                "Tesla cars",
                "Elon Musk",
                "What is machine learning?",
                "History of artificial intelligence",
                "Latest news about OpenAI"
            ]
        }
        
        for category, questions in examples.items():
            with st.expander(category):
                for i, q in enumerate(questions):
                    # Create unique key using category and index
                    category_prefix = category.split()[0].lower()  # "Direct", "Vector", "Graph", "Web"
                    if st.button(q, key=f"example_{category_prefix}_{i}", use_container_width=True):
                        st.session_state.question_input = q
                        st.rerun()


if __name__ == "__main__":
    # Display sidebar
    display_sidebar()
    
    # Run main app
    main()
