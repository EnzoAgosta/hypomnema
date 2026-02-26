---
title: Custom Handlers
---

# Custom Handlers

Extend or replace (de)serialization handlers for non-standard TMX elements.

## Handler Pattern

Each TMX element type has a dedicated handler:

- **Deserializer**: XML → Python object
- **Serializer**: Python object → XML

Handlers are registered with the orchestrator and called via `emit()`.

## Base Classes

```python
class BaseElementDeserializer[TypeOfBackendElement, TypeOfTmxElement: BaseElement](ABC):
    backend: XmlBackend
    policy: XmlDeserializationPolicy
    logger: Logger | None
    
    @abstractmethod
    def _deserialize(self, element: TypeOfBackendElement) -> TypeOfTmxElement | None: ...
    
    def emit(self, element: TypeOfBackendElement) -> BaseElement | None: ...


class BaseElementSerializer[TypeOfBackendElement, TypeOfTmxElement: BaseElement](ABC):
    backend: XmlBackend
    policy: XmlSerializationPolicy
    logger: Logger | None
    
    @abstractmethod
    def _serialize(self, obj: TypeOfTmxElement) -> TypeOfBackendElement | None: ...
    
    def emit(self, obj: BaseElement) -> TypeOfBackendElement | None: ...
```

## Creating a Custom Handler

### Example: Custom Prop Handler

```python
from hypomnema.xml.deserialization.base import BaseElementDeserializer
from hypomnema.xml.serialization.base import BaseElementSerializer
from hypomnema import Prop

class MyPropDeserializer(BaseElementDeserializer[Element, Prop]):
    def _deserialize(self, element: Element) -> Prop | None:
        text = self.backend.get_text(element)
        prop_type = self.backend.get_attribute(element, "type")
        
        if text is None or prop_type is None:
            return None
        
        # Custom logic: auto-prefix unknown types
        if not prop_type.startswith("x-") and not prop_type in KNOWN_TYPES:
            prop_type = f"x-{prop_type}"
        
        return Prop(
            text=text,
            type=prop_type,
            lang=self.backend.get_attribute(element, "{xml}lang"),
        )


class MyPropSerializer(BaseElementSerializer[Element, Prop]):
    def _serialize(self, obj: Prop) -> Element | None:
        element = self.backend.create_element("prop")
        self.backend.set_text(element, obj.text)
        self.backend.set_attribute(element, "type", obj.type)
        
        if obj.lang:
            self.backend.set_attribute(element, "{xml}lang", obj.lang)
        
        return element
```

## Registering Custom Handlers

```python
from hypomnema import load, dump, deserialization, serialization

# Custom deserializer with custom handler
custom_handlers = {
    "prop": MyPropDeserializer(backend=..., policy=..., logger=...),
}

deserializer = deserialization.Deserializer(
    backend=...,
    handlers=custom_handlers,
)

tmx = load("file.tmx", deserializer=deserializer)

# Custom serializer with custom handler
serializers = {
    Prop: MyPropSerializer(backend=..., policy=...),
}

serializer = serialization.Serializer(
    backend=...,
    handlers=serializers,
)

dump(tmx, "output.tmx", serializer=serializer)
```

## Handler Registration Keys

| Deserializer | Serializer |
|--------------|------------|
| Tag name (`"prop"`, `"tu"`, etc.) | Class type (`Prop`, `Tu`, etc.) |

## The emit() Pattern

Handlers call `emit()` for nested elements, not their own methods:

```python
class MyTuDeserializer(BaseElementDeserializer[Element, Tu]):
    def _deserialize(self, element: Element) -> Tu | None:
        variants = []
        for child in self.backend.iter_children(element):
            if self.backend.get_tag(child) == "tuv":
                tuv = self.emit(child)  # Dispatches to TuvDeserializer
                if tuv:
                    variants.append(tuv)
        
        return Tu(variants=variants, ...)
```

This allows handlers to be overridden without modifying parent handlers.

## Use Cases

- **Non-standard attributes**: Handle proprietary TMX extensions
- **Data transformation**: Normalize or transform data during (de)serialization
- **Validation**: Add custom validation beyond standard policies
- **Logging/monitoring**: Track specific elements during processing

## See Also

- [Duck Typing](/en/advanced/duck-typing) — Custom classes without custom handlers
- [Policy](/en/api/policy/) — Configure standard handler behavior
