# Language

Shared vocabulary for every architectural suggestion this skill makes. Use these terms exactly.
Don't substitute "component," "service," "API," or "boundary."

## Terms

**Module**
Anything with an interface and an implementation. In this repo: an agent, a skill, a hook
script, or a utility. Scale-agnostic — applies equally to a single function, a whole agent,
or a pipeline stage.
_Avoid_: unit, component, service.

**Interface**
Everything a caller must know to use the module correctly. For agents: the fields they accept
and the structured report they return. For hooks: the exit-code contract and stdin/stdout
format. For skills: the arguments and the output format.
_Avoid_: API, signature (too narrow — omits invariants and error modes).

**Depth**
Leverage at the interface — how much behaviour a caller exercises per unit of interface they
must learn. **Deep** = large behaviour behind a small interface. **Shallow** = interface
nearly as complex as the implementation.

**Seam** _(from Feathers)_
Where an interface lives; a place behaviour can be altered without editing in place.
_Avoid_: boundary (overloaded; say seam or interface).

**Adapter**
A concrete thing satisfying an interface at a seam.

**Leverage**
What callers get from depth: more capability per unit of interface learned.

**Locality**
What maintainers get from depth: change, bugs, and knowledge concentrated in one place
rather than spreading across callers.

## Principles

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a
  pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. If you want
  to test *past* the interface, the module is probably the wrong shape.
- **One adapter = hypothetical seam. Two adapters = real seam.** Don't introduce a port
  unless at least two adapters are justified (typically production + test).
- **Depth is a property of the interface, not the implementation.** A deep module can be
  internally composed of small parts — they just aren't exposed through the interface.

## Relationships

- A **Module** has exactly one **Interface** (the surface it presents to callers and tests).
- **Depth** is a property of a **Module**, measured against its **Interface**.
- A **Seam** is where a **Module**'s **Interface** lives.
- An **Adapter** sits at a **Seam** and satisfies the **Interface**.
- **Depth** produces **Leverage** for callers and **Locality** for maintainers.

## Rejected framings

- "Service" for agent or skill
- "Boundary" for seam
- "API" for interface (omits invariants and error modes)
- Depth measured as a ratio of line counts (rewards padding the implementation)
