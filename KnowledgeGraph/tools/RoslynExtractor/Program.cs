using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using RoslynExtractor;

// Usage: RoslynExtractor --out facts.json <file-or-dir> [<file-or-dir> ...]
// Parses every .vb / .cs file (syntax only, no compilation/references needed) and writes a JSON array of FileFacts.

string? outPath = null;
var inputs = new List<string>();
for (int i = 0; i < args.Length; i++)
{
    if (args[i] == "--out" && i + 1 < args.Length) outPath = args[++i];
    else inputs.Add(args[i]);
}
if (inputs.Count == 0)
{
    Console.Error.WriteLine("usage: RoslynExtractor --out facts.json <file-or-dir>...");
    return 2;
}

var files = new List<string>();
foreach (var input in inputs)
{
    if (File.Exists(input)) files.Add(Path.GetFullPath(input));
    else if (Directory.Exists(input))
        files.AddRange(Directory.EnumerateFiles(input, "*.*", SearchOption.AllDirectories)
            .Where(f => f.EndsWith(".vb", StringComparison.OrdinalIgnoreCase) || f.EndsWith(".cs", StringComparison.OrdinalIgnoreCase))
            .Where(f => !f.Split(Path.DirectorySeparatorChar).Any(p => p is "bin" or "obj" or ".venv"))
            .Select(Path.GetFullPath));
}

var results = new List<FileFacts>();
foreach (var file in files.Distinct().OrderBy(f => f, StringComparer.OrdinalIgnoreCase))
{
    var text = File.ReadAllText(file, Encoding.UTF8);
    try
    {
        results.Add(file.EndsWith(".vb", StringComparison.OrdinalIgnoreCase)
            ? VbExtractor.Extract(file, text)
            : CSharpExtractor.Extract(file, text));
    }
    catch (Exception ex)
    {
        results.Add(new FileFacts { Path = file, Language = "error", Diagnostics = { ex.ToString() } });
    }
}

var json = JsonSerializer.Serialize(results, new JsonSerializerOptions
{
    WriteIndented = false,
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
});
if (outPath is null) Console.Out.Write(json);
else File.WriteAllText(outPath, json, new UTF8Encoding(false));
Console.Error.WriteLine($"parsed {results.Count} files");
return 0;
