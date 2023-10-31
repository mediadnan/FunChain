# <img id="logo" src="_static/logo/banner.png" alt="FunChain Logo" />
<div style="text-align: center; font-weight: bold;">Chain functions easily and safely</div>

## Overview 📜

**FunChain** is an open-source python package that implements tools for function composition,
and reduces the code needed to create a pipeline to process data sequentially
or through multiple branches in isolation, and capture errors from being propagated,
then reports them at the end of each execution.

The idea behind this package is to help make and maintain reusable components 🧩 that could be combined,
to make data processing easier and more scalable.

- Its declarative syntax is intentionally easy and intuitive, this makes it easy to learn and to get started with;

- The performance is a priority, and the package will always evolve towards being
more optimized and to reduce its impact as much as it's possible.

- It is flexible enough to be integrated in bigger projects, or to be extended with 
more functionality.

- It supports `async` 🎉 out of the box to make it the best choice for IO bound operation,
 like network fetching.

## Dependencies 📦
**FunChain** uses <a href="https://failures.readthedocs.io" target="_blank"><b>Failures</b> [⮩]</a>
under the hood to gather and report errors

## Versioning 🏷️
This python package follows the <a href="https://semver.org" target="_blank"><b>semantic versioning</b></a> specification, so breaking changes
will only be introduced in MAJOR version bumps _(i.e. from ``1.x.x`` to ``2.x.x``)_.
As long as your app relies on a specific version (i.e. ``1.x.x``), the next MINOR releases will always be
backward compatible.

However, it's worth mentioning that `funchain` is still in its experimental phase,
but it's being tested and actively maintained.

Future changes will be documented in the `CHANGELOG.md` file.

(installation)=
## Installation 📥
To integrate `funchain` in your environment, run the command

```bash
pip install funchain
```

## Content 📂
```{toctree}
:caption: User Guide 📖
:maxdepth: 2

user_guide/getting_started.md
user_guide/chains.md
user_guide/models.md
user_guide/optional.md
user_guide/required.md
user_guide/async_support.md
user_guide/static.md
```

```{toctree}
:caption: Reference 🔎
:maxdepth: 2

reference.md
```