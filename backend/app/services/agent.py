import json
import anthropic
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools import AgentTools
from app.core.config import settings


SYSTEM_PROMPT = """You are a Faculty Template Assistant, helping university faculty fill out recurring administrative documents (Word, Excel, PDF).

Your role is to:
1. Understand what document the user needs to fill out
2. Find the right template using search_templates
3. Get the template schema to understand required fields
4. Collect all required field values from the user (and auto-fill from faculty profile where possible)
5. For fields involving money, grades, dates tied to compliance, or personnel actions - always read back values for explicit confirmation
6. Use search_policy when a field's correct value depends on university policy language, and cite which policy chunk you used
7. Generate the filled document using fill_template

RULES:
- ALWAYS call search_templates first when the user describes a task, never guess a template id
- If more than one template plausibly matches, ask a clarifying question before proceeding
- Before calling fill_template, ALWAYS call get_template_schema and confirm you have every required field; ask the user for any missing ones rather than inventing values
- For fields involving money, grades, dates tied to compliance, or personnel actions, always read back the collected values to the user for explicit confirmation before calling fill_template
- Never generate document content as free text — all output must go through fill_template
- Use search_policy when a field's correct value depends on university policy language, and cite which policy chunk you used in your reply to the user
- Be conversational but efficient - ask one question at a time when collecting fields
- Auto-fill known fields from faculty profile (name, department, title, email, courses) when available

Available tools:
1. search_templates(query: str) -> ranked list of matching templates
2. search_policy(query: str, department: str | None) -> relevant policy chunks with citations
3. get_template_schema(template_id: str) -> required_fields JSON schema
4. fill_template(template_id: str, field_values: dict) -> generates filled file
5. get_faculty_profile(user_id: str) -> mock faculty data for auto-fill
"""


TOOL_DEFINITIONS = [
    {
        "name": "search_templates",
        "description": "Search for templates matching a query using vector similarity",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language description of the template needed"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_policy",
        "description": "Search university policy documents for relevant clauses",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Policy question or topic to search for"
                },
                "department": {
                    "type": "string",
                    "description": "Optional department to filter policies"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_template_schema",
        "description": "Get the required fields schema for a specific template",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "UUID of the template"
                }
            },
            "required": ["template_id"]
        }
    },
    {
        "name": "fill_template",
        "description": "Fill a template with provided field values and generate the document",
        "input_schema": {
            "type": "object",
            "properties": {
                "template_id": {
                    "type": "string",
                    "description": "UUID of the template"
                },
                "field_values": {
                    "type": "object",
                    "description": "Dictionary of field names to values"
                }
            },
            "required": ["template_id", "field_values"]
        }
    },
    {
        "name": "get_faculty_profile",
        "description": "Get faculty profile data for auto-filling common fields",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "UUID of the user"
                }
            },
            "required": ["user_id"]
        }
    }
]


class ChatAgent:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.tools = AgentTools(db)
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        self.conversation_history.append({"role": "user", "content": message})
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history
        
        while True:
            response = self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=self.conversation_history,
                tools=TOOL_DEFINITIONS,
            )
            
            if response.stop_reason == "tool_use":
                tool_results = []
                for content in response.content:
                    if content.type == "tool_use":
                        tool_result = await self._execute_tool(content.name, content.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": json.dumps(tool_result)
                        })
                
                self.conversation_history.append({"role": "assistant", "content": response.content})
                self.conversation_history.append({"role": "user", "content": tool_results})
                continue
            
            assistant_message = ""
            generated_file = None
            
            for content in response.content:
                if content.type == "text":
                    assistant_message += content.text
            
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return {
                "response": assistant_message,
                "generated_file": generated_file,
            }
    
    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "search_templates":
                return await self.tools.search_templates(args["query"])
            elif name == "search_policy":
                return await self.tools.search_policy(args["query"], args.get("department"))
            elif name == "get_template_schema":
                return await self.tools.get_template_schema(args["template_id"])
            elif name == "fill_template":
                return await self.tools.fill_template(args["template_id"], args["field_values"])
            elif name == "get_faculty_profile":
                profile = await self.tools.get_faculty_profile(args["user_id"])
                return profile.model_dump() if profile else None
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}