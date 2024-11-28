import json
import jsonref


def remove_unecessary_keys(dictionary, useless_keys):
    """
    since the original API Specification contains a ton of unnecessary metadata occupying
    valuable character count, we remove those extra fields
    """
    if isinstance(dictionary, dict):
        for key, value in list(dictionary.items()):
            if key in useless_keys:
                del dictionary[key]
            else:
                remove_unecessary_keys(value, useless_keys)
    elif isinstance(dictionary, list):
        for item in dictionary:
            remove_unecessary_keys(item, useless_keys)


def bucketer(API_Specification, threshold=2):
    """
    The following code buckets the paths in the API_Specification specification by path segment
    in order to have small json files that can be easily consumed
    """
    buckets = {}
    for path, methods in API_Specification["paths"].items():
        path_parts = path.split("/")
        path_parts = [
            s.split(":", 1)[0].lstrip("{").rstrip("}")
            + (":" + s.split(":", 1)[1] if ":" in s else "")
            for s in path_parts
        ]

        bucket_name = (
            "_".join(path_parts[3 : 3 + threshold])
            if len(path_parts) > 3
            else path_parts[3]
        )
        while bucket_name in buckets and len(buckets[bucket_name]) >= threshold:
            threshold += 1
            bucket_name = (
                "_".join(path_parts[3 : 3 + threshold])
                if len(path_parts) > 3
                else path_parts[3]
            )

        if bucket_name not in buckets:
            buckets[bucket_name] = {}

        buckets[bucket_name][path] = methods
    return buckets


def API_SpecificationParser():
    # import urllib.request

    # CDSW_ENDPOINT = ""
    # urllib.request.urlretrieve(
    #     f"{CDSW_ENDPOINT}/api/v2/API_Specification.json", "original_API_Specification.json"
    # )
    API_Specification = jsonref.load(
        open("original_API_Specification.json"), lazy_load=False, proxies=False, merge_props=True
    )
    # remove unnecessary ref definitions
    del API_Specification["definitions"]

    useless_keys = [
        "type",
        "in",
        "readOnly",
        "format",
        "responses",
        "operationId",
        "tags",
    ]
    remove_unecessary_keys(API_Specification, useless_keys)

    buckets = bucketer(API_Specification)
    metadata = {}

    # we need a metadata file that will allow for direct mapping of paths to relevant json file
    for bucket_name, paths in buckets.items():
        # set the initial data for manager metadata along with where the files are being stored
        for path in paths:
            metadata[path] = {}
            metadata[path]["methods"] = {}
            metadata[path]["file"] = f"{bucket_name}.json"

            for method in paths[path]:
                metadata[path]["methods"][method] = paths[path][method]["summary"]

        # populate the individual json files with api information
        json.dump(
            paths,
            open(f"agent_categorised_json/{bucket_name}.json", "w"),
            separators=(",", ":"),
        )

    # create the manager metadata
    json.dump(metadata, open("manager_metadata.json", "w"), separators=(",", ":"))


if __name__ == "__main__":
    API_SpecificationParser()
