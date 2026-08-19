# Franklin build and serve

Run from the **repo root**, where `Project.toml` lives:

```bash
julia --project=. -e 'using Franklin; serve()'
```

Serves at http://localhost:8000 and rebuilds on every save to `*.md`, `_layout/`, `_css/`,
`_data/` and `utils.jl`.

## First time on a machine

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

Once per machine. Installs Franklin, NodeJS and TOML into the project manifest.

## Flags

```julia
serve(port=8123)      # a different port
serve(single=true)    # build once, do not watch
serve(clear=true)     # delete __site/ first
serve(launch=false)   # do not open a browser
```

**Use `clear=true` after editing `utils.jl` or a `_data/` file.** The data files are cached in a
module-level `Dict` for the whole build, so a long-running `serve()` session can hold a stale copy.
When in doubt, stop the process and start it again.

## Not applicable here

- **No `-J<sysimage>`.** This project has no GLMakie dependency. Do not use the Makie sysimage.
- **Plain `julia` from system juliaup**, not a JuliaHub channel binary.

## Never commit

`__site/`, `_tmp/`, `node_modules/`, `Manifest.toml`. All are in `.gitignore`.
