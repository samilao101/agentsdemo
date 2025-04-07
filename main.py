import requests
import json

# Replace with your actual OpenAI API key
OPENAI_API_KEY = ""

# --- Safe math expression evaluator (very basic) ---
def safe_calculate(expr):
    # Very basic calculator supporting + - * / and parentheses
    # No variables, no functions, just numbers and ops
    allowed_chars = "0123456789+-*/(). "
    if any(c not in allowed_chars for c in expr):
        raise ValueError("Unsafe characters in expression")
    try:
        return str(eval(expr, {"__builtins__": None}, {}))  # Still risky, sandboxed a bit
    except Exception as e:
        return f"Error in calculation: {e}"

# --- Wikipedia summary using requests ---
def search_wikipedia(query):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get("extract", "No summary found.")
    else:
        return f"Wikipedia lookup failed for: {query}"

# --- Define OpenAI functions spec ---
functions = [
    {
        "name": "search_wikipedia",
        "description": "Searches Wikipedia for a summary of the given query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The term to search on Wikipedia"
                }
            },
            "required": ["query"]
        },
    },
    {
        "name": "calculate_expression",
        "description": "Calculates a mathematical expression safely.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to calculate"
                }
            },
            "required": ["expression"]
        },
    },
]

# --- Function dispatcher ---
def call_function(name, arguments):
    args = json.loads(arguments)
    if name == "search_wikipedia":
        return search_wikipedia(args["query"])
    elif name == "calculate_expression":
        return safe_calculate(args["expression"])
    else:
        return "Unknown function."

# --- Query the OpenAI API with function calling ---
def query_agent(question):
    messages = [{"role": "user", "content": question}]

    while True:
        payload = {
            "model": "gpt-3.5-turbo-0613",
            "messages": messages,
            "functions": functions,
            "function_call": "auto"
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        res = requests.post("https://api.openai.com/v1/chat/completions",
                            headers=headers, data=json.dumps(payload))
        res_json = res.json()
        message = res_json["choices"][0]["message"]

        if "function_call" in message:
            fn = message["function_call"]["name"]
            args = message["function_call"]["arguments"]
            print(f"\n🔧 Calling function: {fn} with args: {args}")

            result = call_function(fn, args)
            messages.append(message)
            messages.append({
                "role": "function",
                "name": fn,
                "content": result
            })
        else:
            return message["content"]

# --- Example usage ---
if __name__ == "__main__":
    questions = [
        "What countries border Germany?",
        "What is twelve multiplied by seventeen?",
        "Who was Ada Lovelace?",
        "What is (5 + 3) * 2 - 1?"
    ]

    for q in questions:
        print(f"\n❓ Question: {q}")
        answer = query_agent(q)
        print(f"✅ Answer: {answer}")