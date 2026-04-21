# Web3 Bug Bounty Skills Upgrade Brainstorm

## Problem Statement

Repo hien tai da co nhieu security primitive manh, nhung chua co lop dieu phoi bug bounty Web3/Exchange du chat.

Nhung gi dang co:
- primitive tot cho smart contract, graph analysis, spec compliance, target bootstrap, report submission
- lane bug bounty tong quat cho web, mobile, smart contract, native
- mot so ky thuat rat manh cho Solana

Nhung gi dang thieu:
- lane rieng cho EVM/DeFi/Exchange/Wallet/Web3 app
- orchestration theo multi-surface: onchain + offchain + wallet + browser extension + docs/spec
- sub-agent architecture chuyen cho security, khong phai generic software delivery
- asset inventory / tried-ruled-out / finding pipeline theo dung bug bounty workflow
- false-positive gates va exploit packaging cho Web3

Muc tieu dung:
- xay bo skills/plugins phuc vu bug bounty program
- trong tam: Smart Contract, Blockchain, Exchange, Web3
- uu tien kha nang route dung lane, map dung trust boundary, va goi dung primitive hien co

## What Is Valuable In `codexkit-distill`

Nhung thu dang hoc:

1. Role separation ro rang
- `.codex/agents/*.toml` tach vai tro planner, researcher, debugger, code reviewer, docs manager.
- Gia tri that su: khong phai "nhieu agent", ma la task ownership ro rang.

2. Parallelization co ky luat
- `prompts/plan-parallel.md` ep phase ownership, dependency matrix, conflict prevention.
- Bai hoc dung: neu co sub-agent thi phai chia artifact va file ownership ro rang.

3. Edge-case-first review
- `prompts/review-codebase-parallel.md` bat main agent liet ke edge case truoc khi giao review.
- Bai hoc dung: bug bounty Web3 nen liet ke invariant va edge-case truoc scanner.

4. Logic toolkit co the tai su dung
- `sequential-thinking` co revision, branch, hypothesis, verification.
- `Problem-Solving Techniques` co inversion, simplification cascades, scale game.
- `planner.toml` co decomposition, second-order thinking, root cause, 80/20, systems thinking.

5. Context hygiene
- report ngan
- absolute path handoff
- validation truoc implementation
- khong de agent nao om context vo han

## What Should NOT Be Ported Blindly

Port nguyen bo `codexkit-distill` vao repo nay la sai huong.

Ly do:
- no nghieng ve generic product engineering, khong nghieng ve security research
- nhieu prompt phu thuoc `.claude`, slash commands, tool contracts khong trung voi Codex hien tai
- co nhieu "prompt theater": rat dai, rat nhieu role, nhung neu khong gan domain model thi chi tang nhieu
- cac role `fullstack_developer`, `ui_ux_designer`, `docs_manager` khong phai trong tam cho bug bounty Web3

Ket luan:
- lay pattern dieu phoi
- bo generic delivery boilerplate
- thay bang security-specific orchestration

## Current Repo Assessment

### Strong Assets To Reuse

- `bounty-hunting-programs`: da co lifecycle tong quat va lane routing
- `bounty-target-bootstrap`: intake tu program page, giu metadata wallet/blockchain/exchange
- `bug-bounty-report-submitter`: report packaging rat hop bug bounty
- `building-secure-contracts`: bo scanner/checklist da nen cho nhieu chain
- `solana-audit`: skill sau, co taxonomies, confidence, sub-workflow ro
- `trailmark`: dung de graph, blast radius, taint, attack surface
- `spec-to-code-compliance`: rat hop cho whitepaper/protocol docs
- `entry-point-analyzer`: mapping privileged/state-changing entry point
- `dimensional-analysis`, `property-based-testing`, `mutation-testing`: rat hop cho DeFi math/invariants

### Current Structural Weaknesses

1. `bounty-program-smart-contracts` van qua rong
- no route theo chain, nhung chua route theo protocol class.
- thieu lane rieng cho lending, AMM, vault, bridge, oracle, staking, governance, perp, orderbook.

2. Khong co EVM audit skill sau ngang Solana
- EVM hien dang dua nhieu vao checklist/building blocks.
- Chua co mot "orchestrated auditor" cho Solidity/Vyper/DeFi.

3. Triage van co xu huong single-lane
- target Web3 that su thuong la hybrid:
  - web frontend
  - API/backend
  - smart contracts
  - wallet signing flow
  - browser extension
  - RPC/WebSocket/indexer

4. Chua co workflow rieng cho exchange/backend crypto systems
- CEX, broker, custody, internal ledger, withdrawal engine, signer service, hot wallet, websocket auth.

5. Chua co wallet/browser-extension lane
- trong repo co `browser-extension-mcp-main`, nhung chua duoc bien thanh plugin skill hoan chinh.

6. Chua co bug bounty state system
- asset inventory
- tried / ruled-out
- finding candidates
- validated findings
- PoC registry

7. Hai plugin rat nen co cho bug bounty nhung dang blocked
- `static-analysis`
- `fp-check`

## Evaluated Approaches

### Approach A: Chi them them skills vao plugin hien co

Pros:
- nhanh
- it doi metadata

Cons:
- se tiep tuc roi rac
- khong giai quyet van de orchestration
- lane smart contract tiep tuc bi qua rong

Verdict:
- khong nen chon lam huong chinh

### Approach B: Port `codexkit-distill` gan nhu nguyen bo

Pros:
- co ve bai ban
- co nhieu sub-agent role ngay lap tuc

Cons:
- tool mismatch
- prompt bulk
- generic software bias
- khong giai quyet domain Web3

Verdict:
- khong nen

### Approach C: Giu primitive hien co, them security-centric orchestration + bo sung 3-5 plugin dung cho Web3

Pros:
- dung cai repo nay da manh
- it lang phi
- de bat dau
- hop YAGNI/KISS nhat

Cons:
- can thiet ke lai route layer
- can them vai plugin root-port moi

Verdict:
- khuyen nghi

## Recommended Architecture

### Layer 1: Keep Current Primitives

Giu nguyen va tan dung:
- `trailmark`
- `entry-point-analyzer`
- `building-secure-contracts`
- `solana-audit`
- `spec-to-code-compliance`
- `dimensional-analysis`
- `property-based-testing`
- `mutation-testing`
- `bounty-target-bootstrap`
- `bug-bounty-report-submitter`

### Layer 2: Add Security-Centric Orchestration Plugin

Tao plugin moi: `web3-bounty-programs`

Skill de xay:
- `web3-bounty-triage`
- `web3-surface-mapper`
- `web3-finding-pipeline`
- `web3-poc-packager`
- `web3-engagement-state`

Muc dich:
- cho phep multi-lane thay vi single-lane
- sinh asset inventory
- quan ly tried/ruled-out
- giu evidence va finding lifecycle

### Layer 3: Add Domain Plugins That Are Actually Missing

#### 1. `evm-protocol-audit`

Ly do:
- khoang trong lon nhat hien tai
- can mot skill sau ngang `solana-audit`

Nen gom:
- protocol classification: AMM, lending, vault, staking, governance, bridge, oracle, perp, orderbook
- entry-point map
- privilege graph
- upgrade/proxy review
- accounting and invariant review
- weird token and integration review
- PoC path for found issue

Nen tai su dung:
- `entry-point-analyzer`
- `trailmark`
- `building-secure-contracts`
- `token-integration-analyzer`
- `dimensional-analysis`
- `property-based-testing`
- `mutation-testing`
- `spec-to-code-compliance`

#### 2. `exchange-audit`

Ly do:
- Exchange khong chi la smart contract
- bug bounty thuc te thuong nam o offchain/backend/trading workflow

Skill nen co:
- `exchange-surface-mapper`
- `cex-backend-audit`
- `trading-auth-and-session-audit`
- `withdrawal-and-ledger-audit`
- `websocket-orderflow-audit`

Bug classes uu tien:
- internal ledger mismatch
- authz tren admin/trader/support tools
- withdraw approval bypass
- websocket privilege/state desync
- market/order manipulation via backend trust gap
- signer service exposure
- KYC/region gating bypass co security impact

#### 3. `wallet-extension-audit`

Ly do:
- Web3 flow thuong rot o signing/origin/provider/extension bridge
- repo da co `browser-extension-mcp-main`, day la co hoi that

Skill nen co:
- `browser-wallet-audit`
- `extension-provider-bridge-audit`
- `typed-data-and-signing-flow-audit`
- `wallet-session-and-origin-trust-audit`

Can tich hop:
- `browser-extension-mcp-main`
- `chrome-devtools`
- `agent-browser`
- neu co: `jshook`

#### 4. `bridge-and-oracle-audit`

Ly do:
- bridge/oracle la nhom bounty gia tri cao va khac biet ro

Skill nen co:
- `cross-chain-bridge-audit`
- `oracle-consumer-audit`
- `message-proof-and-replay-audit`

#### 5. Optional: `web3-offchain-infra-audit`

Chi them neu can:
- RPC gateways
- indexers
- keepers
- relayers
- liquidation bots
- signer daemons

## Sub-Agent Strategy To Borrow From Distill

Khong dung generic agents. Dung security agents co ownership hep:

- `surface-mapper`
- `state-transition-auditor`
- `economic-invariant-checker`
- `authz-path-reviewer`
- `poc-verifier`
- `false-positive-checker`
- `report-assembler`

Rule:
- moi sub-agent chi so huu mot artifact class
- khong cho 2 agent sua cung file output
- phai co handoff format ngan
- chi spawn song song khi lanes doc lap

Parallel lanes hop le cho Web3:
- onchain contracts
- offchain web/api/backend
- wallet/extension/browser
- docs/spec/whitepaper
- finding verification

## Logic Model To Codify Into New Skills

Day la phan "xay dung tu duy logic" nen dua thang vao references cua plugin moi:

1. Developer-perspective-first
- sensitive data nam o dau
- client co the thay gi
- trust boundary nao co that
- layer nao kien truc se khong bao gio chua du lieu can tim

2. Invariant-first review
- ai duoc doi state
- state nao phai bao toan
- tai san nao phai duoc backing
- math nao phai monotonic / bounded / conserved

3. Multi-surface decomposition
- frontend
- backend
- signer
- RPC
- onchain
- wallet
- indexer

4. Hypothesis -> verify -> revise
- khong lao vao variant hunting qua som
- phai prove mot path ngan tu input -> state change -> impact

5. Tried / ruled-out discipline
- sau 2-3 huong test co y nghia ma khong ra, pivot
- ghi ly do ruled-out de tranh loop

6. False-positive gate
- path co reachable khong
- attacker co control du input khong
- exploit cost co thuc te khong
- co offchain guard chan lai khong

## Concrete Upgrade Backlog

### Phase 1: High ROI, Low Risk

1. Tang cap `bounty-program-triage`
- cho phep multi-lane ket qua
- output them:
  - onchain lane
  - offchain lane
  - wallet lane
  - extension lane
  - exchange lane

2. Tang cap `bounty-target-bootstrap`
- them schema cho:
  - contract clusters
  - rpc/ws endpoints
  - wallet/extension targets
  - signer/relayer/indexer endpoints
  - exchange/trading surfaces

3. Unblock hoac root-port:
- `static-analysis`
- `fp-check`

4. Them bug bounty state bundle chuan
- `audit-targets/<slug>/inventory/asset-inventory.md`
- `audit-targets/<slug>/inventory/tried-ruled-out.md`
- `audit-targets/<slug>/inventory/finding-pipeline.md`

### Phase 2: Deepen Existing Lanes

- tang chat `bounty-program-smart-contracts` bang protocol archetype triage
- tang chat `bounty-target-bootstrap` bang handoff state bundle
- tang chat `bug-bounty-report-submitter` bang Web3 / exchange evidence structure

## Success Metrics

- triage khong con ep target Web3 hybrid vao mot lane duy nhat
- co asset inventory va tried/ruled-out cho moi target
- EVM audit co do sau tuong duong `solana-audit`
- exchange/offchain flow duoc cover bang skill rieng
- wallet/extension flow duoc cover bang skill rieng
- false positive giam ro rang nho `fp-check`
- static analysis khong con bi blocked trong nhung engagement can scan nhanh

## Recommendation

Theo user constraint hien tai:

- khong them plugin moi
- khong them skill moi
- chi cai tien in-place bo hien co

Tom lai:
- khong port nguyen bo `codexkit-distill`
- chi lay orchestration patterns, logic patterns, context hygiene
- cai tien truc tiep `bounty-program-triage`, `bounty-program-smart-contracts`, `bounty-target-bootstrap`, va `bug-bounty-report-submitter`
- uu tien multi-surface routing, protocol-archetype thinking, bug bounty state tracking, va Web3 evidence packaging

## Next Steps

Neu di tiep theo huong implementation, thu tu nen la:

1. rewrite triage + bootstrap schemas
2. root-port/unblock `static-analysis`
3. root-port/unblock `fp-check`
4. deepen current smart-contract lane
5. deepen current report-submission lane

## Open Questions

- Anh muon toi uu cho bug bounty public platform, hay audit/private engagement?
- Uu tien EVM truoc, hay exchange/backend truoc?
- Muon giu plugin nho nhieu cai, hay gom thanh 1 mega-plugin Web3?
