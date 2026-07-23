# qntm.network markdown demo

This page is rendered from **markdown** into HTML by a *traced Python capability* —
`site-renders-markdown`, qntm.network's first package with a real call stack.

## What it demonstrates

- headings (three levels here)
- lists, like this one
- **bold** and *italic*
- inline `code`
- [links](https://qntm.network)

### A fenced code block

```python
from qntm_network.render import MarkdownRenderer

MarkdownRenderer().to_html("# hello")  # pure: markdown -> html
```

### A table

| layer | thing | depth to sink |
|-------|-------|:-------------:|
| capability | site-renders-markdown | 2 |
| class | MarkdownRenderer (pure leaf) | off-path |
| sink | rendered-page-written | 0 |

> The number is read from the **actual** observed flow, not the declared one — so it catches
> the layer you did not mean to add.
