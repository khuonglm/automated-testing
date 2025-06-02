import os
import json
from webtest import TestRequest

PATH = os.path.dirname(os.path.abspath(__file__))

def test_coverage(testapp):
    with open(os.path.join(PATH, "input.json"), "r") as f:
        apis = json.load(f)
    responses = []
    for api in apis:
        data = api["request"]
        endpoint = api["endpoint"]
        header = None
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
                        is_valid = False
                        break

                    from_data = from_data[field]
                
                assert to_fields[0] == "response"
                to_data = responses[int(to_fields[1][1:-1])].json
                for field in to_fields[2:]:
                    if field[0] == "[" and field[-1] == "]":
                        field = int(field[1:-1])
                    
                    if field not in to_data:
                        is_valid = False
                        break

                    to_data = to_data[field]
                
                if is_valid and from_fields[-1] in from_data:
                    from_data[from_fields[-1]] = to_data

        if "headers" in data:
            header = data["headers"]
            header["Authorization"] = "Token " + header["Authorization"]
        if "path_params" in data:
            for key, value in data["path_params"].items():
                endpoint = endpoint.replace(f"<{key}>", value)
        if "query_params" in data:
            for key, value in data["query_params"].items():
                endpoint = endpoint.replace(f"<{key}>", value)
        if "body" in data:
            req = TestRequest.blank(endpoint,
                              method = api["method"],
                              headers = header,
                              content_type='application/json')
            req.body = json.dumps(data["body"]).encode('utf-8')
            response = testapp.do_request(req, expect_errors=True)
        else:
            response = testapp.request(endpoint,
                                       method = api["method"],
                                       headers = header,
                                       expect_errors=True)

        responses.append(response)