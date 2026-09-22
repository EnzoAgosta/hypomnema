"""Read, edit, and write TMX 1.4b translation memories with typed models.

Import node models from hypomnema.models, streaming readers and writers from
hypomnema.io, and explicit runtime checks from hypomnema.validation. The package
root does not re-export these names.

Reading checks XML structure and coerces model values. Writing also checks
runtime fields and relationships between nodes before serializing each unit.
Applications can invoke the validators separately after modifying a model.
"""
