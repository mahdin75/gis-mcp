# Build a GIS AI Agent with OpenAI-Nodejs

Welcome! This tutorial will guide you on setting up the gis-mcp server and building a Node.js agent that can perform geospatial operations.

**Related:** [OpenAI Node.js overview](README.md) · [Agent tutorials](../README.md) · [Architecture](../architecture.md) · [Best practices](../best-practices.md)

## 📋 Table of Contents

- [What You'll Build](#what-youll-build)
- [Prerequisites](#prerequisites)
- [Step 1: Install GIS MCP Server](#step-1-install-gis-mcp-server)
- [Step 2: Get Your OpenAI API Key](#step-2-get-your-openai-api-key)
- [Security Notice](#security-notice)
- [Step 3: Install Nodejs Dependencies](#step-3-install-nodejs-dependencies)
- [Step 4: Start the MCP Server](#step-4-start-the-mcp-server)
- [Step 5: Run the Agent Code](#step-5-run-the-agent-code)
- [Step 6: Next Steps](#step-6-next-steps)

## What You'll Build

By the end of this tutorial, you'll have:

- ✅ A working GIS MCP server running locally
- ✅ Your own AI agent built with OpenAI's Agent SDK in Node.js
- ✅ An agent that can perform geospatial operations like:
  - Calculate distances between points
  - Transform coordinates between different systems
  - Create buffers around locations
  - Perform spatial analysis
  - And much more!

## Prerequisites

Before we start, make sure you have:

- **Python 3.10 or higher** installed ([Download Python](https://www.python.org/downloads/))
- **Node.js v24.11.1 or higher** installed ([Download Node.js](https://nodejs.org/en/download))
- **A code editor** (VS Code, PyCharm, or any text editor)
- **An internet connection** for installing packages
- **Basic command line knowledge** (we'll guide you through everything)

---

## Step 1: Install GIS MCP Server

The GIS MCP Server provides all the geospatial tools your agent will use. Let's install it.

- Python 3.10 or higher
- Virtual environment (recommended)
- GIS MCP server installed and running

1. **Open your terminal/command prompt**

   - **Windows**: Press `Win + R`, type `cmd` or `powershell`, press Enter
   - **Mac/Linux**: Open Terminal

2. **Create a project folder** (optional but recommended):

   ```bash
   mkdir gis-node-js-project
   cd gis-node-js-project
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

## Step 2: Get Your OpenAI API Key

To let your Node.js agent talk to OpenAI, you'll need an API key. You can easily get one by using this link. [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

Once you have that, return to your project directory and create a file called `.env`.

Inside it, paste your key like this:

```
OPENAI_API_KEY=your_key_here
```

## Security Notice

Before you go any further, make sure your `.env` file is protected. This file contains your API key, and you should never commit it to GitHub or share it with anyone. The safest way to handle this is to add `.env` to your `.gitignore` file so it stays out of version control automatically. If your project doesn't have a `.gitignore` yet, create one in the project root and include `.env` inside it. Once that's in place, Git will ignore the file completely, and you won't have to worry about leaking secrets when you push your code.

## Step 3: Install Node.js Dependencies

In your folder, initialize a Node.js project:

```
npm init -y
```

Then install the Agent SDK and OpenAI package:

```
npm install @openai/agents openai dotenv
```

You are now ready to build your agent.

## Step 4: Start the MCP Server

The MCP server needs to be running for your agent to use GIS tools. Let's start it in HTTP mode.

**⚠️ Important**: Open a **new terminal window** (keep your current one open too - you'll need both):

### Windows (PowerShell)

```powershell
# Navigate to your project folder
cd gis-node-js-project

# Activate your virtual environment
.\.venv\Scripts\Activate.ps1

# Set environment variables
$env:GIS_MCP_TRANSPORT="http"
$env:GIS_MCP_HOST="localhost"
$env:GIS_MCP_PORT="9010"

# Start the server
gis-mcp
```

Keep the server window open while you work. The Node agent depends on this process running in the background, and if you close that terminal, the agent won't be able to reach the MCP server. Just leave it running and open a separate terminal when you switch to the Node.js part.

## Step 5: Run the Agent Code

Create a new file called `app.js` and paste the agent code into it:

```
import { Agent, MCPServerStreamableHttp, run } from "@openai/agents";
import { OpenAI } from "openai";
import dotenv from "dotenv";

/* load environment variables */
dotenv.config();
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

/* mcp server definition */
const mcpServer = new MCPServerStreamableHttp({
    url: 'http://localhost:9010/mcp',
    name: 'GIS MCP server'
});

/* agent definition */
const gisAgent = new Agent({
    client,
    name: 'GIS Agent',
    instructions: 'You must always use the MCP tools to answer GIS questions.',
    mcpServers: [mcpServer]
});

/* Perform a query */
await mcpServer.connect();

const result = await run(
    gisAgent,
    "Calculate distance between points (0,0) and (1,1)",
);

await mcpServer.close();

console.log(result.finalOutput);

```

Then run it:

```
node app.js
```

Your agent connects to the MCP server, discovers its available tools, and uses them to answer the geospatial question. The final computed answer appears in your terminal.

## Step 6: Next Steps

You can now experiment with more GIS operations such as coordinate transformations, buffering, area calculations, and more. The agent will use the MCP server for any question requiring geospatial logic.

You can embed this into your server, build a chat interface or extend MCP tools in Python. This structure is suitable for both micro-projects and large-scale applications.
