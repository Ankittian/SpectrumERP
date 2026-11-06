using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Syntax;

namespace RoslynExtractor;

public static class CSharpExtractor
{
    public static FileFacts Extract(string path, string text)
    {
        var tree = CSharpSyntaxTree.ParseText(text, path: path);
        var root = tree.GetCompilationUnitRoot();
        var facts = new FileFacts { Path = path, Language = "csharp" };
        facts.Diagnostics.AddRange(tree.GetDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Error).Select(d => d.ToString()));
        facts.Imports.AddRange(root.DescendantNodes().OfType<UsingDirectiveSyntax>().Select(u => u.Name?.ToString() ?? ""));

        foreach (var type in root.DescendantNodes().OfType<BaseTypeDeclarationSyntax>())
        {
            var tf = new TypeFacts
            {
                Name = type.Identifier.Text,
                Kind = type switch
                {
                    InterfaceDeclarationSyntax => "interface",
                    StructDeclarationSyntax => "struct",
                    EnumDeclarationSyntax => "enum",
                    RecordDeclarationSyntax => "record",
                    _ => "class",
                },
                Namespace = string.Join(".", type.Ancestors().OfType<BaseNamespaceDeclarationSyntax>().Reverse().Select(n => n.Name.ToString())),
                Partial = type.Modifiers.Any(m => m.IsKind(SyntaxKind.PartialKeyword)),
                StartLine = Line(type),
                EndLine = EndLine(type),
            };
            if (type.BaseList is not null)
                tf.Bases.AddRange(type.BaseList.Types.Select(t => t.Type.ToString()));

            if (type is TypeDeclarationSyntax tds)
            {
                foreach (var member in tds.Members)
                {
                    switch (member)
                    {
                        case FieldDeclarationSyntax f:
                            foreach (var v in f.Declaration.Variables)
                                tf.Fields.Add(new FieldFacts
                                {
                                    Name = v.Identifier.Text,
                                    Type = f.Declaration.Type.ToString(),
                                    Modifiers = f.Modifiers.Select(m => m.Text).ToList(),
                                    Initializer = v.Initializer?.Value.ToString(),
                                    Line = Line(v),
                                });
                            break;
                        case PropertyDeclarationSyntax p:
                            tf.Properties.Add(new PropertyFacts
                            {
                                Name = p.Identifier.Text,
                                Type = p.Type.ToString(),
                                BackingField = BackingField(p),
                                Line = Line(p),
                            });
                            break;
                        case MethodDeclarationSyntax m:
                            tf.Methods.Add(Method(m, m.Identifier.Text, "method", m.ReturnType.ToString(), m.Modifiers, m.ParameterList));
                            break;
                        case ConstructorDeclarationSyntax c:
                            tf.Methods.Add(Method(c, c.Identifier.Text, "constructor", "", c.Modifiers, c.ParameterList));
                            break;
                    }
                }
            }
            facts.Types.Add(tf);
        }
        return facts;
    }

    static string? BackingField(PropertyDeclarationSyntax p)
    {
        var getter = p.AccessorList?.Accessors.FirstOrDefault(a => a.IsKind(SyntaxKind.GetAccessorDeclaration));
        SyntaxNode? body = (SyntaxNode?)getter?.Body ?? getter?.ExpressionBody ?? (SyntaxNode?)p.ExpressionBody;
        var ret = body?.DescendantNodesAndSelf().OfType<ReturnStatementSyntax>().FirstOrDefault()?.Expression
                  ?? (body as ArrowExpressionClauseSyntax)?.Expression;
        return ret switch
        {
            IdentifierNameSyntax id => id.Identifier.Text,
            MemberAccessExpressionSyntax ma when ma.Expression is ThisExpressionSyntax => ma.Name.Identifier.Text,
            _ => null,
        };
    }

    static MethodFacts Method(BaseMethodDeclarationSyntax node, string name, string kind, string returnType,
        SyntaxTokenList modifiers, ParameterListSyntax parameters)
    {
        var mf = new MethodFacts
        {
            Name = name,
            Kind = kind,
            ReturnType = returnType,
            Modifiers = modifiers.Select(m => m.Text).ToList(),
            Parameters = parameters.Parameters.Select(p => new ParamFacts { Name = p.Identifier.Text, Type = p.Type?.ToString() ?? "" }).ToList(),
            StartLine = Line(node),
            EndLine = EndLine(node),
            Code = node.ToString(),
            LeadingComments = Comments(node),
        };
        SyntaxNode body = (SyntaxNode?)node.Body ?? (SyntaxNode?)node.ExpressionBody ?? node;

        foreach (var n in body.DescendantNodes())
        {
            switch (n)
            {
                case InvocationExpressionSyntax inv:
                    {
                        string? receiver = null; string member;
                        if (inv.Expression is MemberAccessExpressionSyntax ma) { receiver = ma.Expression.ToString(); member = ma.Name.Identifier.Text; }
                        else if (inv.Expression is MemberBindingExpressionSyntax mb) { member = mb.Name.Identifier.Text; }
                        else member = inv.Expression.ToString();
                        mf.Invocations.Add(new InvocationFacts
                        {
                            Text = Trunc(inv.ToString()),
                            Receiver = receiver,
                            Member = member,
                            Args = inv.ArgumentList.Arguments.Select(a => Trunc(a.ToString())).ToList(),
                            Line = Line(inv),
                        });
                        break;
                    }
                case MemberAccessExpressionSyntax ma2:
                    mf.MemberAccesses.Add(new MemberAccessFacts { Receiver = ma2.Expression.ToString(), Member = ma2.Name.Identifier.Text, Line = Line(ma2) });
                    break;
                case AssignmentExpressionSyntax asg:
                    {
                        var op = asg.OperatorToken.Text;
                        mf.Assignments.Add(new AssignmentFacts { Left = asg.Left.ToString(), Right = Trunc(asg.Right.ToString()), Op = op, Line = Line(asg) });
                        if (op == "+=" && asg.Left is MemberAccessExpressionSyntax evt)
                        {
                            var handler = asg.Right switch
                            {
                                ObjectCreationExpressionSyntax oc when oc.ArgumentList?.Arguments.Count == 1 => oc.ArgumentList.Arguments[0].ToString(),
                                _ => asg.Right.ToString(),
                            };
                            mf.Subscriptions.Add(new SubscriptionFacts
                            {
                                Target = StripThis(evt.Expression.ToString()),
                                Event = evt.Name.Identifier.Text,
                                Handler = StripThis(handler),
                                Line = Line(asg),
                            });
                        }
                        break;
                    }
                case LocalDeclarationStatementSyntax ld:
                    foreach (var v in ld.Declaration.Variables)
                        mf.Locals.Add(new LocalFacts
                        {
                            Name = v.Identifier.Text,
                            Type = ld.Declaration.Type.IsVar && v.Initializer?.Value is ObjectCreationExpressionSyntax oce ? oce.Type.ToString() : ld.Declaration.Type.ToString(),
                            Initializer = v.Initializer is null ? null : Trunc(v.Initializer.Value.ToString()),
                            Line = Line(v),
                        });
                    break;
                case ObjectCreationExpressionSyntax oc2:
                    mf.ObjectCreations.Add(oc2.Type.ToString());
                    break;
                case LiteralExpressionSyntax lit when lit.IsKind(SyntaxKind.StringLiteralExpression):
                    mf.StringLiterals.Add(lit.Token.ValueText);
                    break;
            }
        }
        return mf;
    }

    static string StripThis(string s) => s.StartsWith("this.") ? s[5..] : s;
    static string Trunc(string s) => s.Length > 400 ? s[..400] + "…" : s;
    static int Line(SyntaxNode n) => n.GetLocation().GetLineSpan().StartLinePosition.Line + 1;
    static int EndLine(SyntaxNode n) => n.GetLocation().GetLineSpan().EndLinePosition.Line + 1;

    static string Comments(SyntaxNode n) => string.Join("\n", n.GetLeadingTrivia()
        .Where(t => t.IsKind(SyntaxKind.SingleLineCommentTrivia) || t.IsKind(SyntaxKind.MultiLineCommentTrivia)
                    || t.IsKind(SyntaxKind.SingleLineDocumentationCommentTrivia))
        .Select(t => t.ToFullString().Trim()));
}
