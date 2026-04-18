# Native Language Matrix

Use this playbook when the main risk is in binaries, parsers, protocol handlers, or crypto-heavy code. If the target is mainly an HTTP service, prefer the web playbook even if it is written in Go or Rust.

| Target Type | Signals | Priority Surfaces | Preferred Building Blocks |
| --- | --- | --- | --- |
| C / C++ libraries and daemons | `CMakeLists.txt`, `meson.build`, `.c`, `.cc`, `.cpp` | parsers, codecs, IPC, file formats, unsafe copies, allocator boundaries | `fuzzer`, `dwarf-expert`, `variant-analysis`, `supply-chain-risk-auditor` |
| Rust crates and services | `Cargo.toml`, `unsafe`, FFI, custom parsers | parser logic, unsafe blocks, FFI boundaries, state invariants, crypto code | `fuzzer`, `kani-proof`, `constant-time-analysis`, `dimensional-analysis` |
| Go binaries and protocol handlers | `go.mod`, parser packages, custom wire formats | length mismatches, path handling, archive parsing, SSRF-ish internal fetches | `fuzzer`, `variant-analysis`, `supply-chain-risk-auditor` |
| Crypto and auth code | custom MAC/signature code, secret-dependent branches | timing side channels, nonce misuse, length confusion, downgrade logic | `constant-time-analysis`, `sharp-edges`, `dimensional-analysis` |
| Reverse-engineering targets | stripped ELF/Mach-O/PE, DWARF info, crash artifacts | parser state, privilege boundaries, binary-only attack surface | `dwarf-expert`, `fuzzer`, `variant-analysis` |

## Common Bug Classes

- Memory corruption and unsafe parsing
- Integer, size, and unit mismatches
- Unsafe FFI or ABI assumptions
- Timing side channels
- Temporary file, path, or environment trust issues
- Privilege boundary mistakes in helper binaries or CLI tooling
