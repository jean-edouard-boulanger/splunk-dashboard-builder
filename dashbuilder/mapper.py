import xml.etree.ElementTree as ETtree


class Undefined(object):
    pass


def is_undefined(value):
    return type(value) is Undefined


def identity(value):
    return value


class GenericMapper(object):
    def __init__(self, source, dest, arity, default, factory):
        self.source = source
        self.dest = dest
        self.arity = arity
        self.default = default
        self.factory = factory

    def assign(self, root, value):
        pass

    def is_optional(self):
        return self.arity == '*' or self.arity == '?'

    def iterable_expected(self):
        return self.arity == '*' or self.arity == '+'

    def __call__(self, data, root):
        if self.source in data:
            if self.iterable_expected():
                items = data[self.source]
                if isinstance(items, list):
                    for item in items:
                        self.assign(root, self.factory(item))
                elif isinstance(items, dict):
                    for k, v in items.iteritems():
                        self.assign(root, self.factory((k, v)))
                else:
                    raise ValueError("""Expected iterable data (list or dict)
                        got '{}' instead (data = {})""".format(
                        type(data), data))
            else:
                self.assign(root, self.factory(data[self.source]))
            return

        if not is_undefined(self.default):
            self.assign(root, self.default)
            return

        if not self.is_optional():
            raise ValueError("Non-optional key '{}' not found in data".format(
                self.source))


class StaticAttributeMapper(object):
    def __init__(self, dest, value):
        self.dest = dest
        self.value = value

    def __call__(self, _, root):
        root.attrib[self.dest] = str(self.value)


class TextMapper(GenericMapper):
    def __init__(self, *args, **kwargs):
        super(TextMapper, self).__init__(*args, **kwargs)

    def assign(self, root, value):
        root.text = str(value)


class AttributeMapper(GenericMapper):
    def __init__(self, *args, **kwargs):
        super(AttributeMapper, self).__init__(*args, **kwargs)

    def assign(self, root, value):
        root.attrib[self.dest] = str(value)


class TextMemberMapper(GenericMapper):
    def __init__(self, *args, **kwargs):
        super(TextMemberMapper, self).__init__(*args, **kwargs)

    def assign(self, root, value):
        child = ETtree.SubElement(root, self.dest)
        child.text = str(value)


class MemberMapper(GenericMapper):
    def __init__(self, *args, **kwargs):
        super(MemberMapper, self).__init__(*args, **kwargs)

    def assign(self, root, child):
        if child is None:
            raise ValueError("Element must not be None")
        root.append(child)


class Mapper(object):
    def __init__(self):
        self.mappers = []
        self.input_data = None

    def add_attribute(self,
                      source,
                      dest=None,
                      arity='1',
                      default=Undefined(),
                      factory=identity):
        """
        """
        if dest is None:
            dest = source

        mapper = AttributeMapper(source, dest, arity, default, factory)
        self.mappers.append(mapper)

        return self

    def add_static_attribute(self, dest, value):
        mapper = StaticAttributeMapper(dest, value)
        self.mappers.append(mapper)
        return self

    def add_text(self,
                 source,
                 arity='1',
                 default=Undefined(),
                 factory=identity):
        """
        """
        dest = None
        mapper = TextMapper(source, dest, arity, default, factory)
        self.mappers.append(mapper)

        return self

    def add_text_member(self,
                        source,
                        dest=None,
                        arity='1',
                        default=Undefined(),
                        factory=identity):
        """
        """
        if dest is None:
            dest = source

        mapper = TextMemberMapper(source, dest, arity, default, factory)
        self.mappers.append(mapper)

        return self

    def add_member(self,
                   source,
                   arity='1',
                   default=Undefined(),
                   factory=identity):
        """
        """
        dest = None
        mapper = MemberMapper(source, dest, arity, default, factory)
        self.mappers.append(mapper)
        return self

    def clear(self):
        self.mappers = []

    def map(self, data):
        """
        """
        if not isinstance(data, dict):
            raise ValueError("mapping input should be a dict (input = {})".format(data))

        self.input_data = data
        return self

    def into(self, root):
        """
        """
        if self.input_data is None:
            return

        [mapper(self.input_data, root) for mapper in self.mappers]
