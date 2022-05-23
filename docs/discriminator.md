[← README.md](/README.md)

# Discriminator
Pythogen is able to generate a base class in which the logic of the discriminator is implemented by the value of the specified field. To do this, the desired field in the "description" parameter must contain a text
```
__description__(BaseClassName.field)
```
- `BaseClassName` — desired name of the base class
- `field` — discriminator field
