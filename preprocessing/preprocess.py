import os
import json
from llm import GoogleModel, ModelArguments
import time
from dotenv import load_dotenv

load_dotenv()

curr_dir = os.path.dirname(os.path.abspath(__file__))
model = GoogleModel(ModelArguments(model_name="models/gemini-2.0-flash-lite"))

def dependency_extraction(api1: dict, api2: dict, curr_time: str) -> list[str]:
    """
    Extract the dependencies between the two APIs.
    """
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)

    while True:
        # Reasoning
        with open(os.path.join(curr_dir, "docs", "prompts", f"relation_reasoning_system_prompt.txt"), "r") as f:
            dependency_reasoning_system_prompt = f.read()
        with open(os.path.join(curr_dir, "docs", "prompts", f"relation_reasoning_user_prompt.txt"), "r") as f:
            dependency_reasoning_user_prompt = f.read()
        user_prompt = dependency_reasoning_user_prompt\
            .replace('{id1}', str(api1["id"]))\
            .replace('{id2}', str(api2["id"]))\
            .replace('{api1}', f"{str(api1['method'])} {str(api1['endpoint'])}")\
            .replace('{api2}', f"{str(api2['method'])} {str(api2['endpoint'])}")\
            .replace('{api_documentation}', json.dumps(api_documentation, indent=4))
        print(user_prompt)
        response = model.query(dependency_reasoning_system_prompt, user_prompt)

        # with open(os.path.join(curr_dir, "docs", "llm_logs", f"relation_reasoning_{curr_time}.txt"), "a") as f:
        #     f.write(f"User Prompt: {user_prompt}\n")
        #     f.write(f"Response: {response}\n\n")

        # Decision
        with open(os.path.join(curr_dir, "docs", "prompts", f"relation_system_prompt.txt"), "r") as f:
            dependency_system_prompt = f.read()
        with open(os.path.join(curr_dir, "docs", "prompts", f"relation_user_prompt.txt"), "r") as f:
            dependency_user_prompt = f.read()

        user_prompt = dependency_user_prompt\
            .replace('{id1}', str(api1["id"]))\
            .replace('{id2}', str(api2["id"]))\
            .replace('{api1}', json.dumps(api1, indent=4))\
            .replace('{api2}', json.dumps(api2, indent=4))\
            .replace('{reasoning_text}', response)
        print(user_prompt)
        response = model.query(dependency_system_prompt, user_prompt)

        # with open(os.path.join(curr_dir, "docs", "llm_logs", f"relation_decision_{curr_time}.txt"), "a") as f:
        #     f.write(f"User Prompt: {user_prompt}\n")
        #     f.write(f"Response: {response}\n\n")

        if response is None:
            return None
        print(response)
        response = response.replace('```json', '').replace('```', '').strip()

        break
        #Verify
        # with open(os.path.join(curr_dir, "docs", "prompts", f"{dependency_type}_verify_user_prompt.txt"), "r") as f:
        #     dependency_verify_user_prompt = f.read()
        # user_prompt = dependency_verify_user_prompt\
        #     .replace('{reasoning}', response)\
        #     .replace('{json_output}', response)
        # verify_response = model.query(dependency_verify_user_prompt, user_prompt)
        # if verify_response is not None and bool(verify_response["relationshipValid"]):
        #     break

    return json.loads(response)

def dependency_collection() -> list[str]:
    """
    Collect the dependencies between the APIs.
    """
    curr_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)

    dependencies = {}
    for api1 in api_documentation["APIs"]:
        for api2 in api_documentation["APIs"]:
            if api1["id"] == api2["id"]:
                continue

            dependency = dependency_extraction(api1, api2, curr_time)
            if dependency is not None and bool(dependency["related"]):
                if api1["id"] not in dependencies:
                    dependencies[api1["id"]] = []
                dependencies[api1["id"]].append(dependency)
    
    with open(os.path.join(curr_dir, "docs", "output", f"relations_{curr_time}.json"), "w") as f:
        f.write(json.dumps(dependencies, indent=4))

def api_extraction() -> list[str]:
    """
    Extract the APIs from the API documentation.
    """
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)
    
    with open(os.path.join(curr_dir, "docs", "prompts", "api_extract_system_prompt.txt"), "r") as f:
        api_extract_system_prompt = f.read()
    
    with open(os.path.join(curr_dir, "docs", "prompts", "api_extract_user_prompt.txt"), "r") as f:
        api_extract_user_prompt = f.read()
    
    api_extracted = []
    for api in api_documentation["APIs"]:
        user_prompt = api_extract_user_prompt.replace('{api}', json.dumps(api, indent=4))
        system_prompt = api_extract_system_prompt
        response = model.query(system_prompt, user_prompt)
        if response is None:
            continue
        response = response[response.find('[Extracted JSON]') + len('[Extracted JSON]'):].replace('```json', '').replace('```', '').strip()
        response = json.loads(response)
        api_extracted.append(response)
    
    with open(os.path.join(curr_dir, "docs", "output", "api_extracted.json"), "w") as f:
        f.write(json.dumps(api_extracted, indent=4))

def bfs(api: str, graph2: dict[str, list[str]]) -> None:
    queue = [api]
    visited = set([api])
    while queue:
        top = queue.pop(0)
        for i in graph2[top]:
            if i not in visited:
                queue.append(i)
                visited.add(i)
    visited.remove(api)
    visited = list(visited)
    visited.sort()
    return visited

def graph_generation() -> dict[str, list[dict[str, str]]]:
    """
    Generate the graph from the API documentation.
    """
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)

    with open(os.path.join(curr_dir, "docs", "output", "relations_2025-06-01_13-38-34.json"), "r") as f:
        relations = json.load(f)
    
    graph = {}
    graph2 = {}
    for i, relation in enumerate(relations):
        relation = relations[str(i)]
        for r in relation:
            if r["related"]:
                api1 = r["relation"]["from"]
                api2 = r["relation"]["to"]
                if api1 not in graph:
                    graph[api1] = []
                    graph2[api1] = []
                graph[api1].append({
                    "api": api2,
                    "related_fields": r["fieldMappings"] if "fieldMappings" in r else []
                })
            graph2[api1].append(api2)
    
    # print(json.dumps(graph, indent=4))
    print(graph2)

    for i in api_documentation["APIs"]:
        print(f" {i['id']} -> {bfs(str(i['id']), graph2)}")

    return graph

if __name__ == "__main__":
    dependency_collection()
    # api_extraction()
    # graph_generation()