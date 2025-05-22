import os
import json
from llm import GoogleModel, ModelArguments
from dotenv import load_dotenv

load_dotenv()

curr_dir = os.path.dirname(os.path.abspath(__file__))
model = GoogleModel(ModelArguments(model_name="models/gemini-2.0-flash-lite"))

def dependency_extraction(api1: int, api2: int) -> list[str]:
    """
    Extract the dependencies between the two APIs.
    """
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)

    with open(os.path.join(curr_dir, "docs", "dependency_system_prompt.txt"), "r") as f:
        dependency_system_prompt = f.read()
    
    with open(os.path.join(curr_dir, "docs", "dependency_user_prompt.txt"), "r") as f:
        dependency_user_prompt = f.read()

    user_prompt = dependency_user_prompt\
        .replace('{id1}', str(api1))\
        .replace('{id2}', str(api2))\
        .replace('{api_documentation}', json.dumps(api_documentation, indent=4))
    system_prompt = dependency_system_prompt
    response = model.query(system_prompt, user_prompt)
    if response is None:
        return None
    response = response.replace('```json', '').replace('```', '').strip()
    return json.loads(response)

def dependency_collection() -> list[str]:
    """
    Collect the dependencies between the APIs.
    """
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)

    dependencies = {}
    for api1 in api_documentation["APIs"][0:7]:
        for api2 in api_documentation["APIs"][api1["id"]+1:7]:
            dependency = dependency_extraction(api1["id"], api2["id"])
            if dependency is not None and dependency["dependent"] == "yes":
                dependencies[api1["id"]] = dependency
    
    with open(os.path.join(curr_dir, "docs", "dependencies.json"), "w") as f:
        f.write(json.dumps(dependencies, indent=4))

def api_extraction() -> list[str]:
    """
    Extract the APIs from the API documentation.
    """
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)
    
    with open(os.path.join(curr_dir, "docs", "api_extract_system_prompt.txt"), "r") as f:
        api_extract_system_prompt = f.read()
    
    with open(os.path.join(curr_dir, "docs", "api_extract_user_prompt.txt"), "r") as f:
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
    
    with open(os.path.join(curr_dir, "docs", "api_extracted.json"), "w") as f:
        f.write(json.dumps(api_extracted, indent=4))

def graph_generation() -> dict[str, list[dict[str, str]]]:
    """
    Generate the graph from the API documentation.
    """
    with open(os.path.join(curr_dir, "docs", "api_documentation.json"), "r") as f:
        api_documentation = json.load(f)

    with open(os.path.join(curr_dir, "docs", "dependencies.json"), "r") as f:
        dependencies = json.load(f)
    
    graph = {}
    for i, dependency in enumerate(dependencies):
        dependency = dependencies[str(i)]
        if dependency["dependent"] == "yes":
            api1 = dependency["relation"].split(" ")[0]
            api2 = dependency["relation"].split(" ")[-1]
            if api1 not in graph:
                graph[api1] = []
            graph[api1].append({
                "api": api2,
                "related_fields": dependency["related fields"]
            })
    
    print(json.dumps(graph, indent=4))

    return graph

# if __name__ == "__main__":
    # dependency_collection()
    # api_extraction()
    # graph_generation()