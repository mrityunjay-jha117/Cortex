# Questionnaire & Explanations

## Q: Why do we need `default_factory` for lists and dictionaries in Pydantic models?
**Context:** In files like `llm.py`, fields are defined as `input_context_keys: list[str] = Field(default_factory=list)`.

**Answer:**
This is used to prevent Python's famous **Mutable Default Argument Problem**. 

If you define a class with a direct list like this:
```python
class LLMExtractionNode(BaseNode):
    input_context_keys: list[str] = []  # BAD
```
Python evaluates class attributes exactly *once* when the module is imported. It creates **one single list in memory** and assigns it as the default for all nodes. 

If you create two separate nodes and modify one:
```python
node_A = LLMExtractionNode()
node_B = LLMExtractionNode()

node_A.input_context_keys.append("user_name")
print(node_B.input_context_keys) # Outputs: ["user_name"]
```
Because they share the exact same list object in memory, modifying one node accidentally modifies all of them!

**The Solution:**
By using `Field(default_factory=list)`, you are telling Pydantic to run the `list()` function *every time a new instance is created*. This guarantees that `node_A` and `node_B` each get a brand-new, independent empty list, keeping their data completely isolated and safe from cross-contamination.
