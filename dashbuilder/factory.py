import xml.etree.ElementTree as ETtree
from mapper import Mapper


class Tags(object):
    Dashboard = "dashboard"
    Form = "form"
    Table = "table"
    Option = "option"
    Html = "html"
    Search = "search"
    Chart = "chart"
    Event = "event"
    Map = "map"
    Single = "single"
    Checkbox = "checkbox"
    Dropdown = "dropdown"
    Link = "link"
    Multiselect = "multiselect"
    Radio = "radio"
    Text = "text"
    Time = "time"


def mappings():
    return {
        Tags.Dashboard: DashboardFactory,
        Tags.Form: FormFactory,
        Tags.Table: TableFactory,
        Tags.Html: HtmlFactory,
        Tags.Chart: ChartFactory,
        Tags.Time: TimeFactory,
        Tags.Event: EventFactory,
        Tags.Map: MapFactory,
        Tags.Single: SingleFactory,
        Tags.Checkbox: CheckboxFactory
    }


def infer_data_type(data):
    if not isinstance(data, dict):
        raise TypeError("""'data' argument must be a dict structure 
            (data = {})""".format(data))

    if len(data) != 1:
        raise ValueError("""'data' must have a single key 
            representing the data type (data = {})""".format(data))

    return data.keys()[0]


def strip_xml(elem):
    for elem in elem.iter():
        if elem.text:
            elem.text = elem.text.strip()
        if elem.tail:
            elem.tail = elem.tail.strip()


class Filterable(object):
    def __call__(self, factory):
        (factory.mapper
         .add_attribute("rejects", arity='?')
         .add_attribute("depends", arity='?'))


class Identifiable(object):
    def __call__(self, factory):
        (factory.mapper
         .add_attribute("id", arity='?'))


class Referenciable(object):
    def __call__(self, factory):
        (factory.mapper
         .add_attribute("ref", arity='?'))


class Titleable(object):
    def __call__(self, factory):
        (factory.mapper
         .add_text_member("title", arity='?'))


class Tokenizable(object):
    def __call__(self, factory):
        (factory.mapper
         .add_attribute("token", arity='?'))


class BaseFactory(object):
    def __init__(self):
        self.mapper = Mapper()

    def add_trait(self, *args):
        for flavour in args:
            flavour(self)
    
    def __call__(self, data):
        if self.__doc__ is None:
            raise RuntimeError("Factories not implementing __call__ must provide a docstring")

        obj = ETtree.Element(self.__doc__)
        self.mapper.map(data).into(obj)
        return obj


class Either(BaseFactory):
    def __init__(self, *args):
        super(Either, self).__init__()

        self.mapping = {}

        m = mappings()
        for t in args:
            if t not in m:
                raise KeyError("No factory defined for type '{}'".format(t))
            self.mapping[t] = m[t]

    def __call__(self, data, t=None):
        # If t is None, the data type is infered from the only key of the dict
        # Data must be of this form: { "the_object_type" : X }
        # Where 'X' is of any type.
        if t is None:
            t = infer_data_type(data)

            # The new value of data is data["the_object_type"], which will
            # be used to create the actual object.
            data = data[t]

        if t not in self.mapping:
            raise KeyError("""'{}' is not a valid choice
                (object must be of type: {})""".format(
                    t, ", ".join(self.mapping)))

        t_factory = self.mapping[t]()
        return t_factory(data)


class Wrap(BaseFactory):
    def __init__(self, factory, text):
        super(Wrap, self).__init__()
        self.factory = factory
        self.text = text

    def __call__(self, data):
        obj = ETtree.Element(self.text)
        obj.append(self.factory(data))
        return obj


class ListFormatter(object):
    def __call__(self, data):
        return ", ".join(data)


class KVFactory(BaseFactory):
    def __init__(self, t, k="name"):
        super(KVFactory, self).__init__()
        self.t = t
        self.k = k

        (self.mapper
             .add_attribute(k)
             .add_text("value"))

    def __call__(self, kv):
        key, value = kv
        data = {"name": key, "value": value}

        kv = ETtree.Element(self.t)
        self.mapper.map(data).into(kv)
        return kv


class SearchFactory(BaseFactory):
    """search"""
    def __init__(self):
        super(SearchFactory, self).__init__()
        (self.mapper
         .add_attribute("app", arity='?')
         .add_attribute("base", arity='?')
         .add_attribute("id", arity='?')
         .add_attribute("ref", arity='?')
         .add_text_member("cache", arity='?')
         .add_text_member("earliest", arity='?')
         .add_text_member("latest", arity='?')
         .add_text_member("query", arity='?')
         .add_text_member("refresh", arity='?')
         .add_text_member("refreshType", arity='?')
         .add_text_member("sampleRatio", arity='?'))


class InputFactory(BaseFactory):
    def __init__(self):
        super(InputFactory, self).__init__()
        self.add_trait(Identifiable(), Tokenizable(), Filterable())
        (self.mapper
         .add_static_attribute("type", self.__doc__)
         .add_attribute("searchWhenChanged", arity='?', default=True)
         .add_text_member("label", arity='?'))

    def __call__(self, data):
        obj = ETtree.Element("input")
        self.mapper.map(data).into(obj)
        return obj


class TimeFactory(InputFactory):
    """time"""
    def __init__(self):
        super(TimeFactory, self).__init__()
        (self.mapper
         .add_text_member("earliest", arity='?')
         .add_text_member("latest", arity='?'))


class CheckboxFactory(InputFactory):
    """checkbox"""
    def __init__(self):
        super(CheckboxFactory, self).__init__()
        (self.mapper
         .add_member("delimiter", arity='?')
         .add_member("prefix", arity='?')
         .add_member("suffix", arity='?')
         .add_member("valuePrefix", arity='?')
         .add_member("valueSuffic", arity='?')
         .add_member("choices",
                     arity='*',
                     factory=KVFactory("choice", "value")))


class VisualizationFactory(BaseFactory):
    def __init__(self):
        super(VisualizationFactory, self).__init__()
        self.add_trait(Filterable(), Identifiable(), Titleable())


class SearchBasedVisualizationFactory(VisualizationFactory):
    def __init__(self):
        super(SearchBasedVisualizationFactory, self).__init__()
        (self.mapper
         .add_member("options",
                     factory=KVFactory(Tags.Option),
                     arity='*')
         .add_member(Tags.Search,
                     factory=SearchFactory(),
                     arity='?'))


class ChartFactory(SearchBasedVisualizationFactory):
    """chart"""
    pass


class TableFactory(SearchBasedVisualizationFactory):
    """table"""
    def __init__(self):
        super(TableFactory, self).__init__()
        (self.mapper
             .add_text_member("fields", arity='?', factory=ListFormatter()))


class EventFactory(SearchBasedVisualizationFactory):
    """event"""
    def __init__(self):
        super(EventFactory, self).__init__()
        (self.mapper
             .add_text_member("fields", arity='?', factory=ListFormatter()))


class MapFactory(SearchBasedVisualizationFactory):
    """map"""
    pass


class SingleFactory(SearchBasedVisualizationFactory):
    """single"""
    pass


class HtmlFactory(VisualizationFactory):
    def __init__(self):
        super(VisualizationFactory, self).__init__()
        (self.mapper
         .add_attribute("encoded", arity='?')
         .add_attribute("src", arity='?')
         .add_attribute("tokens", arity='?'))

    def __call__(self, data):
        raw = ("<html>" + data["html"] + "</html>")
        html = ETtree.XML(raw)
        strip_xml(html)

        self.mapper.map(data).into(html, safe=True)
        return html


class FieldsetFactory(BaseFactory):
    """fieldset"""
    def __init__(self):
        super(FieldsetFactory, self).__init__()
        (self.mapper
         .add_attribute("autoRun", arity='?')
         .add_attribute("submitButton", arity='?')
         .add_member("items",
                     arity='*',
                     factory=Either(Tags.Time,
                                    Tags.Checkbox)))


class RowFactory(BaseFactory):
    """row"""
    def __init__(self):
        super(RowFactory, self).__init__()
        self.add_trait(Filterable(), Identifiable())
        (self.mapper
         .add_attribute("grouping", arity='?')
         .add_member("panels",
                     factory=PanelFactory(),
                     arity='*'))


class BaseDashboardFactory(BaseFactory):
    def __init__(self):
        super(BaseDashboardFactory, self).__init__()
        (self.mapper
         .add_attribute("hideChrome", arity='?')
         .add_attribute("hideAppBar", arity='?')
         .add_attribute("hideEdit", arity='?')
         .add_attribute("hideFilters", arity='?')
         .add_attribute("hideFooter", arity='?')
         .add_attribute("hideSplunkBar", arity='?')
         .add_attribute("hideTitle", arity='?')
         .add_attribute("isDashboard", arity='?')
         .add_attribute("isVisible", arity='?')
         .add_attribute("onunloadCancelJobs", arity='?')
         .add_attribute("refresh", arity='?')
         .add_attribute("script", arity='?')
         .add_attribute("stylesheet", arity='?')
         .add_text_member("label", arity='?')
         .add_text_member("description", arity='?')
         .add_member("search", factory=SearchFactory(), arity='?')
         .add_member("rows", factory=RowFactory(), arity='*')
         .add_member("fieldset", factory=FieldsetFactory(), arity='?'))


class DashboardFactory(BaseDashboardFactory):
    """dashboard"""
    pass


class FormFactory(BaseDashboardFactory):
    """form"""
    pass


class PanelFactory(BaseFactory):
    """panel"""
    def __init__(self):
        super(PanelFactory, self).__init__()
        (self.mapper
         .add_attribute("depends", arity='?')
         .add_attribute("app", arity='?')
         .add_attribute("id", arity='?')
         .add_attribute("ref", arity='?')
         .add_attribute("rejects", arity='?')
         .add_text_member("title", arity='?')
         .add_text_member("description", arity='?')
         .add_member("search", factory=SearchFactory(), arity='?')
         .add_member("items",
                     factory=Either(Tags.Table,
                                    Tags.Html,
                                    Tags.Chart,
                                    Tags.Event,
                                    Tags.Map,
                                    Tags.Single),
                     arity='+'))


def create(data):
    """
    Creates a Splunk dashboard from json formatted data.
    """
    return Either(Tags.Dashboard, Tags.Form)(data)
