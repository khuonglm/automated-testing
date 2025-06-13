import os
import json
from webtest import TestRequest

PATH = os.path.dirname(os.path.abspath(__file__))

def test_coverage(testapp):
    with open(os.path.join(PATH, "input.json"), "r") as f:
        apis = json.load(f)

    responses = []
    requests = []
    all = []
    for api in apis:
        data = api["request"]
        endpoint = api["endpoint"]
        if "replaces" in data:
            for key, value in data["replaces"].items():
                from_fields = key.split(".")
                to_fields = value.split(".")
                from_data = data
                is_valid = True
                for field in from_fields[:-1]:
                    if field[0] == "[" and field[-1] == "]":
                        field = int(field[1:-1])
                    
                    if field not in from_data:
                        from_data[field] = {}

                    from_data = from_data[field]
                
                if to_fields[0] == "response":
                    if 'application/json' in responses[int(to_fields[1][1:-1])].headers.get('Content-Type', ''):
                        to_data = responses[int(to_fields[1][1:-1])].json
                    else:
                        continue
                else:
                    to_data = requests[int(to_fields[1][1:-1])]
                
                # print(from_fields, to_fields, is_valid, to_data)

                for field in to_fields[2 + (to_fields[0] == "response"):]:
                    if field[0] == "[" and field[-1] == "]":
                        field = int(field[1:-1])
                        if field >= len(to_data):
                            is_valid = False
                            break
                        to_data = to_data[field]
                        continue
                    
                    if field not in to_data:
                        is_valid = False
                        break

                    to_data = to_data[field]

                # print(to_data)

                if is_valid:
                    from_data[from_fields[-1]] = to_data

        if "header" in data and "Authorization" in data["header"] and not data["header"]["Authorization"].startswith("Token "):
            data["header"]["Authorization"] = "Token " + data["header"]["Authorization"]

        # build endpoint
        for key, value in data["path"].items():
            endpoint = endpoint.replace(f"<{key}>", str(value))
        
        if data["query"]:
            endpoint += "?" + "&".join(f"{k}={v}" for k, v in data["query"].items())

        requests.append({
            "endpoint": endpoint,
            "header": data["header"],
            "body": data["body"],
            "query": data["query"],
            "path": data["path"]
        })

        # print(endpoint)
        if "body" in data:
            req = TestRequest.blank(endpoint,
                              method = api["method"],
                              headers = data["header"],
                              content_type='application/json')
            req.body = json.dumps(data["body"]).encode('utf-8')
            response = testapp.do_request(req, expect_errors=True)
        else:
            response = testapp.request(endpoint,
                                       method = api["method"],
                                       headers = data["header"],
                                       expect_errors=True)

        responses.append(response)
        all.append({"request": requests[-1], "response": response.json\
                    if 'application/json' in response.headers.get('Content-Type', '') else response.text})

    with open(os.path.join(PATH, "input_fuzzed.json"), "w") as f:
        json.dump(all, f, indent=4)

    # assert 0
