"""
gizmo.response

This module defines parsers for the Gremlin Server response.
"""

class GremlinResponse(list):
    def __init__(self, message):
        """
        A subclass of list that parses and flattens the Gremlin Server's
        response a bit. Make standard usecase easier for end user to process.

        :param message: Message from Gremlin Server.
        """
        super().__init__()
        data = message["result"].get("data", "")
        if data:
            for datum in data:
                if isinstance(datum, dict):
                    try:
                        datum = parse_struct(datum)
                    except (KeyError, IndexError):
                        pass
                self.append(datum)
        self.meta = message["result"]["meta"]
        self.request_id = message["requestId"]
        self.status_code = message["status"]["code"]
        self.message = message["status"]["message"]
        self.attrs = message["status"]["attributes"]


def parse_struct(struct):
    """
    Flatten out Gremlin Vertex and Edges a bit.

    :param struct: Vertex or Edge.
    :return: dict
    """
    output = {}
    for k, v in struct.items():
        if k != "properties":
            output[k] = v
    # TODO - Make sure no info is being lost here.
    properties = {k: [val["value"] for val in v] for (k, v) in
        struct["properties"].items()}
    output.update(properties)
    return output
