# Language guide

**English** · [日本語](../ja/language.md) · [Documentation](../README.md)

Noema constructs meanings from typed expressions, named definitions, and explicit scope. This guide collects the reader-facing rules used in edition 1.0. The tables show compact textual syntax; schematic names such as `EXPR` and `T` are placeholders, not literal Noema tokens.

## Values and types

| Type | Meaning |
| --- | --- |
| `a` | Individual: a member of the document's nonempty object domain, including abstract objects |
| `b` | Exact rational number |
| `c` | Truth value: true or false |
| `d` | Situation: a member of a nonempty domain of cases or states |
| `e` | Content: a truth value for each situation |
| `f` | Message: assertive, interrogative, or directive force paired with content |
| `h[T …] R` | Function from the ordered argument types to result type R |
| `g[T …]` | Question whose answers are ordered tuples of the given types |
| `i[T]` | Description of a closed expression of type T, at evaluation rank 0 |
| `i b[T]`, `i c[T]` | Descriptions at ranks 1 and 2; other ranks use the same numeral convention |
| `j[T]` | Finite sequence of values of type T, preserving order and repetitions |

Types can be nested. Functions, descriptions, and sequences can themselves be arguments. A relation is a function returning a truth value; the grammar does not fix every sentence to the same number of roles. Declared functions are total on their stated domains. Partiality is expressed through applicability and candidate relations, not an invented default value.

Having an individual in a domain does not assert its existence in the actual world. A fictional person or planned house can be represented with its frame and separate actuality conditions. Likewise, a situation need not be physically possible merely because its type is `d`.

## Documents and reusable definitions

Syntax 0.16 starts with `p:`. Declarations and definitions precede statements:

| Form | Meaning |
| --- | --- |
| `r NAME[T …] R.` | Declare a primitive's argument and result types |
| `d NAME[x T …] R[EXPR].` | Define a name by an expression with typed parameters |
| `s[PROP].` | Assert a truth-valued proposition |
| `q[PROP].` | Ask whether a proposition holds |
| `q[QUESTION].` | Ask a question with typed answers |
| `l[MESSAGE].` | Perform the message's linguistic force |
| `a[PROP][STATEMENT. …].` | Speak within an explicit assumption scope |

A declaration's interpretation must be explained separately. A definition reuses earlier meanings; it does not assert that an object satisfying the definition exists. Duplicate names, undeclared uses, forward references, and recursive definitions are rejected. Recurring processes can instead be described with relations and constraints.

Here is a complete document using locally explained primitives: `aa(x)` means “x is a person,” `ab(y)` means “y is a book,” and `ac(x,y)` means “x read y” within a fixed context.

```text
p:
r aa[a] c.
r ab[a] c.
r ac[a a] c.
d ba[x a] c[g y a[w[k ab[v y]][k ac[v x v y]]]].
s[f x a[y[k aa[v x]][k ba[v x]]]].
```

`ba(x)` means that x read some book. The statement says that every person has that property; it does not require the same book for everyone. Time, language, and the interpretation of “read” are not inferred by the parser. A richer description can pass a situation and those conditions explicitly.

## Expressions and scope

| Form | Meaning |
| --- | --- |
| `v x` | Use the nearest enclosing binding of x |
| `k NAME[EXPR …]` | Apply a declared name to ordered arguments |
| `e[A][B]` | Equality of values of the same type |
| `u[P]` | Negation |
| `w[P][Q]`, `x[P][Q]` | Conjunction; inclusive disjunction |
| `y[P][Q]`, `z[P][Q]` | Material implication; equivalence |
| `f x T[P]`, `g x T[P]` | Universal; existential quantification over type T |
| `p NAME` | Refer to a declared function as a value |
| `i[x T …][EXPR]` | Construct a function with typed parameters |
| `c[FUNCTION][ARG …]` | Apply a function value |
| `b w[P]` | Construct content by binding a situation w |
| `t[CONTENT][SITUATION]` | Evaluate content at that situation |

Operators have fixed syntactic roles, so brackets and the parsing position distinguish repeated letters. A call's brackets contain its entire argument list; binary logical operators bracket each operand separately. Free variables and type mismatches are rejected. Renaming bound variables during normalization preserves their referents.

`∀x ∃y` and `∃y ∀x` have different scopes, as the [introductory example](getting-started.md) illustrates. Material implication does not itself express causation, temporal order, or a counterfactual. Those require relations and conditions appropriate to the intended meaning.

A content value describes truth across situations. Equal truth values here and now do not make two contents equal. Contents that agree in every situation are equal at type `e`; if a difference in description matters, use description values as well. A truth-valued parameter passed into a content expression remains that value, rather than becoming an expression reevaluated at every situation.

## Messages, questions, and quotation

`j s[CONTENT]`, `j q[CONTENT]`, and `j m[CONTENT]` construct messages with assertive, questioning, and directive force. `o[MESSAGE]` extracts content. Construction alone does not perform a message. `l[MESSAGE].` does, but does not close a real window, confer institutional authority, or guarantee social uptake.

`j v[FUNCTION]` constructs a typed-answer question from a truth-valued function; `h[QUESTION][CANDIDATE …]` tests an ordered answer tuple. Asking which objects meet a condition does not assert that any do, or that the answer is unique.

| Form | Meaning |
| --- | --- |
| `r[EXPR]` | Describe a closed expression without evaluating it, at rank 0 |
| `r b[EXPR]` | Describe at rank 1; higher ranks use the same numeral convention |
| `s[DESCRIPTION]` | Explicitly evaluate the described expression |
| `o a[FUNCTION-DESCRIPTION][ARGUMENT-DESCRIPTION …]` | Construct the description of a function application |
| `o r[DESCRIPTION]` | Construct a description that quotes the supplied description |

Quotation has its own binding environment. It cannot capture a free variable from the surrounding statement. To represent a bound object inside an attributed content, retain a closed function description together with its typed argument values. Passing an object's value and passing a description of that object remain different choices.

Description equality preserves normalized syntax, not just its current truth. Two names can refer to the same object while their descriptions remain different. Description construction checks argument types, keeps the maximum input rank, and does not evaluate or simplify the described application.

Evaluation inside a quotation must target lower ranks; checks include referenced definitions, with runtime guards on higher-order evaluation paths. This discipline and execution budgets do not establish a general consistency or termination theorem. The original 0.15 prototype notes describe earlier limitations; consult the fixed release and current implementation for the adopted behavior.

## Numbers and sequences

`n p NUM DEN` is a nonnegative rational and `n u NUM DEN` a negative one. Numerals are base 32, with `a = 0`, `b = 1`, `c = 2`; thus `n u b c` is −1/2. Fractions normalize exactly. Zero denominators, floating-point literals, and redundant leading zeroes are rejected.

| Form | Meaning |
| --- | --- |
| `l[T][ITEM …]` | Finite sequence; `l[T][]` is empty |
| `d[SEQ]` | Length |
| `a[SEQ][INDEX][VALUE]` | Whether VALUE occupies the zero-based integer position INDEX |
| `m[LEFT][RIGHT]` | Concatenation of sequences of the same element type |
| `q[SEQ][INITIAL][STEP]` | Left-to-right fold, with step type `h[STATE T] STATE` |

An invalid position makes the position relation false; it does not create an element. A fold on an empty sequence returns its initial value. Order and duplicate occurrences are preserved. Quantification over all finite sequences is expressible, but a finite interpreter cannot enumerate that infinite domain.

## Keeping meanings apart

| Intended distinction | How to preserve it |
| --- | --- |
| Description versus actual existence | Keep the description and actuality conditions separate |
| Unknown value versus no value | Record applicability, candidates, and whether the candidate range is complete |
| Alternatives versus conflicting reports | Distinguish possible candidates from source-attributed, incompatible assertions |
| Belief versus fact | Attribute a content or description without asserting it as true |
| Literal versus intended reading | State both descriptions, their correspondence, and the grounds for that interpretation |
| Institutional declaration versus effective change | Connect the same act to authority, procedure, prerequisites, and outcome |
| A finite sample versus an unlimited process | State a general relation or quantified constraint, without substituting tested cases for its domain |

Noema's core truth type remains two-valued. Support for and against a description are separately recorded relations, so contradictory sources need not become a contradiction asserted by the document itself. Missing model inputs are not silently false.

Unbounded finite reachability can be defined by quantifying over all transitive relations containing the given edges. Infinite indexed processes can be described by functions and successor constraints. Self-reference can be represented through constraints on descriptions; no solution does not mean a sentence was evaluated as false. Expressing these conditions does not promise to solve them algorithmically.

The implementation bounds expression depth and type rank at 128; circle compound names have a 24-root limit. These resource limits are not semantic rules for filling in unknown answers. See [vocabulary](vocabulary.md) for extension rules and [evidence](evidence.md) for the scope of the checks.

## Specification sources

The preserved Japanese specification sequence is [0.8](../spec-v08.md), [0.9](../spec-v09.md), [0.10](../spec-v010.md), [0.11](../spec-v011.md), [0.12](../spec-v012.md), [0.13](../spec-v013.md), [0.14](../spec-v014.md), [ranked quotation](../ranked-quotation-v1.md), and [description construction](../quotation-construction-v1.md). [General composition](../general-language-v1.md) and [semantic boundaries](../semantic-boundaries-v1.md) explain the later semantic conventions. Their historical work reports are not current completion statuses.
