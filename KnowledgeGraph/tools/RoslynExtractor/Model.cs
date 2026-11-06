namespace RoslynExtractor;

// Language-neutral syntax facts. Python (spectrum_kg.extract) interprets these into graph nodes.

public sealed class FileFacts
{
    public string Path { get; set; } = "";
    public string Language { get; set; } = "";          // "vb" | "csharp"
    public List<string> Imports { get; set; } = new();
    public List<TypeFacts> Types { get; set; } = new();
    public List<string> Diagnostics { get; set; } = new(); // syntax errors, if any
}

public sealed class TypeFacts
{
    public string Name { get; set; } = "";
    public string Kind { get; set; } = "";               // class | struct | interface | module | enum
    public string Namespace { get; set; } = "";
    public bool Partial { get; set; }
    public List<string> Bases { get; set; } = new();     // Inherits / base list
    public List<string> Implements { get; set; } = new();
    public List<FieldFacts> Fields { get; set; } = new();
    public List<PropertyFacts> Properties { get; set; } = new();
    public List<MethodFacts> Methods { get; set; } = new();
    public int StartLine { get; set; }
    public int EndLine { get; set; }
}

public sealed class FieldFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public List<string> Modifiers { get; set; } = new();
    public bool WithEvents { get; set; }
    public string? Initializer { get; set; }
    public int Line { get; set; }
}

public sealed class PropertyFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public string? BackingField { get; set; }
    public int Line { get; set; }
}

public sealed class ParamFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
}

public sealed class HandlesFacts
{
    public string Target { get; set; } = "";   // control / field name ("MyBase" for form events)
    public string Event { get; set; } = "";
}

public sealed class InvocationFacts
{
    public string Text { get; set; } = "";
    public string? Receiver { get; set; }      // text left of the final '.', With-target resolved
    public string Member { get; set; } = "";
    public List<string> Args { get; set; } = new();
    public int Line { get; set; }
}

public sealed class MemberAccessFacts
{
    public string Receiver { get; set; } = "";
    public string Member { get; set; } = "";
    public int Line { get; set; }
}

public sealed class AssignmentFacts
{
    public string Left { get; set; } = "";
    public string Right { get; set; } = "";
    public string Op { get; set; } = "=";      // "=", "+=", ...
    public int Line { get; set; }
}

public sealed class LocalFacts
{
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public string? Initializer { get; set; }
    public int Line { get; set; }
}

public sealed class SubscriptionFacts
{
    public string Target { get; set; } = "";
    public string Event { get; set; } = "";
    public string Handler { get; set; } = "";
    public int Line { get; set; }
}

public sealed class MethodFacts
{
    public string Name { get; set; } = "";
    public string Kind { get; set; } = "";     // sub | function | method | constructor
    public string ReturnType { get; set; } = "";
    public List<string> Modifiers { get; set; } = new();
    public List<ParamFacts> Parameters { get; set; } = new();
    public List<HandlesFacts> Handles { get; set; } = new();
    public List<string> ImplementsMembers { get; set; } = new();
    public int StartLine { get; set; }
    public int EndLine { get; set; }
    public string Code { get; set; } = "";
    public string LeadingComments { get; set; } = "";
    public List<InvocationFacts> Invocations { get; set; } = new();
    public List<MemberAccessFacts> MemberAccesses { get; set; } = new();
    public List<AssignmentFacts> Assignments { get; set; } = new();
    public List<LocalFacts> Locals { get; set; } = new();
    public List<string> ObjectCreations { get; set; } = new();
    public List<SubscriptionFacts> Subscriptions { get; set; } = new();
    public List<string> StringLiterals { get; set; } = new();
}
