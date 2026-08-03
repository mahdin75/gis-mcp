# Build Your First GIS AI Agent - From Zero to Hero

Welcome! This tutorial will guide you from complete beginner to creating your own AI agent that can perform geospatial operations. No prior experience needed - we'll cover everything step by step.

📖 **[View the complete documentation →](https://gis-mcp.com/gis-ai-agent/langchain/basic-geospatial-agent/)**

## 📋 Table of Contents

- [What You'll Build](#what-youll-build)
- [Prerequisites](#prerequisites)
- [Step 1: Install GIS MCP Server](#step-1-install-gis-mcp-server)
- [Step 2: Install Agent Dependencies](#step-2-install-agent-dependencies)
- [Step 3: Get Your OpenRouter API Key](#step-3-get-your-openrouter-api-key)
- [Step 4: Configure Your Environment](#step-4-configure-your-environment)
- [Step 5: Start the MCP Server](#step-5-start-the-mcp-server)
- [Step 6: Create Your Agent](#step-6-create-your-agent)
- [Step 7: Run Your Agent](#step-7-run-your-agent)
- [Step 8: Test Your Agent](#step-8-test-your-agent)
- [Architecture Overview](#architecture-overview)
- [Troubleshooting](#troubleshooting)
- [Customization](#customization)
- [Next Steps](#next-steps)

## What You'll Build

By the end of this tutorial, you'll have:

- ✅ A working GIS MCP server running locally
- ✅ Your own AI agent built with LangChain
- ✅ An agent that can perform geospatial operations like:
  - Calculate distances between points
  - Transform coordinates between different systems
  - Create buffers around locations
  - Perform spatial analysis
  - And much more!

## Prerequisites

Before we start, make sure you have:

- **Python 3.10 or higher** installed ([Download Python](https://www.python.org/downloads/))
- **A code editor** (VS Code, PyCharm, or any text editor)
- **An internet connection** for installing packages
- **Basic command line knowledge** (we'll guide you through everything)

That's it! No prior AI or GIS experience needed.

---

## Step 1: Install GIS MCP Server

The GIS MCP Server provides all the geospatial tools your agent will use. Let's install it.

- Python 3.10 or higher
- Virtual environment (recommended)
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))
- GIS MCP server installed and running

1. **Open your terminal/command prompt**

   - **Windows**: Press `Win + R`, type `cmd` or `powershell`, press Enter
   - **Mac/Linux**: Open Terminal

2. **Create a project folder** (optional but recommended):

   ```bash
   mkdir gis-agent-project
   cd gis-agent-project
   ```

3. **Create a virtual environment** (keeps packages organized):

   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Mac/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   You should see `(.venv)` at the start of your command line.

4. **Install GIS MCP Server**:

   ```bash
   pip install gis-mcp
   ```

   Wait for the installation to complete. This may take a few minutes.

**✅ Verification**: Test that it's installed:

```bash
gis-mcp --help
```

You should see help text. If you get an error, make sure your virtual environment is activated.

---

## Step 2: Install Agent Dependencies

Now let's install the packages needed to build your agent with LangChain.

1. **Create a requirements file** (or install directly):

   Create a file named `requirements.txt` in your project folder with this content:

   ```
   langchain>=1.0.0
   langchain-openai>=1.0.0
   langchain-core>=1.0.0
   langchain-mcp-adapters>=0.1.0
   python-dotenv>=1.0.0
   ```

2. **Install the dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   Or install them one by one:

   ```bash
   pip install langchain langchain-openai langchain-core langchain-mcp-adapters python-dotenv
   ```

**✅ Verification**: Check that LangChain is installed:

```bash
python -c "import langchain; print('LangChain installed successfully!')"
```

---

## Step 3: Get Your OpenRouter API Key

OpenRouter is a service that gives you access to many AI models (including DeepSeek, Gemini, GPT-4, Claude, etc.) through a single API. This is perfect for our agent!

### Create an OpenRouter Account

1. **Visit** [https://openrouter.ai](https://openrouter.ai)
2. **Click "Sign Up"** (or "Log In" if you have an account)
3. **Create your account** (you can use Google/GitHub to sign up quickly)

### Get Your API Key

1. **Navigate to API Keys**:

   - Click your profile icon (top right)
   - Select "Keys" or go directly to [https://openrouter.ai/keys](https://openrouter.ai/keys)

2. **Create a new key**:

   - Click "Create Key"
   - Give it a name (e.g., "GIS Agent")
   - Optionally set a credit limit (you can leave it unlimited)
   - Click "Create"

3. **Copy your API key**:
   - Click the copy icon next to your key
   - **Save it somewhere safe** - you'll need it in the next steps
   - ⚠️ **Never share your API key publicly!**

---

## Step 4: Configure Your Environment

### Set Up Your API Key

Create a `.env` file in your project root directory:

1. **Create the file**: In your project folder, create a new file named `.env` (no extension)

2. **Add your API key**: Open the `.env` file and add:

   ```env
   OPENROUTER_API_KEY=your_api_key_here
   ```

   Replace `your_api_key_here` with the API key you copied from OpenRouter.

**✅ Verification**: Make sure the file is saved in the same directory as your project.

---

## Step 5: Start the MCP Server

The MCP server needs to be running for your agent to use GIS tools. Let's start it in HTTP mode.

**⚠️ Important**: Open a **new terminal window** (keep your current one open too - you'll need both):

### Windows (PowerShell)

```powershell
# Navigate to your project folder
cd gis-agent-project

# Activate your virtual environment
.\.venv\Scripts\Activate.ps1

# Set environment variables
$env:GIS_MCP_TRANSPORT="http"
$env:GIS_MCP_HOST="localhost"
$env:GIS_MCP_PORT="9010"

# Start the server
gis-mcp
```

### Windows (Command Prompt)

```cmd
cd gis-agent-project
.\.venv\Scripts\activate
set GIS_MCP_TRANSPORT=http
set GIS_MCP_HOST=localhost
set GIS_MCP_PORT=9010
gis-mcp
```

### Mac/Linux

```bash
cd gis-agent-project
source .venv/bin/activate
export GIS_MCP_TRANSPORT=http
export GIS_MCP_HOST=localhost
export GIS_MCP_PORT=9010
gis-mcp
```

**✅ You should see**:

```
Starting GIS MCP server with http transport on 0.0.0.0:9010
MCP endpoint will be available at: http://0.0.0.0:9010/mcp
```

**⚠️ Important**: Keep this terminal window open! The server needs to keep running. You'll use your other terminal for the next steps.

**✅ Verification**: If you see the messages above, your server is running correctly! The server is now ready to accept connections.

---

## Step 6: Create Your Agent

Now the fun part! Let's create your agent file.

1. **Create the agent file:**

   Save the following code to a file named `my_gis_agent.py` in your project directory:

   ```python
   """
   GIS Agent Implementation

   A LangChain-based agent that connects to the GIS MCP server
   via MultiServerMCPClient to provide geospatial analysis capabilities.
   """

   import os
   import asyncio
   from typing import Optional, List, Any
   from dotenv import load_dotenv
   from langchain_openai import ChatOpenAI
   from langchain.agents import create_agent
   from langchain_core.messages import AIMessage
   from langchain_mcp_adapters.client import MultiServerMCPClient

   # Load environment variables from .env file
   load_dotenv()

   # Configuration constants
   OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
   MCP_SERVER_URL: str = "http://localhost:9010/mcp"
   MODEL_NAME: str = "deepseek/deepseek-chat-v3.1"
   OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
   DEFAULT_TEMPERATURE: float = 0.7

   # System prompt for the agent
   SYSTEM_PROMPT: str = (
       "You are a helpful GIS assistant. You have access to various GIS tools "
       "through the MCP server. Use these tools to help users with geospatial "
       "operations. Always provide clear and accurate responses based on the tool results."
   )


   def initialize_language_model() -> ChatOpenAI:
       """Initialize and configure the language model using OpenRouter."""
       return ChatOpenAI(
           model=MODEL_NAME,
           api_key=OPENROUTER_API_KEY,
           base_url=OPENROUTER_BASE_URL,
           temperature=DEFAULT_TEMPERATURE,
       )


   def initialize_mcp_client() -> MultiServerMCPClient:
       """Initialize the MultiServerMCPClient for connecting to the GIS MCP server."""
       return MultiServerMCPClient(
           {
               "gis": {
                   "transport": "streamable_http",
                   "url": MCP_SERVER_URL,
               }
           }
       )


   async def load_gis_tools(client: MultiServerMCPClient) -> Optional[List[Any]]:
       """Load available GIS tools from the MCP server."""
       try:
           tools = await client.get_tools()
           return tools if tools else None
       except Exception:
           return None


   def extract_agent_response(result: dict) -> str:
       """Extract the AI response message from the agent result."""
       messages = result.get("messages", [])
       for msg in reversed(messages):
           if isinstance(msg, AIMessage):
               return msg.content
       return str(messages[-1]) if messages else "No response generated"


   async def run_interactive_session(agent: Any) -> None:
       """Run the interactive agent session loop."""
       while True:
           try:
               query = input("You: ").strip()
               if query.lower() in ["exit", "quit", "q"]:
                   break
               if not query:
                   continue

               result = await agent.ainvoke({
                   "messages": [{"role": "user", "content": query}]
               })

               response_text = extract_agent_response(result)
               print(f"Agent: {response_text}\n")

           except KeyboardInterrupt:
               break
           except Exception as e:
               print(f"Error: {e}\n")


   async def main() -> None:
       """Main entry point for the GIS agent application."""
       if not OPENROUTER_API_KEY:
           print("Error: OPENROUTER_API_KEY is not set.")
           return

       # Initialize language model
       llm = initialize_language_model()

       # Initialize MCP client
       client = initialize_mcp_client()

       # Load GIS tools from MCP server
       tools = await load_gis_tools(client)
       if tools is None:
           print("Error: Failed to load tools from MCP server.")
           return

       # Create agent with loaded tools
       agent = create_agent(
           model=llm,
           tools=tools,
           system_prompt=SYSTEM_PROMPT
       )

       # Run interactive session
       await run_interactive_session(agent)


   if __name__ == "__main__":
       asyncio.run(main())
   ```

   Save the following code to a file named `my_gis_agent.py` in your project directory.

2. **Save the file** as `my_gis_agent.py`

**🎉 Congratulations!** You just created your first GIS agent!

---

## Step 7: Run Your Agent

1. **Make sure**:

   - Your MCP server is still running (Step 5)
   - Your `.env` file is in the project directory (Step 4)

2. **In your original terminal** (not the server terminal), run:

   ```bash
   python my_gis_agent.py
   ```

3. **You should see**:
   - The agent initializing
   - Connection to the MCP server
   - Tools being loaded
   - "GIS Agent is ready" message

---

## Step 8: Test Your Agent

Now let's test it with some real GIS queries!

### Try These Queries

1. **"What GIS operations can you help me with?"**

   - This will show you what tools are available

2. **"Calculate the distance between points (0, 0) and (1, 1) in WGS84"**

   - Tests coordinate calculations

3. **"Transform point (0, 30) from WGS84 to Mercator projection"**

   - Tests coordinate transformation

4. **"Create a 1km buffer around point (lat: 0, lon: 30)"**

   - Tests geometric operations

5. **"What is the area of a polygon with coordinates [(0,0), (1,0), (1,1), (0,1), (0,0)]?"**
   - Tests area calculations

### What to Expect

- The agent will think about your query
- It will automatically select and use the appropriate GIS tools
- You'll see the agent's response with calculation results
- The agent will provide clear and accurate answers

**💡 Tip**: Watch the terminal output - you'll see the agent working through your queries!

### Exit the Agent

- Type `exit`, `quit`, or `q` to stop
- Or press `Ctrl+C`

---

## Architecture Overview

### Components

1. **Language Model (LLM)**

   - Configured via `ChatOpenAI` with OpenRouter base URL
   - Handles natural language understanding and generation

2. **MCP Client**

   - `MultiServerMCPClient` manages connection to GIS MCP server
   - Uses `streamable_http` transport for HTTP-based communication
   - Lazy connection: connects only when tools are requested

3. **Agent**

   - LangChain agent created with `create_agent()`
   - Integrates LLM with MCP tools
   - Handles tool selection and execution automatically

4. **Tool Integration**
   - Tools are automatically discovered from MCP server
   - Converted to LangChain-compatible format
   - Made available to the agent for execution

### Code Structure

```python
# Configuration
- Environment variable loading
- API key validation
- Server URL configuration

# Initialization
- Language model setup
- MCP client creation
- Tool loading from server

# Agent Creation
- Agent instantiation with tools
- System prompt configuration

# Interactive Session
- User input handling
- Agent invocation
- Response extraction and display
```

## Troubleshooting

### "OPENROUTER_API_KEY is not set"

**Solution:** Ensure the API key is set in your `.env` file or as an environment variable:

```bash
# Check if set
echo $OPENROUTER_API_KEY  # Mac/Linux
echo %OPENROUTER_API_KEY%  # Windows CMD
echo $env:OPENROUTER_API_KEY  # Windows PowerShell
```

### "Failed to connect to GIS MCP server"

**Symptoms:**

- Connection errors when starting the agent
- "No tools found" message

**Solutions:**

1. **Verify server is running:**

   - Check the server terminal window
   - Server should show: "Starting GIS MCP server with http transport on localhost:9010"

2. **Check server URL:**

   - Default: `http://localhost:9010/mcp`
   - Verify port matches in both server and agent configuration

3. **Test server connection:**

   ```bash
   curl http://localhost:9010/mcp/tools/list
   ```

   Should return a JSON list of available tools

4. **Verify environment variables:**
   - Server must have `GIS_MCP_TRANSPORT=http`
   - Server must have `GIS_MCP_PORT=9010`

### "No tools found"

**Possible causes:**

- Server not running
- Wrong port configuration
- Server not in HTTP transport mode

**Solution:**

- Restart server with correct environment variables
- Verify server is accessible at the configured URL

### Import Errors

**Solution:** Install all required dependencies:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install langchain langchain-openai langchain-core langchain-mcp-adapters python-dotenv
```

### Agent Not Using Tools

**Possible reasons:**

- Query doesn't require GIS operations
- Tools not loaded successfully
- Model not recognizing when to use tools

**Solutions:**

- Use more specific queries (e.g., "Calculate distance...", "Transform coordinates...")
- Verify tools were loaded (check startup messages)
- Try different models if tool usage is inconsistent

## Customization

### Change System Prompt

Edit the `SYSTEM_PROMPT` constant in `my_gis_agent.py`:

```python
SYSTEM_PROMPT: str = (
    "You are an expert geospatial analyst. "
    "Provide detailed explanations of all calculations. "
    "Always verify results using appropriate GIS tools."
)
```

### Adjust Temperature

Modify the `DEFAULT_TEMPERATURE` constant:

```python
DEFAULT_TEMPERATURE: float = 0.7  # Range: 0.0-2.0
# Lower = more focused/deterministic
# Higher = more creative/varied
```

### Change Server Configuration

Modify the `MCP_SERVER_URL` constant:

```python
MCP_SERVER_URL: str = "http://localhost:9010/mcp"
```

Ensure the server is configured to match this URL.

## Dependencies

See `requirements.txt` for complete dependency list:

- `langchain>=1.0.0` - Agent framework
- `langchain-openai>=1.0.0` - OpenAI-compatible API support
- `langchain-core>=1.0.0` - Core LangChain functionality
- `langchain-mcp-adapters>=0.1.0` - MCP server integration
- `python-dotenv>=1.0.0` - Environment variable management

## Documentation

- **LangChain MCP Documentation**: [https://docs.langchain.com/oss/python/langchain/mcp](https://docs.langchain.com/oss/python/langchain/mcp)
- **OpenRouter API**: [https://openrouter.ai/docs](https://openrouter.ai/docs)
- **OpenRouter Models**: [https://openrouter.ai/models](https://openrouter.ai/models)
- **GIS MCP Server**: See main project README for available tools

## License

See main project LICENSE file.

## Next Steps

Congratulations! You've built a working GIS agent. Here's what you can do next:

### 1. Explore More Models

Try different models on OpenRouter:

- `google/gemini-2.0-flash-exp` - Fast Gemini model
- `anthropic/claude-3.5-sonnet` - Great reasoning
- `openai/gpt-4o` - Most capable

Edit `MODEL_NAME` in `my_gis_agent.py` to switch models.

### 2. Customize Your Agent

- Change the system prompt to make your agent specialized
- Adjust temperature for different response styles
- Add more features like conversation history

### 3. Learn More

- **LangChain Documentation**: [https://python.langchain.com](https://python.langchain.com)
- **OpenRouter Models**: [https://openrouter.ai/models](https://openrouter.ai/models)
- **GIS MCP Server**: Check the main project README for all available tools

### 4. Share Your Agent

- Add it to your portfolio
- Share on GitHub
- Contribute improvements back to the project

---

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review code comments in `my_gis_agent.py`
3. Consult LangChain and OpenRouter documentation
4. Check GIS MCP server documentation for available tools

**You're now ready to build amazing geospatial AI applications!** 🚀
