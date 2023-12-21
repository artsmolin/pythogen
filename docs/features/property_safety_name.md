# Property safety name
Property names are automatically converted to secure python names. However, you can explicitly specify the name with which the property will be generated for the data schema. To do this, specify the desired name in the property description in the format `__safety_key__(your_name)`.

## Auto converted names
For OpenAPI schema with not safety property names `for`, `class`, `33with.dot-and-hyphens&*`
```yaml
SafetyKeyForTesting:
      title: model for testing safety key
      type: object
      properties:
        for:
          title: For
          type: string
          description: reserved word, expecting "for_"
        class:
          title: Class
          type: string
          description: reserved word, expecting "class_"
        33with.dot-and-hyphens&*:
          title: With dot, hyphens and garbage
          type: integer
          description: invalid identifier, expecting "with_dot_and_hyphens"
```

the following class with  safety property names `for_`, `class_`, `with_dot_and_hyphens` will be generated
```python
class SafetyKeyForTesting(BaseModel):
    for_: str | None = Field(None, alias="for", description='reserved word, expecting "for_"')
    class_: str | None = Field(None, alias="class", description='reserved word, expecting "class_"')
    with_dot_and_hyphens: int | None = Field(
        None, alias="33with.dot-and-hyphens&*", description='invalid identifier, expecting "with_dot_and_hyphens"'
    )
```

## Custom names
For example, for the original schema with not safety property `event-data`
```yaml
PostObjectData:
    title: PostObjectData
    type: object
    properties:
        event-data:
            title: Event-Data
            type: object
            description: __safety_key__(custom_name)
```
the following class with property `custom_name` will be generated
```python
class PostObjectData(BaseModel):
    custom_name: dict = Field(..., alias="event-data", description="__safety_key__(custom_name)")
```