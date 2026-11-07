# Circle writing

**English** · [日本語](../ja/writing.md) · [Documentation](../README.md)

The adopted script uses circles, arcs, lines, and dots to encode typed Noema structures. Geometry carries lexical and grammatical information. A visually permissible drawing is not necessarily a valid sentence: it must also use registered forms, connections, and syntax.

The fixed style is concept2 v7 with the document and sharing rules recorded in [writing-freeze-v2.json](../../data/writing-freeze-v2.json). This page explains the common rules; [the original Japanese specification](../circle-writing-v2.md) preserves the normative release record. The registered form inventory is available through `scripts.concept2_writing.WritingReader().forms`.

## From meaning to drawing, and back

Generation proceeds from type-checked syntax to a scoped sharing plan, registered glyphs, connections, and line wrapping. Expanding the sharing plan must recover the original syntax before drawing. Meanings are not assigned to arbitrary shapes afterward.

Decoding reads visible circles, arcs, lines, and dots, recognizes forms and connections, reconstructs words and syntax, expands sharing, and checks types and bindings. The input consists of SVG geometry and the public dictionary. Hidden ASTs, expected token sequences, sentence numbers, and SVG identifier attributes are not needed. Declarations can also be decoded sequentially from an initially empty dictionary.

This contract applies to compliant vector writing. Handwriting recognition, photographs, and raster OCR are outside it. A text/JSON round trip or a legacy-font rendering is not evidence of this visible decoding.

## Geometry and line length

Let S be the small-circle radius. The radii and vertical lane spacing are:

| Element | Size |
| --- | --- |
| Medium circle M | `(1 + √2)S` |
| Large circle L | `(1 + 2√2)S` |
| Fourth circle F | `(1 + 3√2)S` |
| Upper/lower lane offset P | `(2 + √2)S` from the middle lane |
| Dot radius | `(√2 − 1)S` |

Scaling preserves these ratios. Large and fourth-circle centers lie on the middle lane. Containment is concentric. Permitted orthogonal intersections pair small/medium, small/large, or medium/large circles, with center distance `√(r² + R²)`. Off-center complete containment is forbidden. Inherited tangencies are limited to small/medium circles in one vertical column and medium circles offset by P along both axes. Small circles are complete; straight lines stop at their circumference and never enter their interiors.

At a medium/large intersection, retain the large arc inside the medium circle. The two portions outside the medium circle but within the overlapping-side 90° sector are retained or removed together. Outside that sector, choose 45° portions, retaining at least 45°. Neither cutting out only the arc inside the medium circle nor leaving only that inner arc is allowed. At a small/large intersection, cutting the large arc out of the small circle is permitted.

Other medium and large arcs use 45° intervals, with orthogonal intersection endpoints as an exception. The fourth circle omits the prohibited upper/lower sectors. Direction lines and free ends belonging to a circle stop within radius F from its center; an endpoint at 45° is bounded by `F/√2` on each axis. Connections to another circle follow the connection-length rule instead.

For a connection to the left or right, find the largest of L and M with a positive-length arc in that side's half-circle. Measure the radius-width M from that circle's **complete-circle extremity**, even where the arc is missing. If neither qualifies, use the actual contact point. A single point on the half-circle boundary does not qualify; the fourth circle is excluded from this promotion rule.

For a diagonal large-circle terminal leading to an upper/lower small circle, the horizontal distance from the large circle's complete left/right extremity to the small-circle center is M. Ordinary horizontal connections between small circles measure M between circumferences. In the reference-order stem, small-circle centers are `2S + M` apart, and branch endpoints align vertically with the next stem circle.

## Reading order and arguments

Read rows from top to bottom and each row left to right. New sentences have a 2M gap. A continuing sentence uses radius-width line ends and matching lanes at the end and start of rows. Wrap between glyphs, never inside one; wrapping preserves the lexical and reference environment.

Words are sequences of 30 public roots. Thirteen ligatures and two directional variants expand into their root sequences. A word terminator disambiguates a word from an extension of its spelling; declaration names and alias registrations always have terminators. Document row numbers do not become word names.

There is no uniform sentence-initial glyph. Assertions may begin directly with their expressions; questions, directives, and assumptions have their own syntax. Operators have fixed arities, while calls use previously declared argument types and counts. Variable-length lists have terminators. Circle-bearing delimiters distinguish value, quotation, and reference groups and their endings.

Argument order follows syntax. Two or three distinct references in upper/middle/lower order may use a multiple-small-circle selector. Other orders, including repeated lanes, use the adopted v4/v7 stem. A directional selector points from its center toward the first small circle, then reads clockwise. At a merge, branches read top to bottom and each branch's arc identifies its referent. A merge does not assert identity or logical disjunction. Four or more arguments remain expressible with ordinary lists and group delimiters.

## Bindings, sharing, and dots

Bindings retain their type, scope, depth, and position. Scope hops reach outer bindings; leaving a scope restores its outer environment. Quotations have separate binding/reference environments, and sibling statements under an assumption do not inherit each other's local abbreviations.

Sharing applies only to matching syntax with matching bindings. The available families include eight local-value references, eight word references, three lane references, and three quotation templates. A word abbreviation does not mean reuse of a value. A shared quotation template need not identify its different contents.

The default generator selects repeated expressions within a scope when sharing shortens the representation. It can share expressions containing variables when their bindings remain the same. It does not move them across inner binders or quotations, and it removes unused sharing definitions. Shape frequencies depend on the document and these choices; legal forms need not occur equally often.

Repetition marks encode two to five consecutive occurrences, with combinations for longer runs. Bare vertical-line lengths S, M, L, and F distinguish the counts. Small-circle-only roots are excluded, and intentional uncompressed repetition remains valid.

Dots can pair distant occurrences within a scope. Eight 45° medium-circle arc intervals give 256 identifiers. Ordinary identifiers use medium arcs on both sides; a complete circle is unnecessary. Only the form without medium arcs moves to a large circle, whose counterpart may be a bare dot. Outer circles and connection small circles do not alter the identifier. Lines do not connect to dots, and dots do not sit inside small circles. Matching identifiers pair in order; unmatched pairs and crossing quotation boundaries are rejected. Dots are an available abbreviation, not mandatory decoration or a universal reference marker.

Long two- or three-argument branches can use a local assembly scope: define values on distinct lanes in the original argument order, close the definitions, then supply lane references to the call. Values may contain nested scopes, bindings, and quotations. The final stem or selector remains one glyph, and leaving the assembly restores the outer reference environment. Arbitrarily long parallel branches wrapping independently, cyclic graphs, and unresolved forward references are not part of this notation. Serial notation remains available.

## Implementation and extension

The document API is [WritingReader](../../scripts/concept2_writing.py), with `encode_record` and `read_svg` operations. [Release tests](../../tests/test_concept2_release.py) show a small geometry-level round trip; [assembly tests](../../tests/test_concept2_assembly.py) cover longer branches. These are repository APIs, not a general-purpose GUI editor. The two-work publication uses a recorded repair encoder with the same adopted decoder; its selected inputs are in the [publication manifest](../../data/two-work-publication-v1.json).

Declarations introduce primitives, typed definitions, and aliases before use. Unknown names, duplicate names, spelling collisions, forward references, and cycles are rejected; failed records do not enter the dictionary. The frozen inventory contains 501 registered forms. New vocabulary can use existing root sequences; assigning a new standalone form requires a versioned inventory and decoding-rule update.
