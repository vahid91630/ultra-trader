import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from infra.mongo_data_store import connect_to_mongodb
from services.llm_openai import get_openai_service
from services.gpt_cache import get_gpt_cache

st.set_page_config(page_title="Ultra Trader Dashboard", layout="wide")
st.title("📊 Ultra+ Trading Dashboard")

# Create tabs for different sections
tab1, tab2 = st.tabs(["📈 Trading Data", "🤖 GPT Analysis"])

with tab1:
    # Existing trading data functionality
    client = connect_to_mongodb()
    if client:
        dbname = os.getenv("MONGODB_URI").split("/")[-1].split("?")[0]
        df = pd.DataFrame(list(client[dbname]["signals"].find().sort("timestamp", -1).limit(100)))
        st.subheader("Latest Signals")
        st.dataframe(df)
        if "price" in df.columns and "timestamp" in df.columns:
            fig = px.line(df, x="timestamp", y="price", title="📉 Price History", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("🔒 Safe Mode: fallback data")
        fallback = pd.DataFrame([{"timestamp": i, "price": 30000 + i * 10} for i in range(50)])
        fig = px.line(fallback, x="timestamp", y="price", title="📉 Price (Fallback Mode)", markers=True)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    # GPT Analysis tab
    st.subheader("🤖 AI-Powered Market Analysis")
    
    # Initialize services
    openai_service = get_openai_service()
    gpt_cache = get_gpt_cache()
    
    # Check API key status
    config_status = openai_service.get_config_status()
    
    if not config_status["openai_installed"]:
        st.error("❌ OpenAI package not installed. Please install 'openai>=1.30.0' to use GPT features.")
        st.stop()
    
    if not config_status["has_api_key"]:
        st.warning("⚠️ OpenAI API Key Not Configured")
        st.markdown("""
        To use GPT analysis features, you need to set your OpenAI API key:
        
        **For Railway Deployment:**
        1. Go to your Railway project dashboard
        2. Navigate to Variables section
        3. Add the following environment variables:
           - `OPENAI_API_KEY`: Your OpenAI API key (required)
           - `OPENAI_MODEL`: Model to use (optional, default: gpt-4o-mini)
           - `OPENAI_TEMPERATURE`: Response creativity (optional, default: 0.7)
           - `OPENAI_MAX_TOKENS`: Max response length (optional, default: 2000)
           - `OPENAI_BASE_URL`: Custom endpoint (optional, for Azure/other)
        
        **For Local Development:**
        1. Create a `.env` file in your project root
        2. Add: `OPENAI_API_KEY=your_api_key_here`
        
        **Get an API Key:**
        Visit [OpenAI Platform](https://platform.openai.com/api-keys) to create an API key.
        """)
        st.stop()
    
    # Show configuration status
    with st.expander("🔧 Configuration Status"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Model:** {config_status['model']}")
            st.write(f"**Max Tokens:** {config_status['max_tokens']}")
            st.write(f"**Temperature:** {config_status['temperature']}")
        with col2:
            st.write(f"**Base URL:** {config_status['base_url'] or 'Default'}")
            cache_stats = gpt_cache.get_stats()
            st.write(f"**Cache Backend:** {'MongoDB' if cache_stats['use_mongo'] else 'Memory only'}")
            st.write(f"**Cached Responses:** {cache_stats.get('mongo_cache_size', cache_stats['memory_cache_size'])}")
    
    # Analysis interface
    st.markdown("---")
    
    # Template selection
    template_options = {
        "Custom Prompt": "",
        "Market Sentiment": "sentiment",
        "Signal Explanation": "explanation", 
        "Strategy Report": "strategy_report"
    }
    
    selected_template = st.selectbox(
        "📋 Choose Analysis Type:",
        options=list(template_options.keys()),
        index=0
    )
    
    # Context inputs
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("💰 Symbol (optional):", placeholder="BTC, ETH, etc.")
        timeframe = st.selectbox("📅 Timeframe:", ["1h", "4h", "1d", "1w"], index=2)
    
    with col2:
        include_recent_data = st.checkbox("📊 Include Recent Metrics", value=True)
        if include_recent_data and client:
            try:
                # Get recent data from database
                recent_signals = list(client[dbname]["signals"].find().sort("timestamp", -1).limit(5))
                if recent_signals:
                    st.success(f"✅ Found {len(recent_signals)} recent signals")
                else:
                    st.info("ℹ️ No recent signals found")
            except Exception as e:
                st.warning(f"⚠️ Could not fetch recent data: {e}")
                recent_signals = []
        else:
            recent_signals = []
    
    # Main prompt input
    if selected_template == "Custom Prompt":
        prompt = st.text_area(
            "✍️ Enter your question or analysis request:",
            height=100,
            placeholder="Ask anything about market analysis, trading strategies, or specific assets..."
        )
    else:
        # Load template content
        template_file = f"prompts/{template_options[selected_template]}.md"
        try:
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            st.markdown(f"**Using template:** {selected_template}")
            with st.expander("📝 View Template"):
                st.markdown(template_content)
            
            prompt = st.text_area(
                "📝 Provide context or data to analyze:",
                height=100,
                placeholder="Paste market news, price data, or describe the situation you want analyzed..."
            )
        except FileNotFoundError:
            st.error(f"Template file not found: {template_file}")
            st.stop()
    
    # Build context for analysis
    context_data = {}
    if symbol:
        context_data["symbol"] = symbol
    if timeframe:
        context_data["timeframe"] = timeframe
    if recent_signals:
        context_data["recent_signals"] = recent_signals[:3]  # Limit to avoid token overflow
    
    # Generate analysis button
    if st.button("🚀 Generate Analysis", type="primary"):
        if not prompt.strip():
            st.error("Please enter a prompt or context to analyze.")
        else:
            with st.spinner("🤖 Generating analysis..."):
                try:
                    # Check cache first
                    template_key = template_options[selected_template]
                    cached_response = gpt_cache.get(prompt, template_key, context_data)
                    
                    if cached_response:
                        st.info("♻️ Retrieved from cache")
                        response = cached_response
                    else:
                        # Prepare the full prompt
                        if selected_template != "Custom Prompt":
                            # Load system prompt
                            with open("prompts/system.md", 'r') as f:
                                system_prompt = f.read()
                            
                            # Combine template with user input and context
                            full_prompt = f"{template_content}\n\n"
                            if context_data:
                                full_prompt += f"**Context Data:**\n```json\n{json.dumps(context_data, indent=2, default=str)}\n```\n\n"
                            full_prompt += f"**User Input:**\n{prompt}"
                        else:
                            # For custom prompts, load system context
                            with open("prompts/system.md", 'r') as f:
                                system_prompt = f.read()
                            
                            full_prompt = prompt
                            if context_data:
                                full_prompt += f"\n\n**Context Data:**\n{json.dumps(context_data, indent=2, default=str)}"
                        
                        # Generate response
                        response = openai_service.chat(full_prompt, system_prompt)
                        
                        # Cache the response
                        gpt_cache.set(prompt, response, template_key, context_data)
                        
                        # Log request/response if MongoDB is available
                        if client:
                            try:
                                log_doc = {
                                    "timestamp": datetime.utcnow(),
                                    "template": selected_template,
                                    "symbol": symbol,
                                    "timeframe": timeframe,
                                    "prompt_length": len(prompt),
                                    "response_length": len(response),
                                    "cached": False,
                                    "model": config_status["model"]
                                }
                                client[dbname]["gpt_logs"].insert_one(log_doc)
                            except Exception as e:
                                st.warning(f"Could not log request: {e}")
                    
                    # Display response
                    st.markdown("### 📊 Analysis Result")
                    st.markdown(response)
                    
                    # Show metadata
                    with st.expander("ℹ️ Request Details"):
                        st.write(f"**Template:** {selected_template}")
                        st.write(f"**Model:** {config_status['model']}")
                        st.write(f"**Response Length:** {len(response)} characters")
                        if context_data:
                            st.write(f"**Context:** {list(context_data.keys())}")
                        st.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                except Exception as e:
                    st.error(f"❌ Error generating analysis: {str(e)}")
    
    # Usage tips
    with st.expander("💡 Usage Tips"):
        st.markdown("""
        **Cost & Rate Limits:**
        - Responses are cached to reduce API costs
        - Default model (gpt-4o-mini) is cost-effective for most analyses
        - Longer prompts and responses consume more tokens
        
        **Best Practices:**
        - Be specific about what you want to analyze
        - Include relevant market context or data
        - Use templates for consistent analysis structure
        - Review multiple perspectives before making trading decisions
        
        **Templates:**
        - **Market Sentiment**: Analyze news sentiment and market impact
        - **Signal Explanation**: Understand technical indicators and signals  
        - **Strategy Report**: Get comprehensive trading strategy analysis
        - **Custom Prompt**: Ask specific questions or request custom analysis
        """)
    
    # Cache management (admin section)
    if st.checkbox("🔧 Show Admin Controls"):
        st.markdown("**Cache Management:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Cache"):
                gpt_cache.clear()
                st.success("Cache cleared!")
        with col2:
            st.write(f"Cache Stats: {gpt_cache.get_stats()}")
