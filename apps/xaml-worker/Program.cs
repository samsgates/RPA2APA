using System.Xml.Linq;
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
app.MapGet("/health", () => Results.Ok(new { ok = true, worker = "xaml" }));
app.MapPost("/parse", (ParseRequest req) => {
    if (!Directory.Exists(req.Path)) return Results.BadRequest(new { error = "Path does not exist" });
    var workflows = new List<object>();
    foreach (var file in Directory.EnumerateFiles(req.Path, "*.xaml", SearchOption.AllDirectories)) {
        var doc = XDocument.Load(file, LoadOptions.SetLineInfo);
        var acts = doc.Descendants().Select((e, i) => new {
            id = $"{Path.GetFileNameWithoutExtension(file)}:{i}:{e.Name.LocalName}",
            type = e.Name.LocalName,
            displayName = e.Attributes().FirstOrDefault(a => a.Name.LocalName == "DisplayName")?.Value ?? e.Name.LocalName,
            attributes = e.Attributes().ToDictionary(a => a.Name.LocalName, a => a.Value)
        }).ToList();
        workflows.Add(new { name = Path.GetFileNameWithoutExtension(file), path = Path.GetRelativePath(req.Path, file), activities = acts });
    }
    return Results.Ok(new { workflows });
});
app.Run();
record ParseRequest(string Path);
