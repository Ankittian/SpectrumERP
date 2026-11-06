using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.VisualBasic;
using Microsoft.CodeAnalysis.VisualBasic.Syntax;

namespace RoslynExtractor;

public static class VbExtractor
{
    public static FileFacts Extract(string path, string text)
    {
        var tree = VisualBasicSyntaxTree.ParseText(text, path: path);
        var root = (CompilationUnitSyntax)tree.GetRoot();
        var facts = new FileFacts { Path = path, Language = "vb" };
        facts.Diagnostics.AddRange(tree.GetDiagnostics().Where(d => d.Severity == DiagnosticSeverity.Error).Select(d => d.ToString()));
        facts.Imports.AddRange(root.Imports.SelectMany(i => i.ImportsClauses).Select(c => c.ToString()));

        foreach (var type in root.DescendantNodes().OfType<TypeBlockSyntax>())
        {
            var stmt = type.BlockStatement;
            var tf = new TypeFacts
            {
                Name = stmt.Identifier.Text,
                Kind = type switch
                {
                    ModuleBlockSyntax => "module",
                    StructureBlockSyntax => "struct",
                    InterfaceBlockSyntax => "interface",
                    _ => "class",
                },
                Namespace = string.Join(".", type.Ancestors().OfType<NamespaceBlockSyntax>().Reverse().Select(n => n.NamespaceStatement.Name.ToString())),
                Partial = stmt.Modifiers.Any(m => m.IsKind(SyntaxKind.PartialKeyword)),
                StartLine = Line(type),
                EndLine = EndLine(type),
            };
            tf.Bases.AddRange(type.Inherits.SelectMany(i => i.Types).Select(t => t.ToString()));
            tf.Implements.AddRange(type.Implements.SelectMany(i => i.Types).Select(t => t.ToString()));

            foreach (var member in type.Members)
            {
                switch (member)
                {
                    case FieldDeclarationSyntax f:
                        foreach (var d in f.Declarators)
                            foreach (var name in d.Names)
                                tf.Fields.Add(new FieldFacts
                                {
                                    Name = name.Identifier.Text,
                                    Type = AsType(d.AsClause),
                                    Modifiers = f.Modifiers.Select(m => m.Text).ToList(),
                                    WithEvents = f.Modifiers.Any(m => m.IsKind(SyntaxKind.WithEventsKeyword)),
                                    Initializer = d.Initializer?.Value.ToString() ?? (d.AsClause as AsNewClauseSyntax)?.NewExpression.ToString(),
                                    Line = Line(d),
                                });
                        break;
                    case PropertyBlockSyntax pb:
                        tf.Properties.Add(new PropertyFacts
                        {
                            Name = pb.PropertyStatement.Identifier.Text,
                            Type = AsType(pb.PropertyStatement.AsClause),
                            BackingField = pb.Accessors.FirstOrDefault(a => a.IsKind(SyntaxKind.GetAccessorBlock))?
                                .DescendantNodes().OfType<ReturnStatementSyntax>().FirstOrDefault()?.Expression?.ToString(),
                            Line = Line(pb),
                        });
                        break;
                    case PropertyStatementSyntax ps:
                        tf.Properties.Add(new PropertyFacts { Name = ps.Identifier.Text, Type = AsType(ps.AsClause), Line = Line(ps) });
                        break;
                    case MethodBlockSyntax mb:
                        tf.Methods.Add(Method(mb, mb.SubOrFunctionStatement));
                        break;
                    case ConstructorBlockSyntax cb:
                        tf.Methods.Add(Method(cb, cb.SubNewStatement));
                        break;
                }
            }
            facts.Types.Add(tf);
        }
        return facts;
    }

    static string AsType(AsClauseSyntax? clause) => clause switch
    {
        SimpleAsClauseSyntax s => s.Type.ToString(),
        AsNewClauseSyntax n => n.NewExpression is ObjectCreationExpressionSyntax oc ? oc.Type.ToString() : n.NewExpression.ToString(),
        _ => "",
    };

    static MethodFacts Method(MethodBlockBaseSyntax block, MethodBaseSyntax header)
    {
        var mf = new MethodFacts
        {
            Modifiers = header.Modifiers.Select(m => m.Text).ToList(),
            Parameters = header.ParameterList?.Parameters.Select(p => new ParamFacts
            {
                Name = p.Identifier.Identifier.Text,
                Type = AsType(p.AsClause),
            }).ToList() ?? new(),
            StartLine = Line(block),
            EndLine = EndLine(block),
            Code = block.ToString(),
            LeadingComments = Comments(block),
        };
        switch (header)
        {
            case MethodStatementSyntax ms:
                mf.Name = ms.Identifier.Text;
                mf.Kind = ms.IsKind(SyntaxKind.FunctionStatement) ? "function" : "sub";
                mf.ReturnType = AsType(ms.AsClause);
                if (ms.HandlesClause is not null)
                    mf.Handles.AddRange(ms.HandlesClause.Events.Select(e => new HandlesFacts
                    {
                        Target = e.EventContainer.ToString(),
                        Event = e.EventMember.Identifier.Text,
                    }));
                if (ms.ImplementsClause is not null)
                    mf.ImplementsMembers.AddRange(ms.ImplementsClause.InterfaceMembers.Select(i => i.ToString()));
                break;
            case SubNewStatementSyntax:
                mf.Name = "New";
                mf.Kind = "constructor";
                break;
        }

        foreach (var n in block.Statements.SelectMany(s => s.DescendantNodesAndSelf()))
        {
            switch (n)
            {
                case InvocationExpressionSyntax inv:
                    {
                        string? receiver = null; string member;
                        if (inv.Expression is MemberAccessExpressionSyntax ma) { receiver = Receiver(ma); member = ma.Name.Identifier.Text; }
                        else if (inv.Expression is null) { member = ""; }
                        else member = inv.Expression.ToString();
                        mf.Invocations.Add(new InvocationFacts
                        {
                            Text = Trunc(inv.ToString()),
                            Receiver = receiver,
                            Member = member,
                            Args = inv.ArgumentList?.Arguments.Select(a => Trunc(a.ToString())).ToList() ?? new(),
                            Line = Line(inv),
                        });
                        break;
                    }
                case MemberAccessExpressionSyntax ma2:
                    mf.MemberAccesses.Add(new MemberAccessFacts { Receiver = Receiver(ma2) ?? "", Member = ma2.Name.Identifier.Text, Line = Line(ma2) });
                    break;
                case AssignmentStatementSyntax asg:
                    mf.Assignments.Add(new AssignmentFacts { Left = ResolveWith(asg.Left), Right = Trunc(asg.Right.ToString()), Op = asg.OperatorToken.Text, Line = Line(asg) });
                    break;
                case LocalDeclarationStatementSyntax ld:
                    foreach (var d in ld.Declarators)
                        foreach (var name in d.Names)
                            mf.Locals.Add(new LocalFacts
                            {
                                Name = name.Identifier.Text,
                                Type = AsType(d.AsClause),
                                Initializer = d.Initializer is null ? null : Trunc(d.Initializer.Value.ToString()),
                                Line = Line(d),
                            });
                    break;
                case ObjectCreationExpressionSyntax oc:
                    mf.ObjectCreations.Add(oc.Type.ToString());
                    break;
                case AddRemoveHandlerStatementSyntax ah when ah.IsKind(SyntaxKind.AddHandlerStatement):
                    if (ah.EventExpression is MemberAccessExpressionSyntax evt)
                        mf.Subscriptions.Add(new SubscriptionFacts
                        {
                            Target = Receiver(evt) ?? "",
                            Event = evt.Name.Identifier.Text,
                            Handler = ah.DelegateExpression is UnaryExpressionSyntax u ? u.Operand.ToString() : ah.DelegateExpression.ToString(),
                            Line = Line(ah),
                        });
                    break;
                case LiteralExpressionSyntax lit when lit.IsKind(SyntaxKind.StringLiteralExpression):
                    mf.StringLiterals.Add(lit.Token.ValueText);
                    break;
            }
        }
        return mf;
    }

    // Receiver text of a member access; ".Foo" inside a With block resolves to the With target.
    static string? Receiver(MemberAccessExpressionSyntax ma)
    {
        if (ma.Expression is not null) return ResolveWith(ma.Expression);
        var with = ma.Ancestors().OfType<WithBlockSyntax>().FirstOrDefault();
        return with?.WithStatement.Expression.ToString();
    }

    static string ResolveWith(ExpressionSyntax e)
    {
        var text = e.ToString();
        if (!text.StartsWith(".")) return text;
        var with = e.Ancestors().OfType<WithBlockSyntax>().FirstOrDefault();
        return with is null ? text : with.WithStatement.Expression + text;
    }

    static string Trunc(string s) => s.Length > 400 ? s[..400] + "…" : s;
    static int Line(SyntaxNode n) => n.GetLocation().GetLineSpan().StartLinePosition.Line + 1;
    static int EndLine(SyntaxNode n) => n.GetLocation().GetLineSpan().EndLinePosition.Line + 1;

    static string Comments(SyntaxNode n) => string.Join("\n", n.GetLeadingTrivia()
        .Where(t => t.IsKind(SyntaxKind.CommentTrivia) || t.IsKind(SyntaxKind.DocumentationCommentTrivia))
        .Select(t => t.ToFullString().Trim()));
}
