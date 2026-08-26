# RPA2APA CoreWF XAML Worker

Optional .NET worker intended for production-grade semantic parsing of UiPath/CoreWF workflows. The Python API includes a deterministic XML fallback parser so RPA2APA remains usable without .NET.

When .NET is available:

```bash
dotnet restore
dotnet run
```

The worker accepts `POST /parse` with `{ "path": "/absolute/project/path" }` and returns normalized workflow/activity JSON.
