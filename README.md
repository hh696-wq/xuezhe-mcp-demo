# Xuezhe MCP Demo

Academic Intelligence Tools for AI Agents (MCP)

A simple demo client for the **Xuezhe MCP Server**, providing academic intelligence capabilities such as:

- Scholar Search
- Expert Discovery
- Institution Ranking
- Talent Mobility
- Research Intelligence

This project demonstrates how AI agents and applications can interact with an MCP server to access structured academic data.

---

## MCP Endpoint

https://mcp.xuezhe.pro/mcp

Authentication header:

X-API-Key: your_api_key

---

## Features

### Scholar Intelligence

- scholar_search
- scholar_detail

Search global researchers by:

- name
- institution
- country

---

### Expert Discovery

- talent_discovery
- talent_future_star
- talent_doctor

Find experts and rising researchers by research topic.

---

### Institution Intelligence

- institution_ranking
- institution_growth
- institution_domain_structure

Analyze global universities, research institutes, and corporate research labs.

---

### Talent Intelligence

- talent_mobility

Track researcher movement between institutions and countries.

---

### Research Intelligence

- expert_map
- corporate_intel
- national_tech_structure

Understand global research ecosystems.

---

## Installation

Clone the repository:

git clone https://github.com/hh696-wq/xuezhe-mcp-demo.git
cd xuezhe-mcp-demo

Install dependencies:

pip install -r requirements.txt

---

## Quick Start

Run the demo:

python mcp_demo.py --api-key YOUR_API_KEY --run-examples

---

## Example Usage

List available tools:

python mcp_demo.py --api-key YOUR_API_KEY --list-tools

Call a tool:

python mcp_demo.py --api-key YOUR_API_KEY --tool institution_ranking --args '{"mode":"global","limit":5}'

---

## Example Tools

Current MCP tools include:

scholar_search
scholar_detail
talent_discovery
talent_mobility
talent_doctor
talent_future_star
expert_map
corporate_intel
institution_ranking
institution_growth
institution_domain_structure
national_tech_structure

---

## MCP Session Flow

The demo follows the standard MCP workflow:

1. initialize
2. notifications/initialized
3. tools/list
4. tools/call

---

## Example Use Cases

This MCP server enables AI agents to:

- discover global research experts
- analyze institutional research capabilities
- identify rising scientific talent
- understand global research trends

---

## License

MIT

