import itertools
import re


class Tags(object):
    Template = "_"
    Body = "body"
    Arguments = "arguments"


def value_at_path(data, path):
    current = data
    for k in path:
        if k not in path:
            raise KeyError("path {} is missing in data (at '{}' with data = {})".format(k, data))
        current = current[k]
    return current


def expand_str(s, store):
    new = str(s)
    replaced = set()
    while True:
        match = re.search(r"\{([^\}]+)\}", new)
        if not match:
            return new

        found = match.group(1)

        if found in replaced:
            raise RuntimeError("infinite argument substitution detected (with argument = '{}')".format(found))

        path = found.split(":")
        new = new.replace("{" + found + "}", str(value_at_path(store, path)))
        replaced.add(found)


def parse_dict(data, store):
    new = {}
    if len(data) == 1 and data.keys()[0] == Tags.Template:
        return build_template(data[Tags.Template], store)
    else:
        for k, v in data.iteritems():
            new[k] = parse(v, store)
    return new


def parse_str(data, store):
    return expand_str(str(data), store)


def parse_list(data, store):
    return [parse(item, store) for item in data]


def parse_any(data, _):
    return False, data


def handlers():
    return {
        dict: parse_dict,
        str: parse_str,
        list: parse_list
    }


def dict_product(dicts):
    return (dict(itertools.izip(dicts, x))
            for x in itertools.product(*dicts.itervalues()))


def build_template(data, store):
    is_simple_template = True
    arguments = data.get(Tags.Arguments, {})

    for k, values in arguments.iteritems():
        if k in store:
            raise KeyError(
                "template argument colision with lower-level template (argument = '{}' in template = {})".format(
                    k, data))

        if not isinstance(values, list):
            arguments[k] = [values]
        else:
            is_simple_template = False

    if Tags.Body not in data:
        raise ValueError("missing 'body' attribute in template (in template = {})".format(data))

    results = []
    for args_set in dict_product(arguments):
        args_set.update(store)
        results.append(parse(data[Tags.Body], args_set))

    if is_simple_template:
        assert len(results) == 1
        return results[0]

    return results


def get_handler(t):
    return handlers().get(t, parse_any)


def parse(data, store=None):
    if store is None:
        store = {}
    handler = handlers()[type(data)]
    return handler(data, store)
