# Property safety name
You can explicitly specify the name with which the property will be generated for the data schema. To do this, specify the desired name in the property description in the format `__safety_key__(your_name)`.

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