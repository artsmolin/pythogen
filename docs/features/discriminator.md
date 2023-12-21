# Discriminator
Generate [pydantic classes with discriminators](https://docs.pydantic.dev/latest/api/standard_library_types/#discriminated-unions-aka-tagged-unions) based on [OpenAPI discriminators](https://swagger.io/docs/specification/data-models/inheritance-and-polymorphism/). The original OpenAPI specification must have the `propertyName` and `mapping` fields.


## Example
For OpenAPI schema
```yaml
DiscriminatedOneOfResp:
      title: All Of Resp
      type: object
      required: ['required_discriminated_animal']
      properties:
        discriminated_animal:
          discriminator:
            mapping: {cat: '#/components/schemas/CatWithKind', dog: '#/components/schemas/DogWithKind'}
            propertyName: kind
          oneOf:
            - {$ref: '#/components/schemas/CatWithKind'}
            - {$ref: '#/components/schemas/DogWithKind'}
          title: Animal
        required_discriminated_animal:
          discriminator:
            mapping: {cat: '#/components/schemas/CatWithKind', dog: '#/components/schemas/DogWithKind'}
            propertyName: kind
          oneOf:
            - {$ref: '#/components/schemas/CatWithKind'}
            - {$ref: '#/components/schemas/DogWithKind'}
          title: Animal
```
the following class will be generated
```python
class DiscriminatedOneOfResp(BaseModel):
    required_discriminated_animal: CatWithKind | DogWithKind = Field(..., discriminator="kind")
    discriminated_animal: CatWithKind | DogWithKind | None = Field(None, discriminator="kind")
```