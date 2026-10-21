# M3 controller identity and status research protocol

- Status: Draft; not approved for execution
- Date: 2026-10-21
- Target: Makerspace Næstved JPT 100 W E2/M7 MOPA fiber laser
- Controller: JCZ/EZCAD2-compatible, observed USB `9588:9899`
- Scope: identity and read-only status only
- Hardware access authorized by this document: **no**

## Purpose

This protocol is the review gate between the completed no-device work and any
future controller access. It is deliberately narrower than a controller test:
it defines how a proposed session must be specified, reviewed, stopped and
recorded before an endpoint may be opened.

The public template is
`tests/fixtures/m3-hardware-protocol-template.json`. It contains no allowed USB
operation because the repository does not yet have sufficient evidence to name
exact request bytes, response constraints and safety behavior. That absence is
a blocker, not a field to fill by inference.

The validator can only report `incomplete`, `invalid`, or `ready_for_review`.
It always reports `hardware_access_authorized: false`. A later, session-specific
human approval must reference the immutable plan hash; neither this document
nor a successful validator run grants permission to touch hardware.

## Known facts and unresolved assumptions

Observed facts:

- Windows passively enumerated `USBLMCV4`, VID/PID `9588:9899`, device
  revision descriptor `0005`, with no compatible function driver installed.
- The LightBurn export identifies a `JCZFiber`/`LibUSB` JPT profile and a
  110 × 110 mm work area.
- BalorMK independently targets the same USB identity and provides a mock
  transport, but its live commands include motion- and emission-capable paths.

Not established:

- that descriptor `0005` is a board or firmware revision;
- that any apparently read-only controller request cannot reset state, move a
  galvo, arm the source or change an output;
- the currently mounted lens and correction profile by physical verification;
- a reviewed, reversible Windows driver strategy for this computer;
- the exact request/response bytes safe to use for identity or status.

## Non-negotiable scope

M3 may eventually cover controller enumeration, identity, firmware/capability
discovery and status. The following remain prohibited throughout this protocol:

- persistent writes or configuration changes;
- job or list upload and execution;
- galvo motion and physical framing;
- source arming or laser emission;
- replay of an unknown request or response;
- automatic retry after an abort or unexpected response.

M4 requires a new protocol. An M3 result cannot be stretched to authorize
motion, framing, marking, parameter sweeps or output-off assumptions.

## Gates before a session can be reviewed

### 1. Evidence gate

Every proposed operation must be listed individually with:

- a unique operation identifier and single purpose;
- public evidence provenance using an artifact ID;
- evidence level (`observed` or `independently-implemented`);
- exact request bytes—never wildcards, inferred fields or exploratory ranges;
- a bounded expected-response contract;
- one timeout and exactly one attempt;
- explicit `read-only-no-motion-no-emission` classification;
- `state_change_expected: false`.

An empty allowlist keeps the plan incomplete. A malformed or state-changing
operation makes it invalid.

### 2. Physical gate

Before connecting the research computer, the session plan must record:

- the reviewed physical method that prevents emission independently of
  software, and confirmation that it was verified;
- a cleared work area that assumes unexpected galvo motion is still possible;
- an accessible and tested emergency stop;
- a named safety observer present for the whole live portion;
- physical confirmation of the machine/profile identity and mounted optics.

“Laser power set to zero” or a UI toggle is not an independent emission
inhibition method.

### 3. Software and driver gate

- The production controller backend remains absent from The Pirate Ray.
- A narrow experiment harness must enforce the reviewed operation allowlist.
- Unknown responses are captured and stop the session; they are never replayed.
- No operation is retried automatically.
- The current Windows driver state is recorded privately before change.
- Driver installation, replacement and rollback require their own reviewed,
  reversible plan. This repository does not install or switch drivers.
- The normal LightBurn control computer is not modified for convenience.

### 4. People and review gate

The plan names an operator, safety observer and protocol reviewer. One person
may not silently fill all roles during execution. The reviewer checks the
machine identity, evidence for every allowlisted operation, physical isolation,
driver rollback, capture destination and stop/recovery procedures.

After `validate_m3_hardware_protocol.py` reports `ready_for_review`, freeze the
plan bytes and SHA-256. A separate approval record must identify that hash,
reviewer, approval time with timezone, location and exact session window. Any
plan edit invalidates that approval.

Create the frozen, non-authorizing review packet with:

```powershell
python scripts/prepare_m3_review_packet.py path/to/session-plan.json
```

The generator refuses an incomplete or invalid plan, refuses to overwrite a
non-empty output directory, copies the exact plan bytes and hashes both the
plan and untouched `approval-record-template.json`. A reviewer must create a
separate approval record rather than edit the packet template. The generated
output still states `hardware_access_authorized: false`; generating a packet is
not approval.

After an independent reviewer copies and completes the approval template,
validate the separate record against the unchanged packet:

```powershell
python scripts/validate_m3_approval.py `
  .build/m3-review-packet `
  path/to/approval-record.json
```

The validator checks both packet file hashes and sizes, the frozen plan, Git
commit, reviewer identity, exact session window, approval time and every safety
statement. A successful result is `approval_record_valid`, not automatic
permission to access hardware: the result continues to state
`hardware_access_authorized: false` and `live_preflight_required: true`.

## Session sequence

The eventual reviewed session follows this order and stops at the first failed
gate:

1. Brief operator and observer; verify emergency-stop access.
2. Confirm machine, source, lens and controller identity without opening an
   endpoint.
3. Apply and verify the independent emission inhibition.
4. Clear the work area and assume motion remains possible.
5. Record the original Windows driver state and rollback evidence privately.
6. Verify hashes for the plan, harness and dependencies.
7. Start capture into the prepared private destination.
8. Connect only the allowlisted controller identity.
9. Execute one allowlisted operation once.
10. Compare the response only with its predeclared constraints.
11. Stop; do not improvise a follow-up request.
12. Disconnect, restore the reviewed driver state, and verify normal shutdown.
13. Hash raw evidence privately and create only sanitized derived public notes.

No batch of “harmless queries” is permitted. Additional operations require a
new reviewed plan or a new version of the allowlist.

## Immediate abort conditions

Any of these ends the session without automatic retry:

- unexpected galvo motion;
- any emission or source-arm indication;
- interlock state change;
- unexpected controller reset or disconnect;
- attempted transfer not present in the immutable allowlist;
- response outside the predeclared contract;
- stop request from either operator or observer.

On abort: stop the harness, disconnect USB if safe, use the reviewed physical
power-down procedure, preserve logs, record an incident, and do not send a
speculative reset/stop command. A controller stop command is itself prohibited
until separately evidenced and allowlisted.

## Evidence and publication

Raw captures, serials, instance identifiers, driver exports, photos and local
paths go to `ThePirateRay-PrivateStash` with byte count, SHA-256, acquisition
time, origin and classification. The public repository receives sanitized
derived notes and synthetic regression fixtures only. Vendor binaries are not
executed or committed publicly.

The session report must distinguish:

- **observed** bytes or state;
- **inferred** interpretation;
- **unknown** behavior requiring more evidence.

## Validate the draft plan

```powershell
python scripts/validate_m3_hardware_protocol.py `
  tests/fixtures/m3-hardware-protocol-template.json
```

The committed template is expected to return `incomplete`: roles, physical
controls, recovery, driver plan, session metadata and exact evidence-backed
operations are intentionally absent. Do not change those fields merely to make
the validator green.

## Current conclusion

The written-protocol roadmap requirement is now represented and testable, but
the protocol is not executable. The next evidence needed for M3 is a reviewed
driver/rollback strategy and a justified exact read-only operation contract.
Until those exist and a specific plan receives separate human approval, no USB
endpoint may be opened and no controller bytes may be sent.
