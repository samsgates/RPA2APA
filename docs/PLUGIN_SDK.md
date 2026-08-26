# Plugin SDK

The first release exposes Python extension seams through ordinary protocols/interfaces. A formal entry-point based SDK can evolve without changing APIR.

Recommended plugin types:

```python
class SourceParser(Protocol):
    def parse(self, root: str) -> SourceProject: ...

class TargetCompiler(Protocol):
    def compile(self, plan: MigrationPlan, output: str) -> Path: ...

class ModelProvider(Protocol):
    async def generate(self, *, model: str, system: str, prompt: str) -> str: ...
```

Future plugins:

- Automation Anywhere parser
- Blue Prism parser
- Power Automate parser
- SAP capability mapper
- ServiceNow mapper
- Salesforce mapper
- OpenAI Agents compiler
- Temporal compiler
- OPA policy backend
